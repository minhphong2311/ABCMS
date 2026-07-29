import asyncio

async def deploy_folders(page, site_url, site_id, unique_folders_list, progress_cb, total_items, current_item):
    if not unique_folders_list:
        return current_item
        
    def report(msg):
        nonlocal current_item
        current_item += 1
        if progress_cb:
            progress_cb(min(100, int((current_item / max(1, total_items)) * 100)), msg)

    print(f"Creating folders in Page Manager: {unique_folders_list}")
    target_url_page = f'{site_url}/index.do?siteId={site_id}#!/page'
    await page.goto(target_url_page, wait_until="domcontentloaded")
    await asyncio.sleep(6)
    
    folders_created = False
    for folder in unique_folders_list:
        report(f"Creating folder: {folder}")
        folder_anchor_id = f'/{site_id}/{folder}_anchor'
        try:
            await page.wait_for_selector(f'[id="{folder_anchor_id}"]', timeout=3000)
            folder_el = True
        except Exception:
            folder_el = False
        
        if not folder_el:
            print(f"Folder '{folder}' not found. Creating...")
            await page.evaluate(f'''async () => {{
                try {{ 
                    if (typeof window.angular === 'undefined') return;
                    let injector = window.angular.element(document.body).injector();
                    if (injector) await injector.get("pageService").addFolder("{site_id}", "/{site_id}", "{folder}"); 
                }} catch(e) {{}}
            }}''')
            await asyncio.sleep(1.5)
            folders_created = True
            
            # Verification Step
            # CMS tree needs a refresh to show new nodes created via API
            await page.reload(wait_until="domcontentloaded")
            await asyncio.sleep(4)
            try:
                await page.wait_for_selector(f'[id="{folder_anchor_id}"]', timeout=5000)
                print(f"Xác minh thành công: Thư mục '{folder}' đã tồn tại.")
            except Exception:
                raise Exception(f"Kiểm tra lại thất bại: Thư mục '{folder}' chưa được tạo thành công trên CMS.")
    
    if folders_created:
        print("Folders created successfully.")
        
    return current_item
