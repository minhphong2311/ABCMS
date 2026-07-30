import asyncio

async def check_and_deploy_site(page, site_url, site_id, username, password, progress_cb=None):
    print("\n" + "="*50)
    print("1. KIỂM TRA SITE")
    print("="*50)
    print(f"  1.1 Tìm Site ID: {site_id}")
    try:
        site_check = await page.evaluate(f'''async () => {{
            try {{
                if (typeof window.angular === 'undefined') return false;
                let body = window.angular.element(document.body);
                if (!body) return false;
                let injector = body.injector();
                if (!injector || !injector.has('menuService')) return false;
                let menuMap = injector.get('menuService').getMenuMap('{site_id}');
                return menuMap !== null && menuMap !== undefined;
            }} catch(e) {{
                return false;
            }}
        }}''')
        
        if not site_check:
            print(f"  1.3 Site chưa tồn tại → Đang tiến hành tạo Site ID '{site_id}'...")
            if progress_cb:
                progress_cb(10, f"Creating new Site ID: {site_id}...")
            
            site_creation_url = f'{site_url}/index.do#!/site'
            
            if 'login.do' in page.url:
                print("  [Auto-Login] Tiến hành đăng nhập tài khoản admin...")
                await page.goto(f'{site_url}/index.do')
                await page.wait_for_selector('input[name="userId"]', timeout=15000)
                await page.fill('input[name="userId"]', 'webadmin')
                await page.fill('input[name="userPassword"]', '12andvina#$')
                await page.click('button[type="submit"]')
                await asyncio.sleep(4)
            
            print(f"  Điều hướng đến: {site_creation_url}")
            await page.goto(site_creation_url, wait_until="domcontentloaded")
            await asyncio.sleep(5)

            print("  Đang gửi API tạo Site trên hệ thống CMS...")
            res = await page.evaluate(f'''async () => {{
                try {{
                    if (typeof window.angular === 'undefined') return "Angular undefined";
                    let injector = window.angular.element(document.body).injector();
                    if (!injector || !injector.has('siteService')) return "No siteService";
                    
                    let res = await injector.get('siteService').insert({{ siteId: '{site_id}', siteNm: '{site_id}' }});
                    return res;
                }} catch (e) {{
                    return "Error: " + e.message;
                }}
            }}''')
            print(f"  Kết quả tạo Site: {res}")
            await asyncio.sleep(2)
            
            target_url = f'{site_url}/index.do?siteId={site_id}#!/menu'
            print(f"  Quay lại trang Menu Manager: {target_url}")
            await page.goto(f'{site_url}/logOut.do')
            await asyncio.sleep(2)
            await page.goto(f'{site_url}/index.do')
            await page.wait_for_selector('input[name="userId"]', timeout=15000)
            await page.fill('input[name="userId"]', username)
            await page.fill('input[name="userPassword"]', password)
            await page.click('button[type="submit"]')
            await asyncio.sleep(4)
            
            await page.goto(target_url, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            print(f"  1.4 Kiểm tra lại Site ID...")
            if not isinstance(res, dict) or not res.get('success'):
                raise Exception(f"Kiểm tra lại thất bại: Site ID '{site_id}' chưa được tạo thành công trên hệ thống CMS. Lỗi: {res}")
            print(f"  ✓ 1.4 Kiểm tra lại Site ID THÀNH CÔNG: Site '{site_id}' đã sẵn sàng.")
                
        else:
            print(f"  1.2 Site đã tồn tại ({site_id}) → Chuyển sang bước 2.")
    except Exception as e:
        raise Exception(f"Lỗi trong quá trình kiểm tra/tạo Site: {e}")

