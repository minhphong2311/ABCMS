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
        
    def report(msg, fraction=0.0):
        if progress_cb:
            progress_cb(min(100, int(((current_item + fraction) / max(1, total_items)) * 100)), msg)

    target_url_page = f'{site_url}/index.do?siteId={site_id}#!/page'
    await page.goto(target_url_page, wait_until="domcontentloaded")
    await asyncio.sleep(3.6)
    
    folders_created = False
    for folder in unique_folders_list:
        if is_cancelled and is_cancelled():
            raise Exception("Deploy cancelled by user")
            
        report(f"Folder: checking {folder}", 0.1)
        print(f"\n  3.2 Kiểm tra Folder '{folder}' theo thứ tự Menu...")
        
        # Ensure '폴더별' (Folder) tab is active in the sidebar
        await page.evaluate('''() => {
            const tabs = Array.from(document.querySelectorAll('.nav-tabs li a'));
            const folderTab = tabs.find(t => (t.innerText || '').includes('폴더별'));
            if (folderTab) folderTab.click();
        }''')
        await asyncio.sleep(0.5)
        
        # Expand root folder if it's closed
        await page.evaluate(f'''() => {{
            const rootNode = document.getElementById('/{site_id}');
            if (rootNode && rootNode.classList.contains('jstree-closed')) {{
                const icon = rootNode.querySelector('.jstree-icon.jstree-ocl');
                if (icon) icon.click();
            }}
        }}''')
        await asyncio.sleep(1)

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
            report(f"Folder: creating {folder}", 0.5)
            print(f"  3.4 Folder '{folder}' chưa tồn tại → Tiến hành tạo Folder '{folder}' qua UI...")
            try:
                # 1. Right click the site root folder
                await page.locator(f'[id="/{site_id}_anchor"]').first.click(button="right", force=True)
                await asyncio.sleep(1)
                
                # 2. Click Add Folder (support Korean, Vietnamese, English)
                import re
                await page.locator('.vakata-context a', has_text=re.compile(r'Thêm|추가|Add|createFolder', re.IGNORECASE)).first.click()
                await asyncio.sleep(1)
                
                # 3. Fill form - check for inline input first
                input_loc = page.locator('.jstree-rename-input')
                if await input_loc.count() > 0:
                    await input_loc.first.fill(folder)
                    await input_loc.first.press("Enter")
                    await asyncio.sleep(2)
                else:
                    # Fallback to modal
                    inputs = page.locator('.modal-content input[type="text"]')
                    await inputs.nth(0).fill(folder)
                    if await inputs.count() > 1:
                        await inputs.nth(1).fill(folder)
                    await page.locator('.modal-content button', has_text=re.compile(r'Lưu|저장|Save|primary', re.IGNORECASE)).first.click()
                    await asyncio.sleep(2)
            except Exception as ex:
                print(f"  [Lỗi] Không thể tạo thư mục qua UI: {ex}")
                raise Exception(f"Không thể tạo thư mục '{folder}' qua UI: {ex}")
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            folders_created = True
            
            # Verification Step
            await page.reload(wait_until="domcontentloaded")
            await asyncio.sleep(2.4)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            report(f"Folder: verifying {folder}", 0.9)
            print(f"  3.5 Kiểm tra lại Folder '{folder}' trong danh sách...")
            try:
                await page.wait_for_selector(f'[id="{folder_anchor_id}"]', timeout=5000)
                print(f"  ✓ 3.5 Kiểm tra lại THÀNH CÔNG: Thư mục '{folder}' đã tồn tại.")
            except Exception as e:
                if str(e) == 'Deploy cancelled by user': raise
                raise Exception(f"Kiểm tra lại thất bại: Thư mục '{folder}' chưa được tạo thành công trên CMS.")
        
        current_item += 1
    
    print("  ✓ 3.5 Hoàn thành kiểm tra và xác nhận lại toàn bộ Folder theo đúng thứ tự.")
    return current_item

