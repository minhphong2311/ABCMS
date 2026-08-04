# Author: sawyer88
# Email: phongnguyen@andvina.com

import asyncio

async def deploy_folders(page, site_url, site_id, unique_folders_list, progress_cb, total_items, current_item, is_cancelled=None):
    print("\n" + "="*50)
    print("3. KIỂM TRA FOLDER")
    print("="*50)
    print("  3.1 Mở danh sách Folder.")
    if not unique_folders_list:
        print("  Không có folder riêng biệt cần tạo.")
        return current_item
        
    def report(msg):
        nonlocal current_item
        current_item += 1
        if progress_cb:
            progress_cb(min(100, int((current_item / max(1, total_items)) * 100)), msg)

    target_url_page = f'{site_url}/index.do?siteId={site_id}#!/page'
    await page.goto(target_url_page, wait_until="domcontentloaded")
    await asyncio.sleep(3.6)
    
    folders_created = False
    for folder in unique_folders_list:
        if is_cancelled and is_cancelled():
            raise Exception("Deploy cancelled by user")
            
        report(f"Checking folder: {folder}")
        print(f"\n  3.2 Kiểm tra Folder '{folder}' theo thứ tự Menu...")
        folder_anchor_id = f'/{site_id}/{folder}_anchor'
        try:
            await page.wait_for_selector(f'[id="{folder_anchor_id}"]', timeout=3000)
            folder_el = True
        except Exception as e:
            if str(e) == 'Deploy cancelled by user': raise
            folder_el = False
        
        if folder_el:
            print(f"  3.3 Folder '{folder}' đã tồn tại → Kiểm tra Folder của Menu tiếp theo.")
        else:
            print(f"  3.4 Folder '{folder}' chưa tồn tại → Tiến hành tạo Folder '{folder}' qua UI...")
            try:
                # Right click the first anchor (Root folder)
                await page.locator('.jstree-anchor').first.click(button="right", force=True)
                await asyncio.sleep(1)
                # Click "Thêm thư mục"
                await page.click('.vakata-context a[rel="createFolder"], .vakata-context a:has-text("Thêm thư mục"), .vakata-context a:has-text("폴더 추가")')
                await asyncio.sleep(1)
                # Fill the form
                await page.fill('.modal-content input[name="folder"]', folder)
                await page.fill('.modal-content input[name="folderNm"]', folder)
                # Save
                await page.click('.modal-content button[ng-click*="save"], .modal-content button.btn-primary')
                await asyncio.sleep(2)
            except Exception as ex:
                print(f"  [Lỗi] Không thể tạo thư mục qua UI: {ex}")
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            folders_created = True
            
            # Verification Step
            await page.reload(wait_until="domcontentloaded")
            await asyncio.sleep(2.4)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            print(f"  3.5 Kiểm tra lại Folder '{folder}' trong danh sách...")
            try:
                await page.wait_for_selector(f'[id="{folder_anchor_id}"]', timeout=5000)
                print(f"  ✓ 3.5 Kiểm tra lại THÀNH CÔNG: Thư mục '{folder}' đã tồn tại.")
            except Exception as e:
                if str(e) == 'Deploy cancelled by user': raise
                raise Exception(f"Kiểm tra lại thất bại: Thư mục '{folder}' chưa được tạo thành công trên CMS.")
    
    print("  ✓ 3.5 Hoàn thành kiểm tra và xác nhận lại toàn bộ Folder theo đúng thứ tự.")
    return current_item

