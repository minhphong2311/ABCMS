import asyncio

async def deploy_pages(page, site_url, site_id, menus, progress_cb, total_items, current_item, is_cancelled=None):
    print("\n" + "="*50)
    print("6. KIỂM TRA PAGE")
    print("="*50)
    if progress_cb:
        progress_cb(92, "Creating ready pages for menus (UI Mode)...")

    # Ready HTML content
    res_org = 'kookmin'
    ready_img_url = f'/_res/{res_org}/{site_id}/img/content/img-ready.png'
    ready_html = f"""<div class="content-box">
	<div class="con-box no-pd">
		<div class="img-box border">
			<img src="{ready_img_url}" alt="ready"/>
		</div>
	</div>
</div>"""

    # Only create pages for leaf menus
    parent_ids = {m.get('parent_id') for m in menus if m.get('parent_id')}
    leaf_menus = [m for m in menus if m.get('id') not in parent_ids]

    for i, m in enumerate(leaf_menus):
        if is_cancelled and is_cancelled():
            raise Exception("Deploy cancelled by user")
            
        slug = m.get('slug', '').strip()
        folder = m.get('folder', '').strip() or slug
        layout = m.get('layout', 'sub-template')
        menu_name = m.get('name', '').strip()
        
        if not slug:
            continue

        try:
            if progress_cb:
                progress_cb(min(99, 92 + int((i / len(leaf_menus)) * 7)), f"Processing page: {slug}")
            print(f"\n  6.1 Mở Folder '{folder}' (Page Manager)...")
            
            target_url_page = f'{site_url}/index.do?siteId={site_id}#!/page'
            await page.goto("about:blank")
            await asyncio.sleep(0.6)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            await page.goto(target_url_page, wait_until="domcontentloaded")
            await asyncio.sleep(2.4)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')

            
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
                await asyncio.sleep(1.2)
                if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            except Exception as e:
                if str(e) == 'Deploy cancelled by user': raise
                if str(e) == 'Deploy cancelled by user': raise
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
                await asyncio.sleep(1.2)
                if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            except Exception as e:
                if str(e) == 'Deploy cancelled by user': raise
                if str(e) == 'Deploy cancelled by user': raise
                print(f"[{slug}] Warning: Tree expansion failed: {e}")
            
            # 2. Select folder on main screen
            folder_anchor_id = f'/{site_id}/{folder}_anchor' if folder else f'/{site_id}_anchor'
            print(f"[{slug}] Selecting folder: {folder_anchor_id}")
            try:
                await page.wait_for_selector(f'div[js-tree="folderTree.config"] [id="{folder_anchor_id}"]', timeout=5000)
                await page.evaluate(f'(() => {{ const el = document.querySelector("div[js-tree=\\"folderTree.config\\"] [id=\\"{folder_anchor_id}\\"]"); if (el) el.click(); }})()')
                await asyncio.sleep(1.2)
                if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            except Exception as e:
                if str(e) == 'Deploy cancelled by user': raise
                if str(e) == 'Deploy cancelled by user': raise
                print(f"[{slug}] WARNING: Could not select folder {folder_anchor_id}: {e}")
                # Keep going but it might fail
                
            # 3. Check if page already exists in the folder
            print(f"  6.2 Kiểm tra Page '{slug}' trong Folder '{folder}'...")
            page_exists = await page.evaluate('''async (slug) => {
                const container = document.querySelector('[ng-controller], .content-wrapper, body');
                if (!container) return false;
                const text = container.innerText || '';
                return text.includes(slug + '.do') || text.includes('/' + slug + '.jsp');
            }''', slug)
            
            page_was_created = False
            if page_exists:
                print(f"  6.3 Page '{slug}' đã tồn tại → Chuyển sang kiểm tra Page tiếp theo.")
            else:
                print(f"  6.4 Page '{slug}' chưa tồn tại → Tiến hành Tạo Page...")
                await page.evaluate('''() => {
                    const btn = Array.from(document.querySelectorAll('button')).find(b =>
                        b.innerText && (b.innerText.includes('페이지 등록') || b.innerText.includes('등록') || b.innerText.includes('Thêm'))
                    ) || document.querySelector('button[x-ng-click="pg.addPage()"]');
                    if (btn) btn.click();
                }''')
                
                try:
                    await page.wait_for_selector('.modal-dialog', timeout=5000)
                except Exception as e:
                    if str(e) == 'Deploy cancelled by user': raise
                    if str(e) == 'Deploy cancelled by user': raise
                    pass
                await asyncio.sleep(0.6)
                if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                    
                # 4. Fill Modal Form
                await page.evaluate(f'''async (args) => {{
                    const slug = args[0];
                    const menuName = args[1];
                    const siteId = args[2];
                    const layoutName = args[3];
                    const folderName = args[4];
                    
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
                await asyncio.sleep(1.5)
                if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')

                has_warning = await page.evaluate('''() => {
                    const modal = document.querySelector('.modal-dialog');
                    if (!modal) return false;
                    return modal.innerText.includes('동일한 파일이 존재') || modal.innerText.includes('이미 존재');
                }''')
                
                if has_warning:
                    try:
                        await page.get_by_role("button", name="닫기").click()
                    except Exception as e:
                        if str(e) == 'Deploy cancelled by user': raise
                        if str(e) == 'Deploy cancelled by user': raise
                        await page.keyboard.press("Escape")
                    await asyncio.sleep(1.2)
                    if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                    page_exists = True
                else:
                    try:
                        await page.evaluate('''() => {
                            const btn = Array.from(document.querySelectorAll('.modal-dialog button, .modal-dialog a')).find(b => 
                                b.innerText && (b.innerText.includes('저장 후 편집') || b.innerText.trim() === '저장 후 편집')
                            ) || document.querySelector('.modal-dialog .modal-footer .btn-primary, .modal-dialog .btn-primary');
                            if (btn) btn.click();
                        }''')
                        await asyncio.sleep(1.2)
                        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                        page_was_created = True
                    except Exception as e:
                        if str(e) == 'Deploy cancelled by user': raise
                        if str(e) == 'Deploy cancelled by user': raise
                        print(f"  Error saving modal: {e}")
                    await asyncio.sleep(0.6)
                    if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                    
            print(f"  6.5 Mở màn hình Edit Page cho '{slug}'...")
            try:
                # Check if editor is already open for this page
                is_editor_open = await page.evaluate(f'''(slug) => {{
                    try {{
                        const btn = document.querySelector('button[ng-click*="editor.save()"], button[x-ng-click*="editor.save()"]');
                        if (!btn) return false;
                        const s = window.angular && window.angular.element(btn).scope();
                        if (s && s.editor && s.editor.item && (s.editor.item.filename === slug || s.editor.item.filename === slug + '.jsp')) return true;
                        return !!btn;
                    }} catch(e) {{ return false; }}
                }}''', slug)

                if not is_editor_open:
                    print(f"  Mở editor từ danh sách trang...")
                    await page.evaluate(f'''async (slug) => {{
                        try {{
                            const searchInput = document.querySelector('input[ng-model*="search"], input[placeholder*="검색"]');
                            if (searchInput) {{
                                searchInput.value = slug;
                                searchInput.dispatchEvent(new Event('input', {{bubbles:true}}));
                                searchInput.dispatchEvent(new Event('change', {{bubbles:true}}));
                                const searchBtn = document.querySelector('button[ng-click*="search"], .zmdi-search');
                                if (searchBtn) searchBtn.click();
                                await new Promise(r => setTimeout(r, 2000));
                            }}
                            const rows = Array.from(document.querySelectorAll('table tbody tr'));
                            for (let tr of rows) {{
                                if (tr.innerText.includes(slug)) {{
                                    const btn = tr.querySelector('.zmdi-brush, button[ng-click*="edit"], a[ng-click*="edit"]');
                                    if (btn) {{ btn.click(); return; }}
                                }}
                            }}
                            const anyBtn = document.querySelector('.zmdi-brush');
                            if (anyBtn) anyBtn.click();
                        }} catch(e) {{}}
                    }}''', slug)
                    await asyncio.sleep(2.4)
                    if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                
                print(f"  6.6 Chuyển sang View Code (Click nút </>)...")
                
                # Loop to verify HTML exists in View Code and paste + save if not present
                max_attempts = 3
                html_verified = False
                
                for attempt in range(1, max_attempts + 1):
                    # Ensure View Code is clicked/active
                    await page.evaluate('''() => {
                        const btn1 = document.querySelector('.fr-command[data-cmd="html"]') || document.querySelector('button[data-cmd="html"]');
                        if (btn1 && !btn1.classList.contains('fr-active')) {
                            btn1.click();
                        }
                    }''')
                    await asyncio.sleep(0.9)
                    if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')

                    print(f"  6.7 Kiểm tra bên trong View Code (Lần thử {attempt}/{max_attempts})...")
                    current_html = await page.evaluate('''() => {
                        try {
                            const cm = document.querySelector('.CodeMirror');
                            if (cm && cm.CodeMirror) return cm.CodeMirror.getValue();
                        } catch(e) {}
                        try {
                            let val = "";
                            Array.from(document.querySelectorAll('*')).some(el => {
                                const s = window.angular && window.angular.element(el).scope();
                                if (s && s.editor && s.editor.item && s.editor.item.contentText) {
                                    val = s.editor.item.contentText;
                                    return true;
                                }
                            });
                            return val;
                        } catch(e) {}
                        return "";
                    }''')

                    if current_html and current_html.strip() != "" and current_html.strip() != "<p><br></p>":
                        print(f"  ✓ 6.7 THÀNH CÔNG: Đã có sẵn nội dung HTML trong View Code của Page '{slug}'!")
                        html_verified = True
                        break
                    else:
                        print(f"  --> Chưa có nội dung HTML trong View Code → Tiến hành nạp mã HTML chuẩn...")
                        
                        # Click HTML View
                        print(f"  [{slug}] Clicking HTML Code View...")
                        try:
                            await page.locator('button[data-cmd="html"] >> visible=true').first.click()
                        except Exception as e:
                            if str(e) == 'Deploy cancelled by user': raise
                            if str(e) == 'Deploy cancelled by user': raise
                            print(f"  [{slug}] Could not click HTML view: {e}")
                        await asyncio.sleep(1.2)
                        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                        
                        # Paste HTML via Keyboard
                        print(f"  [{slug}] Pasting HTML via Keyboard...")
                        try:
                            await page.locator('textarea, .CodeMirror-code >> visible=true').first.focus()
                            await asyncio.sleep(0.5)
                            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                            await page.keyboard.press("Control+A")
                            await page.keyboard.press("Backspace")
                            await page.keyboard.insert_text(ready_html)
                        except Exception as e:
                            if str(e) == 'Deploy cancelled by user': raise
                            if str(e) == 'Deploy cancelled by user': raise
                            print(f"  [{slug}] Could not paste HTML: {e}")
                        await asyncio.sleep(1.2)
                        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                        
                        # Click HTML View AGAIN to sync
                        print(f"  [{slug}] Clicking HTML Code View AGAIN...")
                        try:
                            await page.locator('button[data-cmd="html"] >> visible=true').first.click()
                        except Exception as e:
                            if str(e) == 'Deploy cancelled by user': raise
                            if str(e) == 'Deploy cancelled by user': raise
                            pass
                        await asyncio.sleep(1.2)
                        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                        
                        # Save Editor
                        print(f"  [{slug}] Saving Editor...")
                        try:
                            saved = await page.evaluate('''() => {
                                const btn1 = document.querySelector('button[x-ng-click="editor.save()"], button[ng-click="editor.save()"]');
                                if (btn1) { btn1.click(); return "editor.save clicked"; }
                                const btn2 = document.querySelector('button[x-ng-click="pg.save()"], button[ng-click="pg.save()"]');
                                if (btn2) { btn2.click(); return "pg.save clicked"; }
                                const btn3 = Array.from(document.querySelectorAll('button, a')).find(b => (b.innerText || '').trim().includes('저장') || (b.innerText || '').trim() === 'Save');
                                if (btn3) { btn3.click(); return "Text 저장 clicked"; }
                                return "no save button found";
                            }''')
                            print(f"  [{slug}] Save action result: {saved}")
                        except Exception as e:
                            if str(e) == 'Deploy cancelled by user': raise
                            if str(e) == 'Deploy cancelled by user': raise
                            print(f"  [{slug}] Error saving editor: {e}")
                        
                        await asyncio.sleep(2.4)
                        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')

                        # Handle SweetAlert (Success or confirm popup)
                        await page.evaluate('''() => {
                            const confirmBtn = document.querySelector('.sweet-alert button.confirm, .sweet-alert .confirm, button.confirm');
                            if (confirmBtn) confirmBtn.click();
                        }''')
                        await asyncio.sleep(1.8)
                        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                        
                        # Click Back / Close button to exit Edit Page
                        print("  Nhấn Back/Đóng để thoát Edit Page...")
                        await page.evaluate('''() => {
                            const closeBtn = Array.from(document.querySelectorAll('button, a')).find(b => 
                                (b.innerText || '').includes('이전으로') || 
                                (b.innerText || '').includes('목록으로') || 
                                (b.innerText || '').includes('닫기') ||
                                (b.innerText || '').includes('목록') ||
                                (b.innerText || '').includes('List')
                            );
                            if (closeBtn) closeBtn.click();
                        }''')
                        await asyncio.sleep(2.4)
                        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')

                if not html_verified:
                    raise Exception(f"Kiểm tra thất bại sau {max_attempts} lần thử: Page '{slug}' chưa có nội dung HTML trong View Code.")

            except Exception as e:
                if str(e) == 'Deploy cancelled by user': raise
                if str(e) == 'Deploy cancelled by user': raise
                print(f"  [Lỗi xử lý HTML page {slug}]: {e}")
            
            # Go back to page manager for next page
            await page.goto(target_url_page, wait_until='domcontentloaded')
            await asyncio.sleep(1.8)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            print(f"  6.8 Lặp lại cho đến khi kiểm tra hết tất cả Page trong Folder (Hoàn thành page {i+1}/{len(leaf_menus)}).")

            
        except Exception as e:
            if str(e) == 'Deploy cancelled by user': raise
            if str(e) == 'Deploy cancelled by user': raise
            print(f"  [Lỗi page {slug}]: {e}")

    print("  ✓ Hoàn thành kiểm tra tất cả các Page.")


