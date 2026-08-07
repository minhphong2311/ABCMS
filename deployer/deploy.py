# Author: sawyer88
# Email: phongnguyen@andvina.com

import asyncio
import os
import sys
from playwright.async_api import async_playwright
from deployer.deploy_site import check_and_deploy_site
from deployer.deploy_menu import deploy_menu_items
from deployer.deploy_folder import deploy_folders
from deployer.deploy_upload import deploy_upload_image
from deployer.deploy_page import deploy_pages

async def full_deploy_task_async(site_url, site_id, site_name, username, password, menus, progress_cb=None, is_cancelled=None):
    # Safe print to avoid cp949 encode errors on Windows
    def safe_print(*args, **kwargs):
        msg = " ".join(str(a) for a in args)
        sys.stdout.buffer.write((msg + "\n").encode('utf-8', errors='replace'))
        sys.stdout.buffer.flush()
    
    # Store original print and override
    import builtins
    orig_print = builtins.print
    builtins.print = safe_print

    # Calculate depth to ensure parents are always created before children
    menu_map = {m['id']: m for m in menus}
    def get_depth(m):
        depth = 0
        curr = m
        while curr and curr.get('parent_id'):
            depth += 1
            curr = menu_map.get(curr['parent_id'])
        return depth
        
    # Sort menus by depth first, then by order
    print("Sorting menus...")
    menus = sorted(menus, key=lambda x: (get_depth(x), x.get('order', 999)))
    print("Sorted menus.")
    
    from routes.helpers import get_config
    config = get_config()
    show_ui = bool(config.get('show_ui', True))
    headless_mode = not show_ui

    async with async_playwright() as p:
        print("Playwright started...")
        try:
            browser = await p.chromium.launch(
                headless=headless_mode,
                channel="chrome",
                slow_mo=500,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--start-maximized']
            )
            print(f'Google Chrome launched (headless={headless_mode}).')
        except Exception:
            browser = await p.chromium.launch(
                headless=headless_mode,
                slow_mo=500,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--start-maximized']
            )
            print(f'Chromium launched (headless={headless_mode}).')
            
        context = await browser.new_context(
            no_viewport=True, 
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        try:
            await page.bring_to_front()
        except Exception:
            pass
        
        # Auto-accept any dialogs (alerts, confirms) to prevent them from blocking the deployment
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
        
        # --- Helper cho progress ---
        def get_scaled_cb(base_cb, start_pct, end_pct):
            if not base_cb:
                return None
            def scaled_cb(local_pct, msg):
                actual_pct = start_pct + (local_pct / 100.0) * (end_pct - start_pct)
                base_cb(int(actual_pct), msg)
            return scaled_cb

        try:
            if progress_cb:
                progress_cb(0, "Site: logging in to CMS...")
            print(f'Logging in to CMS for menu deploy: {site_url}')
            await page.goto(site_url)
            await page.wait_for_selector('input[name="userId"]', timeout=15000)
            await page.fill('input[name="userId"]', username)
            await page.fill('input[name="userPassword"]', password)
            await page.click('button[type="submit"]')
            await asyncio.sleep(4)
            
            if progress_cb:
                progress_cb(1, "Site: navigating to dashboard...")
            target_url = f'{site_url}/index.do?siteId={site_id}#!/menu'
            print(f'Navigating to Menu Manager: {target_url}')
            await page.goto(target_url, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            # --- KIỂM TRA VÀ TẠO SITE NẾU CHƯA CÓ ---
            await check_and_deploy_site(page, site_url, site_id, site_name, username, password, get_scaled_cb(progress_cb, 0, 5), is_cancelled)
            
            if is_cancelled and is_cancelled(): raise Exception("Deploy cancelled by user")
            
            # --- TẠO LAYOUT TEMPLATE TRƯỚC MENU ---
            from deployer.deploy_layout import deploy_layouts
            await deploy_layouts(page, site_url, site_id, get_scaled_cb(progress_cb, 5, 15), is_cancelled)
            
            if is_cancelled and is_cancelled(): raise Exception("Deploy cancelled by user")
            
            # Tính toán các thư mục cần tạo
            unique_folders = set()
            for m in menus:
                folder = m.get('folder', '').strip() or m.get('slug', '').strip()
                if folder:
                    unique_folders.add(folder)
            unique_folders_list = sorted(list(unique_folders))
            
            total_items = len(menus) + len(unique_folders_list) + 1
            current_item = 0
            
            menu_folder_cb = get_scaled_cb(progress_cb, 15, 80)
            
            # --- 1. TẠO MENU VÀ CHỈ ĐỊNH URL ---
            created_menu_cds, current_item = await deploy_menu_items(page, site_id, menus, menu_folder_cb, total_items, current_item, is_cancelled)
            
            if is_cancelled and is_cancelled(): raise Exception("Deploy cancelled by user")
            
            # --- 2. TẠO CÁC FOLDER ---
            current_item = await deploy_folders(page, site_url, site_id, unique_folders_list, menu_folder_cb, total_items, current_item, is_cancelled)
            
            if is_cancelled and is_cancelled(): raise Exception("Deploy cancelled by user")
            
            # --- 3. UPLOAD HÌNH ẢNH DÙNG CHUNG ---
            res_org = await deploy_upload_image(page, site_url, site_id, get_scaled_cb(progress_cb, 80, 85), is_cancelled)
            if not res_org:
                res_org = 'kookmin' # fallback in case it fails to return
            
            if is_cancelled and is_cancelled(): raise Exception("Deploy cancelled by user")
            
            # --- 4. TẠO PAGE VÀ INJECT HTML ---
            await deploy_pages(page, site_url, site_id, menus, get_scaled_cb(progress_cb, 85, 100), total_items, current_item, is_cancelled, res_org)

            if progress_cb:
                progress_cb(100, "Page: completed")
            return {'success': True, 'message': 'Site, Layouts, Menus, Folders, Images and Pages deployed successfully!'}

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f'Deploy ERROR: {e}')
            return {'success': False, 'message': f'Deploy error: {str(e)}'}
        finally:
            await browser.close()
            # Restore original print
            try:
                import builtins
                builtins.print = orig_print
            except:
                pass

def run_full_deploy(site_url, site_id, site_name, username, password, menus, progress_cb=None, is_cancelled=None):
    return asyncio.run(full_deploy_task_async(site_url, site_id, site_name, username, password, menus, progress_cb, is_cancelled))
