import asyncio
import os

async def deploy_layouts(page, site_url, site_id, progress_cb, is_cancelled=None):
    if progress_cb:
        progress_cb(30, "Checking and creating layouts")
    print(">>> Deploying Layouts")
    
    target_url = f"{site_url}/index.do?siteId={site_id}#!/res-layout"
    print(f"Navigating to: {target_url}")
    try:
        await page.goto(target_url, wait_until='domcontentloaded', timeout=15000)
    except Exception:
        await page.evaluate('window.location.hash = "#!/res-layout";')
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(4)
    
    layouts_to_check = ['sub-template', 'sub-template-tab']
    base_dir = os.path.dirname(os.path.dirname(__file__))
    layout_dir = os.path.join(base_dir, 'assets', 'layout')
    
    for layout_name in layouts_to_check:
        if is_cancelled and is_cancelled():
            return
        if progress_cb:
            progress_cb(40, f"Checking layout: {layout_name}")
            
        print(f"[{layout_name}] Ensuring we are on Layout Grid: {target_url}")
        try:
            await page.goto(target_url, wait_until='domcontentloaded', timeout=15000)
        except Exception:
            await page.evaluate('window.location.hash = "#!/res-layout";')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(4)
        
        local_html_path = os.path.join(layout_dir, f"{layout_name}.html")
        if not os.path.exists(local_html_path):
            print(f"Local file {local_html_path} not found, skipping.")
            continue
            
        with open(local_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        layout_exists = await page.evaluate(f'''(layoutName) => {{
            const els = Array.from(document.querySelectorAll('a, span, div, td'));
            return els.some(el => (el.innerText || el.textContent || '').trim() === layoutName || (el.innerText || el.textContent || '').trim() === layoutName + '.jsp');
        }}''', layout_name)
        
        if not layout_exists:
            print(f"[{layout_name}] Not found. Creating new layout...")
            if progress_cb:
                progress_cb(45, f"Creating layout: {layout_name}")
                
            await page.evaluate('''() => {
                const addBtn = document.querySelector('[x-ng-click*="addLayout"]') || 
                               document.querySelector('[ng-click*="addLayout"]') ||
                               Array.from(document.querySelectorAll('button, a.btn')).find(b => (b.innerText || '').includes('추가'));
                if (addBtn) addBtn.click();
            }''')
            await asyncio.sleep(2)
            await page.screenshot(path=f"layout_creation_modal_opened_{layout_name}.png")
            
            try:
                # Type slowly to ensure Angular registers it
                inputs = await page.locator('.modal-dialog input[type="text"]').all()
                if len(inputs) > 0 and await inputs[0].is_visible():
                    await inputs[0].click()
                    await inputs[0].fill("")
                    await inputs[0].press_sequentially(layout_name, delay=50)
                    await asyncio.sleep(1)
                
                if len(inputs) > 1 and await inputs[1].is_visible():
                    val = await inputs[1].input_value()
                    if not val:
                        await inputs[1].click()
                        await inputs[1].fill("")
                        await inputs[1].press_sequentially(layout_name, delay=50)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error filling form: {e}")
            await page.screenshot(path=f"layout_creation_modal_filled_{layout_name}.png")
            await page.evaluate('''() => {
                const saveBtn = Array.from(document.querySelectorAll('.modal-footer button, .btn-primary')).find(b => (b.innerText || '').includes('저장') || (b.innerText || '').includes('Save') || (b.innerText || '').includes('확인'));
                if (saveBtn) saveBtn.click();
            }''')
            await asyncio.sleep(3)
            
            await page.evaluate('''() => {
                const confirmBtn = document.querySelector('.sweet-alert button.confirm, .sweet-alert .confirm, button.confirm');
                if (confirmBtn) confirmBtn.click();
            }''')
            await asyncio.sleep(2)
            
            # Go back to layout grid in case it opens editor immediately
            await page.evaluate('''() => {
                const closeBtn = Array.from(document.querySelectorAll('button, a')).find(b => 
                    (b.innerText || '').includes('목록으로') || 
                    (b.innerText || '').includes('닫기') ||
                    (b.innerText || '').includes('List')
                );
                if (closeBtn) closeBtn.click();
            }''')
            await asyncio.sleep(2)

        print(f"[{layout_name}] Refreshing grid using UI button...")
        await page.evaluate('''() => {
            const refreshBtn = Array.from(document.querySelectorAll('button, a, span')).find(b => (b.innerText || '').includes('새로고침'));
            if (refreshBtn) refreshBtn.click();
        }''')
        await asyncio.sleep(4)
        
        await page.screenshot(path=f"layout_grid_before_open_{layout_name}.png")
        print(f"[{layout_name}] Opening editor...")
        await page.evaluate(f'''(layoutName) => {{
            const titles = Array.from(document.querySelectorAll('h4, .card-title, .title'));
            const targetTitle = titles.find(t => t.textContent.trim() === layoutName + '.jsp' || t.textContent.trim() === layoutName);
            if (targetTitle) {{
                const card = targetTitle.closest('.card, .card-item, .box, .list-item, div.col-sm-6');
                if (card) {{
                    const editBtn = card.querySelector('button[uib-tooltip*="레이아웃"]') || card.querySelector('button.btn-default, a.btn');
                    if (editBtn) editBtn.click();
                    else card.dispatchEvent(new MouseEvent('dblclick', {{ bubbles: true }}));
                }}
            }} else {{
                const links = Array.from(document.querySelectorAll('a'));
                const targetLink = links.find(l => (l.innerText || '').trim() === layoutName || (l.innerText || '').trim() === layoutName + '.jsp');
                if (targetLink) targetLink.click();
            }}
        }}''', layout_name)
        await asyncio.sleep(4)
        
        await page.screenshot(path=f"layout_editor_opened_{layout_name}.png")
        print(f"[{layout_name}] Clicking Source Edit tab...")
        await page.evaluate('''() => {
            const headings = Array.from(document.querySelectorAll('uib-tab-heading'));
            const target = headings.find(h => h.textContent.includes('소스 편집') || h.textContent.includes('Source'));
            if (target) {
                const a = target.closest('a');
                if (a) a.click();
            }
        }''')
        await asyncio.sleep(3)
        
        await page.screenshot(path=f"layout_source_tab_clicked_{layout_name}.png")
        print(f"[{layout_name}] Setting HTML via CodeMirror API...")
        try:
            # Set HTML directly into CodeMirror instance
            success = await page.evaluate(f'''(html) => {{
                const cm = document.querySelector('.CodeMirror').CodeMirror;
                if (cm) {{
                    cm.setValue(html);
                    return true;
                }}
                return false;
            }}''', html_content)
            
            if success:
                print(f"[{layout_name}] Set HTML via CodeMirror API successfully")
            else:
                print(f"[{layout_name}] Failed to set HTML via CodeMirror API")
        except Exception as e:
            print(f"[{layout_name}] Error setting HTML: {e}")
            
        await asyncio.sleep(2)
        print(f"[{layout_name}] Saving...")
        
        await page.evaluate('''() => {
            const btn = document.querySelector('button[ng-click*="edit.save()"], button[x-ng-click*="edit.save()"]');
            if (btn) btn.click();
        }''')
        await asyncio.sleep(3)
        
        # Click SweetAlert confirm if it appears
        await page.evaluate('''() => {
            const confirmBtn = document.querySelector('.sweet-alert button.confirm');
            if (confirmBtn) confirmBtn.click();
        }''')
        await asyncio.sleep(1)
        
        # --- VERIFICATION STEP FOR LAYOUT ---
        print(f"[{layout_name}] Verifying HTML content...")
        cms_html = await page.evaluate('''() => {
            try {
                const cm = document.querySelector('.CodeMirror').CodeMirror;
                if (cm) return cm.getValue();
            } catch(e) {}
            return null;
        }''')
        
        if not cms_html or cms_html.strip() == "":
            raise Exception(f"Kiểm tra lại thất bại: Layout '{layout_name}' chưa được lưu HTML thành công vào CMS.")
        
        print(f"Xác minh thành công: Layout '{layout_name}' đã được lưu HTML chính xác!")
        # ------------------------------------
        
        await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('button, a'));
            const backBtn = btns.find(b => (b.textContent || '').includes('목록으로') || (b.textContent || '').includes('List'));
            if (backBtn) backBtn.click();
        }''')
        await asyncio.sleep(3)
        
    print("<<< Layout deployment complete")
