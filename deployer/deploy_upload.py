# Author: sawyer88
# Email: phongnguyen@andvina.com

import asyncio
import os

async def deploy_upload_image(page, site_url, site_id, progress_cb=None, is_cancelled=None):
    try:
        print("\n" + "="*50)
        print("4. KIỂM TRA UPLOAD")
        print("="*50)
        print("  4.1 Mở Upload (Giao diện Quản lý hình ảnh res-img).")
        if progress_cb:
            progress_cb(50, "Uploading img-ready.png to CMS...")
        
        target_url_res = f'{site_url}/index.do?siteId={site_id}#!/res-img'
        
        await page.goto(target_url_res, wait_until="domcontentloaded")
        await asyncio.sleep(3.6)
        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')

        res_org = 'kookmin'
        root_folder_id = f'/_res/{res_org}/{site_id}/img/_anchor'
        content_folder_id = f'/_res/{res_org}/{site_id}/img/content_anchor'
        
        await page.wait_for_selector(f'[id="{root_folder_id}"]', timeout=10000)
        
        print("  4.2 Kiểm tra đã có Folder 'content' hay chưa...")
        content_exists = await page.locator(f'[id="{content_folder_id}"]').count() > 0
        
        if not content_exists:
            print("  4.3 Chưa có Folder 'content' → Tiến hành Tạo Folder 'content'...")
            await page.click(f'[id="{root_folder_id}"]', button='right')
            await asyncio.sleep(0.6)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            
            await page.locator('.vakata-context li a:has(.fa-plus), .jstree-contextmenu li a:has(.fa-plus)').first.click()
            await asyncio.sleep(0.6)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            
            await page.locator('.jstree-rename-input').fill('content')
            await asyncio.sleep(0.5)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            await page.keyboard.press('Enter')
            await asyncio.sleep(1.2)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            print("  ✓ Đã tạo Folder 'content'.")
        else:
            print("  ✓ Folder 'content' đã tồn tại.")
        
        print("  4.4 Mở Folder 'content'.")
        try:
            await page.wait_for_selector(f'[id="{content_folder_id}"]', timeout=5000)
            await page.click(f'[id="{content_folder_id}"]')
        except Exception as e:
            if str(e) == 'Deploy cancelled by user': raise
            await page.locator('.jstree-anchor').filter(has_text='content').last.click()
        await asyncio.sleep(1.2)
        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_name = 'img-ready.png'
        image_path = os.path.join(base_dir, 'assets', 'img', 'content', image_name)

        print(f"  4.5 Kiểm tra hình ảnh '{image_name}' trong Folder 'content'...")
        img_exists = await page.evaluate(f'''() => {{
            return document.body.innerText.includes('{image_name}');
        }}''')

        if img_exists:
            print(f"  4.6 Hình ảnh '{image_name}' đã tồn tại → Kiểm tra hình ảnh tiếp theo.")
        else:
            print(f"  4.7 Hình ảnh '{image_name}' chưa tồn tại → Upload hình ảnh...")
            if os.path.exists(image_path):
                await page.click('button[ng-click="img.upload()"]')
                await asyncio.sleep(1.2)
                if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                
                file_input = page.locator('input[type="file"][flow-btn]').first
                await file_input.set_input_files(image_path)
                await asyncio.sleep(1.2)
                if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                
                upload_confirm = page.locator('button:has(.fa-cloud-upload), button:has-text("업로드")').first
                await upload_confirm.click()
                await asyncio.sleep(2.4)
                if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            else:
                print(f"  [Lỗi] File hình ảnh không tồn tại tại: {image_path}")

        print("  4.8 Sau khi hoàn thành, kiểm tra lại toàn bộ hình ảnh trong Folder 'content'...")
        try:
            await page.wait_for_function(f'''() => {{
                return document.body.innerText.includes('{image_name}');
            }}''', timeout=10000)
            print(f"  ✓ 4.8 Kiểm tra lại THÀNH CÔNG: Hình ảnh '{image_name}' đã có mặt đầy đủ trong Folder 'content'!")
        except Exception as e:
            if str(e) == 'Deploy cancelled by user': raise
            raise Exception(f"Kiểm tra lại thất bại: Hình ảnh '{image_name}' chưa xuất hiện trong Folder 'content'.")

    except Exception as e:
        if str(e) == 'Deploy cancelled by user': raise
        print(f"Lỗi trong quá trình kiểm tra Upload: {e}")
        raise

