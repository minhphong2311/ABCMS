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
            ui_creation_result = await page.evaluate(f'''async (folderName) => {{
                try {{
                    // 1. Right click root folder
                    const anchor = document.querySelector('.jstree-anchor');
                    if (!anchor) return "Error: No .jstree-anchor found";
                    
                    // Dispatch contextmenu event
                    const ev = new MouseEvent('contextmenu', {{ bubbles: true, cancelable: false, view: window, button: 2, buttons: 2, clientX: anchor.getBoundingClientRect().left, clientY: anchor.getBoundingClientRect().top }});
                    anchor.dispatchEvent(ev);
                    
                    // Wait for context menu
                    await new Promise(r => setTimeout(r, 1000));
                    
                    // 2. Click Add Folder
                    const menuItems = Array.from(document.querySelectorAll('.vakata-context a'));
                    const addBtn = menuItems.find(a => (a.innerText||'').includes('Thêm') || (a.innerText||'').includes('추가') || (a.innerText||'').includes('Add') || a.getAttribute('rel') === 'createFolder');
                    if (!addBtn) return "Error: Context menu 'Add Folder' not found. Menu HTML: " + (document.querySelector('.vakata-context') ? document.querySelector('.vakata-context').innerHTML : 'none');
                    addBtn.click();
                    
                    // Wait for modal
                    await new Promise(r => setTimeout(r, 1000));
                    
                    // 3. Fill form
                    const modal = document.querySelector('.modal-content');
                    if (!modal) return "Error: Modal not found";
                    
                    const inputs = Array.from(modal.querySelectorAll('input[type="text"]'));
                    if (inputs.length < 2) return "Error: Form inputs not found in modal";
                    
                    inputs[0].value = folderName; inputs[0].dispatchEvent(new Event('input', {{bubbles: true}}));
                    inputs[1].value = folderName; inputs[1].dispatchEvent(new Event('input', {{bubbles: true}}));
                    
                    // 4. Save
                    const saveBtn = Array.from(modal.querySelectorAll('button')).find(b => (b.innerText||'').includes('Lưu') || (b.innerText||'').includes('저장') || (b.innerText||'').includes('Save') || b.className.includes('btn-primary'));
                    if (!saveBtn) return "Error: Save button not found";
                    saveBtn.click();
                    
                    return "Success";
                }} catch (e) {{
                    return "Exception: " + e.toString();
                }}
            }}''', folder)
            
            if ui_creation_result != "Success":
                print(f"  [Lỗi] Không thể tạo thư mục qua UI: {ui_creation_result}")
                raise Exception(f"Không thể tạo thư mục '{folder}' qua UI: {ui_creation_result}")
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

