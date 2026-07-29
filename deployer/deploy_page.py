import asyncio

async def deploy_pages(page, site_url, site_id, menus, progress_cb, total_items, current_item):
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
                print(f"[{slug}] Already on target page. Skipping reload...")
                await asyncio.sleep(1)
            else:
                await page.goto(target_url_page, wait_until="domcontentloaded")
                await asyncio.sleep(4)
            
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
                    
                # 4. Fill Modal Form
                print(f"[{slug}] Assuring modal form is filled...")
                # Pass folder name instead of ID
                await page.evaluate(f'''async (args) => {{
                    const slug = args[0];
                    const menuName = args[1];
                    const siteId = args[2];
                    const layoutName = args[3];
                    const folderName = args[4];
                    
                    // Expand the menu tree inside the modal
                    const treeEl = document.querySelector('.modal-dialog div[js-tree="menuTree.config"]');
                    if (treeEl) {{
                        for (let i = 0; i < 20; i++) {{
                            if (window.angular && window.angular.element(treeEl).jstree && window.angular.element(treeEl).jstree(true)) {{
                                window.angular.element(treeEl).jstree(true).open_all();
                                break;
                            }}
                            await new Promise(r => setTimeout(r, 500));
                        }}
                    }}
                    
                    // Expand the folder tree inside the modal
                    const folderTreeEl = document.querySelector('.modal-dialog div[js-tree="folderTree.config"], .modal-dialog div[js-tree="pg.folderTree"]');
                    if (folderTreeEl) {{
                        for (let i = 0; i < 20; i++) {{
                            if (window.angular && window.angular.element(folderTreeEl).jstree && window.angular.element(folderTreeEl).jstree(true)) {{
                                window.angular.element(folderTreeEl).jstree(true).open_all();
                                break;
                            }}
                            await new Promise(r => setTimeout(r, 500));
                        }}
                    }}
                    
                    await new Promise(r => setTimeout(r, 1000));
                    
                    // Select matching folder in modal tree by text
                    if (folderTreeEl && folderName) {{
                        const folderAnchors = Array.from(folderTreeEl.querySelectorAll('.jstree-anchor'));
                        const folderModalItem = folderAnchors.find(a => a.innerText.trim() === folderName);
                        if (folderModalItem) {{
                            folderModalItem.click();
                        }}
                    }}
                    
                    const fnInput = document.querySelector('input[name="filename"]');
                    if (fnInput) {{
                        fnInput.value = slug;
                        fnInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                    }}
                    const titleInput = document.querySelector('input[name="title"]');
                    if (titleInput) {{
                        titleInput.value = menuName;
                        titleInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                    }}
                    
                    // Select matching menu in modal tree if available
                    const modalAnchors = Array.from(document.querySelectorAll('.modal-dialog .jstree-anchor'));
                    const menuId = args[5];
                    const modalItem = modalAnchors.find(a => (menuId && a.innerText.includes(String(menuId))) || a.innerText.trim() === menuName);
                    if (modalItem) {{
                        modalItem.click();
                    }}

                    const selectTpl = (name, fname) => {{
                        const el = document.querySelector(`[name="${{name}}"]`);
                        if (el) {{
                            try {{
                                const s = window.angular.element(el).scope();
                                const list = s.pg[`${{name}}List`] || [];
                                const item = list.find(t => t.filename === fname && t.siteId === siteId) || 
                                             list.find(t => t.filename === fname) || 
                                             list.find(t => t.filename.includes('sub.jsp')) || 
                                             list[0];
                                if (item) {{
                                    window.angular.element(el).controller('uiSelect').select(item);
                                }}
                            }} catch (e) {{}}
                            
                            setTimeout(() => {{
                                const textSpan = el.querySelector('.ui-select-match-text');
                                if (!textSpan || textSpan.innerText.trim() === '' || textSpan.innerText.trim().includes('선택')) {{
                                    const toggle = el.querySelector('.ui-select-toggle');
                                    if (toggle) toggle.click();
                                    setTimeout(() => {{
                                        const choices = Array.from(document.querySelectorAll('.ui-select-choices-row-inner, .ui-select-choices-row'));
                                        const choice = choices.find(c => c.innerText.includes(fname)) || choices.find(c => c.innerText.includes('sub.jsp')) || choices[0];
                                        if (choice) choice.click();
                                    }}, 500);
                                }}
                            }}, 200);
                        }}
                    }};
                    selectTpl('headTemplate', 'common.jsp');
                    setTimeout(() => {{ selectTpl('layoutTemplate', layoutName + '.jsp'); }}, 1000);
                }}''', [slug, menu_name, site_id, layout, folder, str(m.get('id', ''))])
                await asyncio.sleep(2.5)

                
                # Check duplicate warning in modal
                has_warning = await page.evaluate('''() => {
                    const modal = document.querySelector('.modal-dialog');
                    if (!modal) return false;
                    return modal.innerText.includes('동일한 파일이 존재') || modal.innerText.includes('이미 존재');
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
                    # 5. Save modal using "저장 후 편집" (Save)
                    print(f"[{slug}] Saving modal using Save...")
                    try:
                        await page.evaluate('''() => {
                            const btn = Array.from(document.querySelectorAll('.modal-dialog button, .modal-dialog a')).find(b => 
                                b.innerText && (b.innerText.includes('저장 후 편집') || b.innerText.trim() === '저장 후 편집')
                            ) || document.querySelector('.modal-dialog .modal-footer .btn-primary, .modal-dialog .btn-primary');
                            if (btn) btn.click();
                        }''')
                        await asyncio.sleep(2)
                        page_was_created = True
                    except Exception as e:
                        print(f"Error saving modal: {e}")
                    await asyncio.sleep(1)
                    
            if page_exists and not page_was_created:
                print(f"[{slug}] Page already exists. Proceeding to update HTML via API...")
            
            # 6. Save page HTML via API
            print(f"[{slug}] Inserting ready HTML via UI...")
            
            try:
                # We need to open the editor from the grid if not already open
                print(f"[{slug}] Opening editor for existing page...")
                err = await page.evaluate(f'''async (slug) => {{
                    try {{
                        const htmlBtn = document.querySelector('button[data-cmd="html"]');
                        if (htmlBtn && htmlBtn.offsetParent !== null) return null; // Already open
                        
                        const btns = Array.from(document.querySelectorAll('.pagination-sm a'));
                        const btn100 = btns.find(b => b.innerText.trim() === '100');
                        if (btn100) btn100.click();
                        await new Promise(r => setTimeout(r, 2000));
                        
                        const searchInput = document.querySelector('input[ng-model*="search"], input[placeholder*="검색"]');
                        if (searchInput) {{
                            searchInput.value = slug;
                            searchInput.dispatchEvent(new Event('input'));
                            searchInput.dispatchEvent(new Event('change'));
                            const searchBtn = document.querySelector('button[ng-click*="search"], .zmdi-search');
                            if (searchBtn) searchBtn.click();
                            await new Promise(r => setTimeout(r, 2000));
                        }}
                        
                        const rows = Array.from(document.querySelectorAll('table tbody tr'));
                        for (let tr of rows) {{
                            if (tr.innerText.includes(slug)) {{
                                const btn = tr.querySelector('.zmdi-brush, button[ng-click*="edit"], a[ng-click*="edit"]');
                                if (btn) {{
                                    btn.click();
                                    return null;
                                }}
                            }}
                        }}
                        // Fallback if not found by slug
                        const anyBtn = document.querySelector('.zmdi-brush');
                        if (anyBtn) {{
                            anyBtn.click();
                            return null;
                        }}
                        return "Edit button not found in row";
                    }} catch(e) {{
                        return "Error clicking edit: " + e.message;
                    }}
                }}''', slug)
                if err: print(f"[{slug}] Warning opening editor: {err}")
                await asyncio.sleep(2)
                    
                # Wait for modal/editor
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
                    
            except Exception as e:
                print(f"[{slug}] Error saving HTML via UI: {e}")
            
            await asyncio.sleep(1)
            print(f"[{slug}] Done deploying page.")
            
        except Exception as e:
            print(f"[{slug}] Error: {e}")
