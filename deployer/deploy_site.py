import asyncio

async def check_and_deploy_site(page, site_url, site_id, username, password, progress_cb=None):
    print(f"Kiểm tra sự tồn tại của Site ID: {site_id}")
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
            print(f"Site ID '{site_id}' không tồn tại. Đang tiến hành tạo mới tại trang Quản lý Site...")
            if progress_cb:
                progress_cb(10, f"Creating new Site ID: {site_id}...")
            
            # Truy cập trang quản lý site theo yêu cầu
            site_creation_url = f'{site_url}/index.do#!/site'
            
            if 'login.do' in page.url:
                print("Bị đẩy ra trang login, tiến hành login lại (webadmin) để tạo site...")
                await page.goto(f'{site_url}/index.do')
                await page.wait_for_selector('input[name="userId"]', timeout=15000)
                await page.fill('input[name="userId"]', 'webadmin')
                await page.fill('input[name="userPassword"]', '12andvina#$')
                await page.click('button[type="submit"]')
                await asyncio.sleep(4)
            
            print(f"Điều hướng đến: {site_creation_url}")
            await page.goto(site_creation_url, wait_until="domcontentloaded")
            await asyncio.sleep(5)

            print("Đang gọi API tạo Site trên hệ thống CMS...")
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
            print(f"Kết quả tạo Site: {res}")
            await asyncio.sleep(2)
            
            # Tải lại trang menu manager ban đầu
            target_url = f'{site_url}/index.do?siteId={site_id}#!/menu'
            print(f"Quay lại trang Menu Manager: {target_url}")
            # Phải login lại bằng user gốc vì hiện tại đang là webadmin
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
            
            # Xác minh lại xem site đã tạo thành công chưa
            if 'login.do' in page.url:
                raise Exception("Đăng nhập hoặc tự động tạo Site thất bại. URL vẫn bị đẩy về trang Login. Hãy kiểm tra lại tài khoản hệ thống hoặc tạo Site bằng tay.")
                
        else:
            print(f"Site ID '{site_id}' đã tồn tại, tiếp tục deploy.")
    except Exception as e:
        raise Exception(f"Lỗi trong quá trình kiểm tra/tạo Site: {e}")
