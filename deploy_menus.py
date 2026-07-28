import asyncio
import os
from playwright.async_api import async_playwright

async def deploy_menus_task_async(site_url, site_id, username, password, menus, progress_cb=None):
    # Calculate depth to ensure parents are always created before children
    menu_map = {m['id']: m for m in menus}
    def get_depth(m):
        depth = 0
        curr = m
        while curr and curr.get('parent_id'):
            depth += 1
            curr = menu_map.get(curr['parent_id'])
        return depth
        
    # Sort menus by depth first, then by order
    print("Sorting menus...")
    menus = sorted(menus, key=lambda x: (get_depth(x), x.get('order', 999)))
    print("Sorted menus.")
    
    async with async_playwright() as p:
        print("Playwright started...")
        browser = await p.chromium.launch(headless=True)
        print("Browser launched.")
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}, 
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            print(f'Logging in to CMS for menu deploy: {site_url}')
            await page.goto(site_url)
            await page.wait_for_selector('input[name="userId"]', timeout=15000)
            await page.fill('input[name="userId"]', username)
            await page.fill('input[name="userPassword"]', password)
            await page.click('button[type="submit"]')
            await asyncio.sleep(4)
            
            target_url = f'{site_url}/index.do?siteId={site_id}#!/menu'
            print(f'Navigating to Menu Manager: {target_url}')
            await page.goto(target_url, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            async def get_cms_menus():
                res = await page.evaluate(f'''() => {{
                    return window.angular.element(document.body).injector().get('menuService').getMenuMap('{site_id}');
                }}''')
                return list(res.values()) if res and isinstance(res, dict) else []

            async def get_menu_info(menu_cd):
                res = await page.evaluate(f'''(cd) => {{
                    return window.angular.element(document.body).injector().get('menuService').getMenuInfo(cd);
                }}''', menu_cd)
                return res
                
            async def update_menu(data):
                await page.evaluate(f'''async (d) => {{
                    const s = window.angular.element(document.body).injector().get('menuService');
                    try {{ await s.update(d); }} catch(e) {{}}
                    return true;
                }}''', data)

            created_menu_cds = {}

            unique_folders = set()
            for m in menus:
                folder = m.get('folder', '').strip() or m.get('slug', '').strip()
                if folder:
                    unique_folders.add(folder)
            unique_folders_list = sorted(list(unique_folders))
            
            total_items = len(menus) + len(unique_folders_list) + 1
            current_item = 0
            
            def report(msg):
                nonlocal current_item
                current_item += 1
                if progress_cb:
                    progress_cb(min(100, int((current_item / max(1, total_items)) * 100)), msg)

            for m in menus:
                report(f"Deploying menu: {m['name']}")
                cms_menus = await get_cms_menus()
                
                # Determine expected parent menu CD
                parent_menu_cd = None
                if m.get('parent_id'):
                    parent_menu_cd = created_menu_cds.get(m['parent_id'])
                    if not parent_menu_cd:
                        print(f"Parent for '{m['name']}' not found locally or in CMS. Skipping.")
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
                    print(f"Menu '{m['name']}' already exists in this group (menuCd: {existing['menuCd']})")
                    menu_cd = existing['menuCd']
                else:
                    print(f"Creating menu '{m['name']}'...")
                    add_res = None
                    if not parent_menu_cd:
                        add_res = await page.evaluate(f'''async () => {{
                            return await window.angular.element(document.body).injector().get('menuService').addMenu('{site_id}', '{m['name']}');
                        }}''')
                    else:
                        add_res = await page.evaluate(f'''async (pid) => {{
                            return await window.angular.element(document.body).injector().get('menuService').addChildMenu('{site_id}', pid, '{m['name']}');
                        }}''', parent_menu_cd)
                        
                    await asyncio.sleep(1)
                    
                    if not add_res or not add_res.get('item'):
                        print(f"Failed to get newly created menu '{m['name']}' from API response: {add_res}")
                        continue
                    menu_cd = add_res['item']['menuCd']
                    
                created_menu_cds[m['id']] = menu_cd
                
                # Update URL (slug)
                folder = m.get('folder') or m.get('slug')
                slug = m.get('slug')
                url = f"/{folder}/{slug}.do" if folder else f"/{slug}.do" if slug else None
                
                existing_url = existing.get('page') if existing else None
                if url and existing_url != url:
                    print(f"Updating URL for '{m['name']}' to '{url}'...")
                    info_res = await get_menu_info(menu_cd)
                    if info_res and 'item' in info_res:
                        data = info_res['item']
                        data['page'] = url
                        data['url'] = url
                        await update_menu(data)
                        await asyncio.sleep(1)

            print("Finished deploying menus!")
            
            # --- CREATE FOLDERS IN PAGE MANAGER ---
            if unique_folders_list:
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
                            try {{ await window.angular.element(document.body).injector().get("pageService").addFolder("{site_id}", "/{site_id}", "{folder}"); }} catch(e) {{}}
                        }}''')
                        await asyncio.sleep(1.5)
                        folders_created = True
                
                if folders_created:
                    print("Folders created successfully.")
            
            # --- UPLOAD IMAGE TO RES-IMG ---
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
                
                # Build image path relative to deploy_menus.py location
                base_dir = os.path.dirname(os.path.abspath(__file__))
                image_path = os.path.join(base_dir, 'data', 'img', 'content', 'img-ready.png')
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
                    upload_confirm = page.locator('button:has(.fa-cloud-upload), button:text("업로드")').first
                    await upload_confirm.click()
                    await asyncio.sleep(4)
                    print("img-ready.png uploaded successfully!")
                else:
                    print(f"Image file not found at: {image_path}")

            except Exception as e:
                print(f"Error during res-img upload: {e}")


            # --- DEPLOY READY PAGES FOR EACH MENU ---
            print("Starting page deployment for menus...")
            if progress_cb:
                progress_cb(92, "Creating ready pages for menus (UI Mode)...")

            # Ready HTML content
            res_org = 'kookmin'
            ready_img_url = f'/_res/{res_org}/{site_id}/img/content/img-ready.png'
            ready_html = f"""<div class="content-box">
	<div class="con-box no-pd">
		<div class="img-box border">
			<img src="{ready_img_url}" alt=""/>
		</div>
	</div>
</div>"""

            # Only create pages for leaf menus
            parent_ids = {m.get('parent_id') for m in menus if m.get('parent_id')}
            leaf_menus = [m for m in menus if m.get('id') not in parent_ids]

            for i, m in enumerate(leaf_menus):
                slug = m.get('slug', '').strip()
                folder = m.get('folder', '').strip() or slug
                layout = m.get('layout', 'sub-template')
                menu_name = m.get('name', '').strip()
                
                if not slug:
                    continue

                try:
                    if progress_cb:
                        progress_cb(min(99, 92 + int((i / len(leaf_menus)) * 7)), f"Processing page: {slug}")
                    print(f"[{slug}] Navigating to Page Manager...")
                    
                    target_url_page = f'{site_url}/index.do?siteId={site_id}#!/page'
                    if page.url == target_url_page:
                        print(f"[{slug}] Already on target page. Reloading browser for clean state...")
                        await page.reload(wait_until="domcontentloaded")
                    else:
                        await page.goto(target_url_page, wait_until="domcontentloaded")
                    await asyncio.sleep(6)
                    

                    
                    # Ensure Table view is selected
                    try:
                        await page.evaluate('''() => {
                            const btnGroup = document.querySelector('.pull-right .btn-group');
                            if (btnGroup) {
                                const labels = btnGroup.querySelectorAll('label');
                                if (labels.length > 2) {
                                    labels[2].click();
                                } else if (labels.length > 1) {
                                    labels[1].click();
                                }
                            }
                        }''')
                        await asyncio.sleep(2)
                    except:
                        pass
                    
                    # 1. Expand jsTree folders on main screen
                    print(f"[{slug}] Expanding tree...")
                    try:
                        # Wait up to 10 seconds for tree nodes to be attached in DOM
                        await page.wait_for_selector('div[js-tree="folderTree.config"] li.jstree-node', state="attached", timeout=10000)
                        # Wait for Angular jstree plugin to bind and initialize
                        await page.evaluate('''async () => {
                            const el = document.querySelector('div[js-tree="folderTree.config"]');
                            for (let i = 0; i < 20; i++) {
                                if (window.angular && window.angular.element(el).jstree && window.angular.element(el).jstree(true)) {
                                    window.angular.element(el).jstree(true).open_all();
                                    return;
                                }
                                await new Promise(r => setTimeout(r, 500));
                            }
                            throw new Error("jstree instance not ready after 10s");
                        }''')
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"[{slug}] Warning: Tree expansion failed: {e}")
                    
                    # 2. Select folder on main screen
                    folder_anchor_id = f'/{site_id}/{folder}_anchor' if folder else f'/{site_id}_anchor'
                    print(f"[{slug}] Selecting folder: {folder_anchor_id}")
                    try:
                        await page.wait_for_selector(f'div[js-tree="folderTree.config"] [id="{folder_anchor_id}"]', timeout=5000)
                        await page.evaluate(f'(() => {{ const el = document.querySelector("div[js-tree=\\"folderTree.config\\"] [id=\\"{folder_anchor_id}\\"]"); if (el) el.click(); }})()')
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"[{slug}] WARNING: Could not select folder {folder_anchor_id}: {e}")
                        # Keep going but it might fail
                        
                    # 3. Check if page already exists in the folder
                    print(f"[{slug}] Checking if page exists...")
                    page_exists = await page.evaluate('''async (slug) => {
                        const table = document.querySelector('table.table');
                        if (!table) return false;
                        return table.innerText.includes(slug + '.do') || table.innerText.includes('/' + slug);
                    }''', slug)
                    
                    page_was_created = False
                    if not page_exists:
                        # Click Create Page button
                        print(f"[{slug}] Page does not exist. Clicking Create Page...")
                        await page.evaluate('''() => {
                            const btn = Array.from(document.querySelectorAll('button')).find(b =>
                                b.innerText && (b.innerText.includes('페이지 등록') || b.innerText.includes('등록') || b.innerText.includes('Thêm'))
                            ) || document.querySelector('button[x-ng-click="pg.addPage()"]');
                            if (btn) btn.click();
                        }''')
                        
                        # Wait for modal
                        try:
                            await page.wait_for_selector('.modal-dialog', timeout=5000)
                        except:
                            pass
                        await asyncio.sleep(1)
                        try:
                            await page.screenshot(path=f"scratch/deploy_{slug}_1_modal_open.png")
                        except:
                            pass
                        
                        # 4. Fill modal filename and title
                        print(f"[{slug}] Assuring modal form is filled...")
                        await page.evaluate('''async (args) => {
                            const slug = args[0];
                            const menuName = args[1];
                            const siteId = args[2];
                            const layoutName = args[3];
                            const folderAnchorId = args[4];
                            
                            // Expand the menu tree inside the modal
                            const treeEl = document.querySelector('.modal-dialog div[js-tree="menuTree.config"]');
                            if (treeEl) {
                                for (let i = 0; i < 20; i++) {
                                    if (window.angular && window.angular.element(treeEl).jstree && window.angular.element(treeEl).jstree(true)) {
                                        window.angular.element(treeEl).jstree(true).open_all();
                                        break;
                                    }
                                    await new Promise(r => setTimeout(r, 500));
                                }
                            }
                            
                            // Expand the folder tree inside the modal
                            const folderTreeEl = document.querySelector('.modal-dialog div[js-tree="folderTree.config"], .modal-dialog div[js-tree="pg.folderTree"]');
                            if (folderTreeEl) {
                                for (let i = 0; i < 20; i++) {
                                    if (window.angular && window.angular.element(folderTreeEl).jstree && window.angular.element(folderTreeEl).jstree(true)) {
                                        window.angular.element(folderTreeEl).jstree(true).open_all();
                                        break;
                                    }
                                    await new Promise(r => setTimeout(r, 500));
                                }
                            }
                            
                            // Wait a bit for DOM to update after expansion
                            await new Promise(r => setTimeout(r, 1000));
                            
                            // Select matching folder in modal tree if available
                            if (folderTreeEl && folderAnchorId) {
                                const folderModalItem = folderTreeEl.querySelector(`[id="${folderAnchorId}"]`);
                                if (folderModalItem) {
                                    folderModalItem.click();
                                }
                            }
                            
                            const fnInput = document.querySelector('input[name="filename"]');
                            if (fnInput) {
                                fnInput.value = slug;
                                fnInput.dispatchEvent(new Event('input', {bubbles: true}));
                            }
                            const titleInput = document.querySelector('input[name="title"]');
                            if (titleInput) {
                                titleInput.value = menuName;
                                titleInput.dispatchEvent(new Event('input', {bubbles: true}));
                            }
                            
                            // Select matching menu in modal tree if available
                            const modalAnchors = Array.from(document.querySelectorAll('.modal-dialog .jstree-anchor'));
                            const modalItem = modalAnchors.find(a => a.innerText.trim() === menuName);
                            if (modalItem) {
                                modalItem.click();
                            }

                            const selectTpl = (name, fname) => {
                                const el = document.querySelector(`[name="${name}"]`);
                                if (el) {
                                    const s = window.angular.element(el).scope();
                                    const list = s.pg[`${name}List`] || [];
                                    const item = list.find(t => t.filename === fname && t.siteId === siteId) || list.find(t => t.filename === fname);
                                    if (item) window.angular.element(el).controller('uiSelect').select(item);
                                }
                            };
                            selectTpl('headTemplate', 'common.jsp');
                            selectTpl('layoutTemplate', layoutName + '.jsp');
                        }''', [slug, menu_name, site_id, layout, folder_anchor_id.replace('#', '')])
                        await asyncio.sleep(1)
                        try:
                            await page.screenshot(path=f"scratch/deploy_{slug}_2_modal_filled.png")
                        except:
                            pass
                        await asyncio.sleep(0.5)
                        
                        # Check duplicate warning in modal
                        has_warning = await page.evaluate('''() => {
                            const body = document.body.innerText || '';
                            return body.includes('동일한 파일이 존재') || body.includes('이미 존재');
                        }''')
                        
                        if has_warning:
                            print(f"[{slug}] Warning: Page already exists according to modal warning. Closing modal and editing...")
                            try:
                                await page.get_by_role("button", name="닫기").click()
                            except:
                                await page.keyboard.press("Escape")
                            await asyncio.sleep(2)
                            page_exists = True
                        else:
                            # 5. Save modal using "저장 후 편집" (Save & Edit)
                            print(f"[{slug}] Saving modal using Save & Edit...")
                            try:
                                await page.evaluate('''() => {
                                    const btn = Array.from(document.querySelectorAll('.modal-dialog button, .modal-dialog a')).find(b => 
                                        b.innerText && b.innerText.includes('저장 후 편집')
                                    ) || document.querySelector('.modal-dialog .modal-footer .btn-primary, .modal-dialog .btn-primary');
                                    if (btn) btn.click();
                                }''')
                                await asyncio.sleep(5)
                                page_was_created = True
                            except Exception as e:
                                print(f"Error saving modal: {e}")
                            await asyncio.sleep(1)
                            try:
                                await page.screenshot(path=f"scratch/deploy_{slug}_3_after_modal_save.png")
                            except:
                                pass
                            
                    if page_exists and not page_was_created:
                        print(f"[{slug}] Page already exists. Opening editor directly...")
                        # 6. Click Edit (Brush) button for the specific page
                        print(f"[{slug}] Clicking Edit (Brush) button...")
                        try:
                            # Set pagination to 100 to ensure row is visible
                            await page.evaluate('''() => {
                                const btns = Array.from(document.querySelectorAll('.pagination-sm a'));
                                const btn100 = btns.find(b => b.innerText.trim() === '100');
                                if (btn100) btn100.click();
                            }''')
                            await asyncio.sleep(2)
                            
                            # Find the row and click its edit button
                            await page.evaluate(f'''(slug) => {{
                                const trs = Array.from(document.querySelectorAll('table tbody tr'));
                                for (let tr of trs) {{
                                    if (tr.innerText.includes(slug)) {{
                                        const btn = tr.querySelector('.zmdi-brush');
                                        if (btn) btn.click();
                                        return;
                                    }}
                                }}
                                // Fallback if not found by slug
                                const anyBtn = document.querySelector('.zmdi-brush');
                                if (anyBtn) anyBtn.click();
                            }}''', slug)
                            await asyncio.sleep(5)
                        except Exception as e:
                            print(f"[{slug}] Error clicking edit button: {e}")
                            continue
                        try:
                            await page.screenshot(path=f"scratch/deploy_{slug}_4_after_edit_click.png")
                        except:
                            pass
                            
                        await asyncio.sleep(3)     
                    await asyncio.sleep(3)
                    
                    # 8. Paste HTML
                    print(f"[{slug}] Clicking HTML Code View...")
                    try:
                        # Click the HTML view button using Playwright mouse simulation (only targeting visible ones)
                        await page.locator('button[data-cmd="html"] >> visible=true').first.click()
                    except Exception as e:
                        print(f"[{slug}] Could not click HTML view: {e}")
                    await asyncio.sleep(2)
                    
                    print(f"[{slug}] Pasting HTML via Keyboard...")
                    try:
                        # Focus the visible textarea inside the editor
                        await page.locator('textarea >> visible=true').first.focus()
                        await asyncio.sleep(0.5)
                        # Select all and replace content
                        await page.keyboard.press("Control+A")
                        await page.keyboard.press("Backspace")
                        await page.keyboard.insert_text(ready_html)
                    except Exception as e:
                        print(f"[{slug}] Could not paste HTML: {e}")
                    await asyncio.sleep(2)
                    
                    print(f"[{slug}] Clicking HTML Code View AGAIN...")
                    try:
                        await page.locator('button[data-cmd="html"] >> visible=true').first.click()
                    except Exception as e:
                        pass
                    await asyncio.sleep(2)
                    try:
                        await page.screenshot(path=f"scratch/deploy_{slug}_5_after_html_paste.png")
                    except:
                        pass
                    # 9. Save Editor
                    print(f"[{slug}] Saving Editor...")
                    try:
                        saved = await page.evaluate('''() => {
                            const btn1 = document.querySelector('button[x-ng-click="editor.save()"], button[ng-click="editor.save()"]');
                            if (btn1) {
                                btn1.click();
                                return "editor.save clicked";
                            }
                            const btn2 = document.querySelector('button[x-ng-click="pg.save()"], button[ng-click="pg.save()"]');
                            if (btn2) {
                                btn2.click();
                                return "pg.save clicked";
                            }
                            return "no save button found";
                        }''')
                        print(f"[{slug}] Save action result: {saved}")
                        await asyncio.sleep(4)
                    except Exception as e:
                        print(f"[{slug}] Error saving editor: {e}")
                    
                    try:
                        await page.screenshot(path=f"scratch/deploy_{slug}_6_after_editor_save.png")
                    except:
                        pass
                    await asyncio.sleep(2)
                    print(f"[{slug}] Done deploying page.")
                    print(f"[{slug}] Done.")
                    
                except Exception as e:
                    print(f"[{slug}] Error: {e}")

            if progress_cb:
                progress_cb(100, "Completed!")
            return {'success': True, 'message': 'Menus, folders and ready pages deployed successfully!'}

        except Exception as e:
            print(f'Menu deploy ERROR: {e}')
            return {'success': False, 'message': f'Menu deploy error: {str(e)}'}
        finally:
            await browser.close()

def run_deploy_menus(site_url, site_id, username, password, menus, progress_cb=None):
    return asyncio.run(deploy_menus_task_async(site_url, site_id, username, password, menus, progress_cb))
def run_deploy_menus(site_url, site_id, username, password, menus, progress_cb=None):
    return asyncio.run(deploy_menus_task_async(site_url, site_id, username, password, menus, progress_cb))
