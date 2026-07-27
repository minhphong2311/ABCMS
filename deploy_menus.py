import asyncio
from playwright.async_api import async_playwright

async def deploy_menus_task_async(site_url, site_id, username, password, menus):
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
        browser = await p.chromium.launch(headless=True, slow_mo=200)
        context = await browser.new_context(ignore_https_errors=True)
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

            for m in menus:
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
            unique_folders = set()
            for m in menus:
                if m.get('folder'):
                    unique_folders.add(m.get('folder'))
                elif not m.get('parent_id') and m.get('slug'):
                    unique_folders.add(m.get('slug'))
            
            unique_folders = sorted(list(unique_folders))
            
            if unique_folders:
                print(f"Creating folders in Page Manager: {unique_folders}")
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
                for folder in unique_folders:
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
            
            return {'success': True, 'message': 'Menus and folders deployed successfully!'}
        except Exception as e:
            print(f'Menu deploy ERROR: {e}')
            return {'success': False, 'message': f'Menu deploy error: {str(e)}'}
        finally:
            await browser.close()

def run_deploy_menus(site_url, site_id, username, password, menus):
    return asyncio.run(deploy_menus_task_async(site_url, site_id, username, password, menus))
