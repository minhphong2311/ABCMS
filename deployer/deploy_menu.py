# Author: sawyer88
# Email: phongnguyen@andvina.com

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
            
            // Clean up problematic fields before sending to Spring MVC
            if (d.children) delete d.children;
            if (d.nodes) delete d.nodes;
            
            await s.update(d);
        }} catch(e) {{}}
        return true;
    }}''', data)

async def deploy_menu_items(page, site_id, menus, progress_cb, total_items, current_item, is_cancelled=None):
    print("\n" + "="*50)
    print("2. KIỂM TRA MENU")
    print("="*50)
    print("  2.1 Mở danh sách Menu.")
    created_menu_cds = {}
    
    def report(msg, fraction=0.0):
        if progress_cb:
            progress_cb(min(100, int(((current_item + fraction) / max(1, total_items)) * 100)), msg)

    for m in menus:
        if is_cancelled and is_cancelled():
            raise Exception("Deploy cancelled by user")
        
        report(f"Menu: checking {m['name']}", 0.1)
        print(f"\n  2.2 Kiểm tra Menu '{m['name']}' trong danh sách Menu...")
        cms_menus = await get_cms_menus(page, site_id)
        
        # Determine expected parent menu CD
        parent_menu_cd = None
        if m.get('parent_id'):
            parent_menu_cd = created_menu_cds.get(m['parent_id'])
            if not parent_menu_cd:
                print(f"  [Cảnh báo] Parent for '{m['name']}' not found locally or in CMS. Skipping.")
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
            print(f"  2.3 Menu '{m['name']}' đã tồn tại (menuCd: {existing['menuCd']}) → Chuyển sang bước 3 (kiểm tra menu tiếp theo).")
            menu_cd = existing['menuCd']
        else:
            report(f"Menu: creating {m['name']}", 0.4)
            print(f"  2.4 Menu '{m['name']}' chưa tồn tại → Tiến hành Tạo Menu '{m['name']}'...")
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
            await asyncio.sleep(0.6)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            
            if not add_res or not add_res.get('item'):
                print(f"  Lỗi khi tạo menu '{m['name']}': {add_res}")
                continue
            menu_cd = add_res['item']['menuCd']
            
        created_menu_cds[m['id']] = menu_cd
        
        # Update URL (slug)
        folder = m.get('folder') or m.get('slug')
        slug = m.get('slug')
        url = f"/{folder}/{slug}.do" if folder else f"/{slug}.do" if slug else None
        
        existing_url = existing.get('page') if existing else None
        if url and existing_url != url:
            report(f"Menu: updating URL for {m['name']}", 0.7)
            print(f"  Cập nhật URL cho '{m['name']}' -> '{url}'...")
            info_res = await get_menu_info(page, menu_cd)
            if info_res and 'item' in info_res:
                data = info_res['item']
                data['page'] = url
                data['url'] = url
                
                # Delete children on python side as well to be safe
                if 'children' in data: del data['children']
                if 'nodes' in data: del data['nodes']
                
                await update_menu(page, data)
                await asyncio.sleep(0.6)
                if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                
                # Close any SweetAlert that might have popped up from Spring 500 error or success
                try:
                    await page.evaluate('''() => {
                        const confirmBtn = document.querySelector('.sweet-alert button.confirm, .sweet-alert .confirm, button.confirm');
                        if (confirmBtn) confirmBtn.click();
                    }''')
                except: pass
                
        # Verification Step
        report(f"Menu: verifying {m['name']}", 0.9)
        print(f"  2.5 Kiểm tra lại toàn bộ danh sách Menu để xác nhận...")
        verify_menus = await get_cms_menus(page, site_id)
        is_verified = any(str(cm.get('menuCd')) == str(menu_cd) for cm in verify_menus)
        if not is_verified:
            raise Exception(f"Kiểm tra lại thất bại: Menu '{m['name']}' chưa được tạo thành công trên hệ thống CMS.")
        print(f"  ✓ 2.5 Xác nhận thành công: Menu '{m['name']}' đã tồn tại (menuCd: {menu_cd}).")
        
        current_item += 1

    print("  ✓ Hoàn tất kiểm tra và tạo Menu.")
    return created_menu_cds, current_item

