import asyncio
from playwright.async_api import async_playwright
import os
import sys

async def main():
    print("=== TEST CMS UPLOAD ===")
    site_url = 'https://demo.jiniworks.com/_fox'
    site_id = 'test-phong'
    
    username = input("Nhập username CMS (mặc định kookmin): ").strip() or "kookmin"
    password = input("Nhập password CMS (mặc định kookmin_user): ").strip() or "kookmin_user"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        print("Mở trang đăng nhập...")
        await page.goto(site_url)
        await asyncio.sleep(2)
        await page.fill('input[name="userId"]', username)
        await page.fill('input[name="userPassword"]', password)
        await page.click('button[type="submit"]')
        
        print("Đang đăng nhập...")
        await asyncio.sleep(5)
        
        # Navigate using hash explicitly
        print("Chuyển hướng đến res-img...")
        target_url = f'{site_url}/index.do?siteId={site_id}#!/res-img'
        await page.goto(target_url)
        await page.reload()
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)
        
        root_folder_id = f'/_res/{username}/{site_id}/img/_anchor'
        content_folder_id = f'/_res/{username}/{site_id}/img/content_anchor'
        
        print(f"Kiểm tra root folder: {root_folder_id}")
        try:
            await page.click(f'[id="{root_folder_id}"]', timeout=5000)
            print("Đã click root folder.")
        except Exception as e:
            print("Không tìm thấy root folder:", e)
            
        await asyncio.sleep(2)
        
        # Try to find create folder button
        print("Thử tạo thư mục content (nếu chưa có)...")
        await page.evaluate(f'''async () => {{
            try {{
                const injector = window.angular.element(document.body).injector();
                const svc = injector.has('resImgService') ? injector.get('resImgService') : 
                           (injector.has('fileService') ? injector.get('fileService') : null);
                if (svc && svc.addFolder) {{
                    await svc.addFolder("{site_id}", "/_res/{username}/{site_id}/img/", "content");
                }}
            }} catch(e) {{ console.error(e); }}
        }}''')
        await asyncio.sleep(3)
        
        try:
            await page.click(f'[id="{content_folder_id}"]', timeout=5000)
            print("Đã click thư mục content.")
        except:
            print("Không tìm thấy thư mục content, có thể chưa được tạo.")
            
        image_path = os.path.abspath(os.path.join('data', 'img', 'content', 'img-ready.png'))
        if os.path.exists(image_path):
            print(f"Bắt đầu upload ảnh: {image_path}")
            
            # Click upload button if exists
            await page.evaluate('''() => {
                const btn = document.querySelector('[data-cmd="uploadFile"]') || document.querySelector('[ng-click*="upload"]');
                if (btn) btn.click();
            }''')
            await asyncio.sleep(2)
            
            # Find file input
            file_inputs = await page.locator('input[type="file"]').element_handles()
            if file_inputs:
                print("Đã tìm thấy file input, đang truyền file...")
                for fi in file_inputs:
                    try:
                        await fi.set_input_files(image_path)
                        break
                    except Exception:
                        pass
                        
            await asyncio.sleep(2)
            # Click submit/upload
            await page.evaluate('''() => {
                const btn = document.querySelector('[data-cmd="startUpload"]') || 
                           Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Upload') || b.innerText.includes('업로드') || b.innerText.includes('Tải lên'));
                if (btn) btn.click();
            }''')
            print("Đã gửi lệnh upload.")
        else:
            print("KHÔNG TÌM THẤY ẢNH TẠI:", image_path)
            
        print("Giữ trình duyệt mở trong 30 giây để kiểm tra...")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
