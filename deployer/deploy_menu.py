import asyncio

async def get_cms_menus(page, site_id):
    res = await page.evaluate(f'''() => {{
        try {{
            if (typeof window.angular === 'undefined') return [];
            let body = window.angular.element(document.body);
            if (!body) return [];
            let injector = body.injector();
            if (!injector || !injector.has('menuService')) return [];
            let menuMap = injector.get('menuService').getMenuMap('{site_id}');
            return menuMap;
        }} catch(e) {{
            return null;
        }}
    }}''')
    return list(res.values()) if res and isinstance(res, dict) else []

async def get_menu_info(page, menu_cd):
    res = await page.evaluate(f'''(cd) => {{
        try {{
            if (typeof window.angular === 'undefined') return null;
            let body = window.angular.element(document.body);
            if (!body) return null;
            let injector = body.injector();
            if (!injector || !injector.has('menuService')) return null;
            return injector.get('menuService').getMenuInfo(cd);
        }} catch(e) {{ return null; }}
    }}''', menu_cd)
    return res
    
async def update_menu(page, data):
    await page.evaluate(f'''async (d) => {{
        try {{
            if (typeof window.angular === 'undefined') return false;
            let body = window.angular.element(document.body);
            if (!body) return false;
            let injector = body.injector();
            if (!injector || !injector.has('menuService')) return false;
            const s = injector.get('menuService');
            await s.update(d);
        }} catch(e) {{}}
        return true;
    }}''', data)

async def deploy_menu_items(page, site_id, menus, progress_cb, total_items, current_item):
    created_menu_cds = {}
    
    def report(msg):
        nonlocal current_item
        current_item += 1
        if progress_cb:
            progress_cb(min(100, int((current_item / max(1, total_items)) * 100)), msg)

    for m in menus:
        report(f"Deploying menu: {m['name']}")
        cms_menus = await get_cms_menus(page, site_id)
        
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
            async def add_menu(m, pid=None):
                if pid is None:
                    return await page.evaluate(f'''async () => {{
                        try {{
                            if (typeof window.angular === 'undefined') return null;
                            let injector = window.angular.element(document.body).injector();
                            if (!injector || !injector.has('menuService')) return null;
                            return await injector.get('menuService').addMenu('{site_id}', '{m['name']}');
                        }} catch (e) {{ return null; }}
                    }}''')
                else:
                    return await page.evaluate(f'''async (pid) => {{
                        try {{
                            if (typeof window.angular === 'undefined') return null;
                            let injector = window.angular.element(document.body).injector();
                            if (!injector || !injector.has('menuService')) return null;
                            return await injector.get('menuService').addChildMenu('{site_id}', pid, '{m['name']}');
                        }} catch (e) {{ return null; }}
                    }}''', pid)
            
            add_res = await add_menu(m, parent_menu_cd)
            await asyncio.sleep(1)
            
            if not add_res or not add_res.get('item'):
                print(f"Failed to get newly created menu '{m['name']}' from API response: {add_res}")
                continue
            menu_cd = add_res['item']['menuCd']
            
        created_menu_cds[m['id']] = menu_cd
        
        # Update URL (slug)
        folder = m.get('folder') or m.get('slug')
        slug = m.get('slug')
        url = f"/{folder}/{slug}.do" if folder else f"/{slug}.do" if slug else None
        
        existing_url = existing.get('page') if existing else None
        if url and existing_url != url:
            print(f"Updating URL for '{m['name']}' to '{url}'...")
            info_res = await get_menu_info(page, menu_cd)
            if info_res and 'item' in info_res:
                data = info_res['item']
                data['page'] = url
                data['url'] = url
                await update_menu(page, data)
                await asyncio.sleep(1)

    print("Finished deploying menus!")
    return created_menu_cds, current_item
