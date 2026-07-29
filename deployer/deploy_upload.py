import asyncio
import os

async def deploy_upload_image(page, site_url, site_id, progress_cb=None):
    try:
        if progress_cb:
            progress_cb(90, "Uploading img-ready.png to CMS...")
        
        print("Navigating to res-img...")
        target_url_res = f'{site_url}/index.do?siteId={site_id}#!/res-img'
        
        # Navigate robustly (page was already logged in)
        await page.goto(target_url_res, wait_until="domcontentloaded")
        await asyncio.sleep(6)

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
        
        # Build image path relative to root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_path = os.path.join(base_dir, 'assets', 'img', 'content', 'img-ready.png')
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
            upload_confirm = page.locator('button:has(.fa-cloud-upload), button:has-text("업로드")').first
            await upload_confirm.click()
            await asyncio.sleep(4)
            
            # Verification Step
            try:
                await page.wait_for_function('''() => {
                    return document.body.innerText.includes('img-ready.png');
                }''', timeout=10000)
                print("Xác minh thành công: img-ready.png đã tồn tại trong CMS!")
            except Exception:
                raise Exception("Kiểm tra lại thất bại: Hình ảnh 'img-ready.png' chưa được upload thành công sau 10 giây.")
        else:
            print(f"Image file not found at: {image_path}")

    except Exception as e:
        print(f"Error during res-img upload: {e}")
        raise
