import asyncio
import os
import sys
from playwright.async_api import async_playwright
from deployer.deploy_site import check_and_deploy_site
from deployer.deploy_menu import deploy_menu_items
from deployer.deploy_folder import deploy_folders
from deployer.deploy_upload import deploy_upload_image
from deployer.deploy_page import deploy_pages

async def deploy_menus_task_async(site_url, site_id, username, password, menus, progress_cb=None):
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
    
    async with async_playwright() as p:
        print("Playwright started...")
        browser = await p.chromium.launch(headless=True)
        print("Browser launched.")
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}, 
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            print(f'Logging in to CMS for menu deploy: {site_url}')
            await page.goto(site_url)
            await page.wait_for_selector('input[name="userId"]', timeout=15000)
            await page.fill('input[name="userId"]', username)
            await page.fill('input[name="userPassword"]', password)
            await page.click('button[type="submit"]')
            await asyncio.sleep(4)
            
            target_url = f'{site_url}/index.do?siteId={site_id}#!/menu'
            print(f'Navigating to Menu Manager: {target_url}')
            await page.goto(target_url, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            # --- KIỂM TRA VÀ TẠO SITE NẾU CHƯA CÓ ---
            await check_and_deploy_site(page, site_url, site_id, username, password, progress_cb)
            
            # Tính toán các thư mục cần tạo
            unique_folders = set()
            for m in menus:
                folder = m.get('folder', '').strip() or m.get('slug', '').strip()
                if folder:
                    unique_folders.add(folder)
            unique_folders_list = sorted(list(unique_folders))
            
            total_items = len(menus) + len(unique_folders_list) + 1
            current_item = 0
            
            # --- 1. TẠO MENU VÀ CHỈ ĐỊNH URL ---
            created_menu_cds, current_item = await deploy_menu_items(page, site_id, menus, progress_cb, total_items, current_item)
            
            # --- 2. TẠO CÁC FOLDER ---
            current_item = await deploy_folders(page, site_url, site_id, unique_folders_list, progress_cb, total_items, current_item)
            
            # --- 3. UPLOAD HÌNH ẢNH DÙNG CHUNG ---
            await deploy_upload_image(page, site_url, site_id, progress_cb)
            
            # --- 4. TẠO PAGE VÀ INJECT HTML ---
            await deploy_pages(page, site_url, site_id, menus, progress_cb, total_items, current_item)

            if progress_cb:
                progress_cb(100, "Completed!")
            return {'success': True, 'message': 'Menus, folders and ready pages deployed successfully!'}

        except Exception as e:
            print(f'Menu deploy ERROR: {e}')
            return {'success': False, 'message': f'Menu deploy error: {str(e)}'}
        finally:
            await browser.close()
            # Restore original print
            try:
                import builtins
                builtins.print = orig_print
            except:
                pass

def run_deploy_menus(site_url, site_id, username, password, menus, progress_cb=None):
    return asyncio.run(deploy_menus_task_async(site_url, site_id, username, password, menus, progress_cb))
