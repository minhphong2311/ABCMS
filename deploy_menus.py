import asyncio
import os
from playwright.async_api import async_playwright

async def deploy_menus_task_async(site_url, site_id, username, password, menus, progress_cb=None):
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
    menus = sorted(menus, key=lambda x: (get_depth(x), x.get('order', 999)))
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            target_url = f'{site_url}/index.do?siteId={site_id}#!/menu'
            print(f'Navigating to Menu Manager: {target_url}')
            await page.goto(target_url)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(4)
            
            async def get_cms_menus():
                res = await page.evaluate(f'''() => {{
                    return window.angular.element(document.body).injector().get('menuService').getMenuMap('{site_id}');
                }}''')
                return list(res.values()) if res and isinstance(res, dict) else []

            async def get_menu_info(menu_cd):
                res = await page.evaluate(f'''(cd) => {{
                    return window.angular.element(document.body).injector().get('menuService').getMenuInfo(cd);
                }}''', menu_cd)
                return res
                
            async def update_menu(data):
                await page.evaluate(f'''async (d) => {{
                    const s = window.angular.element(document.body).injector().get('menuService');
                    try {{ await s.update(d); }} catch(e) {{}}
                    return true;
                }}''', data)

            created_menu_cds = {}

            unique_folders = set()
            for m in menus:
                if m.get('folder'):
                    unique_folders.add(m.get('folder'))
                elif not m.get('parent_id') and m.get('slug'):
                    unique_folders.add(m.get('slug'))
            unique_folders_list = sorted(list(unique_folders))
            
            total_items = len(menus) + len(unique_folders_list) + 1
            current_item = 0
            
            def report(msg):
                nonlocal current_item
                current_item += 1
                if progress_cb:
                    progress_cb(min(100, int((current_item / max(1, total_items)) * 100)), msg)

            for m in menus:
                report(f"Deploying menu: {m['name']}")
                cms_menus = await get_cms_menus()
                
                # Determine expected parent menu CD
                parent_menu_cd = None
                if m.get('parent_id'):
                    parent_menu_cd = created_menu_cds.get(m['parent_id'])
                    if not parent_menu_cd:
                        print(f"Parent for '{m['name']}' not found locally or in CMS. Skipping.")
                        continue
                
                # Helper to normalize menu codes for safe comparison
                def normalize_cd(cd):
                    if cd is None or cd == 0 or cd == '0' or cd == '':
                        return None
                    return str(cd)

                # Find existing menu that matches BOTH name and parent
                existing = None
                for cm in cms_menus:
                    if cm.get('menuNm') == m['name']:
                        cm_parent_cd = cm.get('parentMenuCd')
                        if normalize_cd(cm_parent_cd) == normalize_cd(parent_menu_cd):
                            existing = cm
                            break
                
                if existing:
                    print(f"Menu '{m['name']}' already exists in this group (menuCd: {existing['menuCd']})")
                    menu_cd = existing['menuCd']
                else:
                    print(f"Creating menu '{m['name']}'...")
                    add_res = None
                    if not parent_menu_cd:
                        add_res = await page.evaluate(f'''async () => {{
                            return await window.angular.element(document.body).injector().get('menuService').addMenu('{site_id}', '{m['name']}');
                        }}''')
                    else:
                        add_res = await page.evaluate(f'''async (pid) => {{
                            return await window.angular.element(document.body).injector().get('menuService').addChildMenu('{site_id}', pid, '{m['name']}');
                        }}''', parent_menu_cd)
                        
                    await asyncio.sleep(1)
                    
                    if not add_res or not add_res.get('item'):
                        print(f"Failed to get newly created menu '{m['name']}' from API response: {add_res}")
                        continue
                    menu_cd = add_res['item']['menuCd']
                    
                created_menu_cds[m['id']] = menu_cd
                
                # Update URL (slug)
                folder = m.get('folder')
                slug = m.get('slug')
                url = f"/{folder}/{slug}.do" if folder else f"/{slug}.do" if slug else None
                
                existing_url = existing.get('page') if existing else None
                if url and existing_url != url:
                    print(f"Updating URL for '{m['name']}' to '{url}'...")
                    info_res = await get_menu_info(menu_cd)
                    if info_res and 'item' in info_res:
                        data = info_res['item']
                        data['page'] = url
                        data['url'] = url
                        await update_menu(data)
                        await asyncio.sleep(1)

            print("Finished deploying menus!")
            
            # --- CREATE FOLDERS IN PAGE MANAGER ---
            if unique_folders_list:
                print(f"Creating folders in Page Manager: {unique_folders_list}")
                target_url_page = f'{site_url}/index.do?siteId={site_id}#!/page'
                await page.goto(target_url_page)
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(4)
                
                await page.evaluate('''() => {
                    const tabs = Array.from(document.querySelectorAll('.nav-tabs li a, uib-tab-heading, a'));
                    const pageTab = tabs.find(x => (x.innerText || x.textContent || '').trim().includes('페이지'));
                    if (pageTab) pageTab.click();
                }''')
                await asyncio.sleep(2)
                
                folders_created = False
                for folder in unique_folders_list:
                    report(f"Creating folder: {folder}")
                    folder_anchor_id = f'/{site_id}/{folder}_anchor'
                    try:
                        await page.wait_for_selector(f'[id="{folder_anchor_id}"]', timeout=3000)
                        folder_el = True
                    except Exception:
                        folder_el = False
                    
                    if not folder_el:
                        print(f"Folder '{folder}' not found. Creating...")
                        await page.evaluate(f'''async () => {{
                            try {{ await window.angular.element(document.body).injector().get("pageService").addFolder("{site_id}", "/{site_id}", "{folder}"); }} catch(e) {{}}
                        }}''')
                        await asyncio.sleep(1.5)
                        folders_created = True
                
                if folders_created:
                    print("Folders created successfully.")
            
            # --- UPLOAD IMAGE TO RES-IMG ---
            try:
                if progress_cb:
                    progress_cb(90, "Uploading img-ready.png to CMS...")
                
                print("Navigating to res-img...")
                target_url_res = f'{site_url}/index.do?siteId={site_id}#!/res-img'
                
                # Navigate robustly (page was already logged in)
                await page.goto(target_url_res)
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(5)

                # The img folder path uses 'kookmin' (org), not the login username
                res_org = 'kookmin'
                root_folder_id = f'/_res/{res_org}/{site_id}/img/_anchor'
                content_folder_id = f'/_res/{res_org}/{site_id}/img/content_anchor'
                
                print(f"Waiting for root folder: {root_folder_id}")
                await page.wait_for_selector(f'[id="{root_folder_id}"]', timeout=10000)
                
                # Check if content folder exists
                content_exists = await page.locator(f'[id="{content_folder_id}"]').count() > 0
                
                if not content_exists:
                    print("Folder 'content' not found. Creating via right-click context menu...")
                    # Right-click root folder to open context menu
                    await page.click(f'[id="{root_folder_id}"]', button='right')
                    await asyncio.sleep(1)
                    
                    # Context menu shows "추가" (Add) - click it to create a subfolder
                    # The context menu item has class with fa-plus icon
                    await page.locator('.vakata-context li a:has(.fa-plus), .jstree-contextmenu li a:has(.fa-plus)').first.click()
                    await asyncio.sleep(1)
                    
                    # JSTree inline rename input appears - type 'content' and confirm
                    await page.locator('.jstree-rename-input').fill('content')
                    await asyncio.sleep(0.3)
                    await page.keyboard.press('Enter')
                    await asyncio.sleep(2)
                    print("Folder 'content' created.")
                
                # Click content folder to select it (try ID first, fallback to text)
                print("Selecting 'content' folder...")
                try:
                    await page.wait_for_selector(f'[id="{content_folder_id}"]', timeout=5000)
                    await page.click(f'[id="{content_folder_id}"]')
                except Exception:
                    print("ID-based selector failed, trying text-based selector...")
                    await page.locator('.jstree-anchor').filter(has_text='content').last.click()
                await asyncio.sleep(2)
                
                # Build image path relative to deploy_menus.py location
                base_dir = os.path.dirname(os.path.abspath(__file__))
                image_path = os.path.join(base_dir, 'data', 'img', 'content', 'img-ready.png')
                if os.path.exists(image_path):
                    print(f"Uploading {image_path}...")
                    
                    # Click the upload button (ng-click="img.upload()") to open modal
                    await page.click('button[ng-click="img.upload()"]')
                    await asyncio.sleep(2)
                    
                    # In the modal: set file directly to the flow-btn file input
                    file_input = page.locator('input[type="file"][flow-btn]').first
                    await file_input.set_input_files(image_path)
                    await asyncio.sleep(2)
                    
                    # Click the "업로드" button in the modal footer to confirm upload
                    upload_confirm = page.locator('button:has(.fa-cloud-upload), button:text("업로드")').first
                    await upload_confirm.click()
                    await asyncio.sleep(4)
                    print("img-ready.png uploaded successfully!")
                else:
                    print(f"Image file not found at: {image_path}")

            except Exception as e:
                print(f"Error during res-img upload: {e}")



            if progress_cb:
                progress_cb(100, "Completed!")
            return {'success': True, 'message': 'Menus and folders deployed successfully!'}

        except Exception as e:
            print(f'Menu deploy ERROR: {e}')
            return {'success': False, 'message': f'Menu deploy error: {str(e)}'}
        finally:
            await browser.close()

def run_deploy_menus(site_url, site_id, username, password, menus, progress_cb=None):
    return asyncio.run(deploy_menus_task_async(site_url, site_id, username, password, menus, progress_cb))
