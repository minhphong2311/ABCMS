# Author: sawyer88
# Email: phongnguyen@andvina.com

import asyncio
import os

async def deploy_layouts(page, site_url, site_id, progress_cb, is_cancelled=None):
    print("\n" + "="*50)
    print("5. KIỂM TRA LAYOUT")
    print("="*50)
    if progress_cb:
        progress_cb(30, "Checking and creating layouts")
    
    target_url = f"{site_url}/index.do?siteId={site_id}#!/res-layout"
    try:
        await page.goto(target_url, wait_until='domcontentloaded', timeout=15000)
    except Exception as e:
        if str(e) == 'Deploy cancelled by user': raise
        await page.evaluate('window.location.hash = "#!/res-layout";')
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(2.4)
    if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
    
    layouts_to_check = ['sub-template', 'sub-template-tab']
    base_dir = os.path.dirname(os.path.dirname(__file__))
    layout_dir = os.path.join(base_dir, 'assets', 'layout')
    
    for layout_name in layouts_to_check:
        if is_cancelled and is_cancelled():
            raise Exception("Deploy cancelled by user")
        if progress_cb:
            progress_cb(40, f"Checking layout: {layout_name}")
            
        print(f"\n  5.1 Tìm kiếm Layout theo tên: '{layout_name}'...")
        try:
            await page.goto(target_url, wait_until='domcontentloaded', timeout=15000)
        except Exception as e:
            if str(e) == 'Deploy cancelled by user': raise
            await page.evaluate('window.location.hash = "#!/res-layout";')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2.4)
        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
        
        local_html_path = os.path.join(layout_dir, f"{layout_name}.html")
        if not os.path.exists(local_html_path):
            print(f"  [Lỗi] File HTML chuẩn {local_html_path} không tồn tại, bỏ qua.")
            continue
            
        with open(local_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Thực hiện Search Layout trước để đảm bảo nó hiển thị trên trang 1
        await page.evaluate(f'''(layoutName) => {{
            const inputs = Array.from(document.querySelectorAll('input[type="text"]'));
            const searchInput = inputs.find(i => (i.placeholder || '').includes('검색') || (i.getAttribute('ng-model') || '').toLowerCase().includes('search')) || inputs[inputs.length - 1];
            if (searchInput) {{
                searchInput.value = layoutName;
                searchInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                searchInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                
                const searchBtn = Array.from(document.querySelectorAll('button, a, span')).find(b => (b.innerText || '').includes('검색'));
                if (searchBtn) searchBtn.click();
                else searchInput.dispatchEvent(new KeyboardEvent('keydown', {{'key': 'Enter'}}));
            }}
        }}''', layout_name)
        await asyncio.sleep(2.4)
        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
        
        layout_exists = await page.evaluate(f'''(layoutName) => {{
            const els = Array.from(document.querySelectorAll('a, span, div, td, h4, .card-title'));
            return els.some(el => (el.innerText || el.textContent || '').trim() === layoutName || (el.innerText || el.textContent || '').trim() === layoutName + '.jsp');
        }}''', layout_name)
        
        if layout_exists:
            print(f"  5.2 Layout '{layout_name}' đã tồn tại → Bỏ qua (không edit).")
            continue
        else:
            print(f"  5.3 Layout '{layout_name}' chưa tồn tại → Tiến hành Tạo Layout '{layout_name}'...")
            if progress_cb:
                progress_cb(45, f"Creating layout: {layout_name}")
                
            await page.evaluate('''() => {
                const addBtn = document.querySelector('[x-ng-click*="addLayout"]') || 
                               document.querySelector('[ng-click*="addLayout"]') ||
                               Array.from(document.querySelectorAll('button, a.btn')).find(b => (b.innerText || '').includes('추가'));
                if (addBtn) addBtn.click();
            }''')
            await asyncio.sleep(1.2)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            
            try:
                inputs = await page.locator('.modal-dialog input[type="text"]').all()
                if len(inputs) > 0 and await inputs[0].is_visible():
                    await inputs[0].click()
                    await inputs[0].fill("")
                    await inputs[0].press_sequentially(layout_name, delay=50)
                    await asyncio.sleep(0.6)
                    if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                
                if len(inputs) > 1 and await inputs[1].is_visible():
                    val = await inputs[1].input_value()
                    if not val:
                        await inputs[1].click()
                        await inputs[1].fill("")
                        await inputs[1].press_sequentially(layout_name, delay=50)
                await asyncio.sleep(0.6)
                if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            except Exception as e:
                if str(e) == 'Deploy cancelled by user': raise
                print(f"  Error filling form: {e}")

            await page.evaluate('''() => {
                const saveBtn = Array.from(document.querySelectorAll('.modal-footer button, .btn-primary')).find(b => (b.innerText || '').includes('저장') || (b.innerText || '').includes('Save') || (b.innerText || '').includes('확인'));
                if (saveBtn) saveBtn.click();
            }''')
            await asyncio.sleep(1.8)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            
        # Kiểm tra xem có popup lỗi "file đã tồn tại" không
            error_exists = await page.evaluate('''() => {
                const swal = document.querySelector('.sweet-alert');
                if (swal && (swal.innerText || '').includes('존재')) {
                    const btn = document.querySelector('.sweet-alert button.confirm');
                    if (btn) btn.click();
                    return true;
                }
                return false;
            }''')
            
            if error_exists:
                print(f"  [Cảnh báo] Layout '{layout_name}' đã tồn tại (phát hiện qua popup error). Bỏ qua (không edit).")
                await asyncio.sleep(0.6)
                if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                await page.evaluate('''() => {
                    const closeBtn = document.querySelector('.modal-header .close, button[ng-click*="cancel"]');
                    if (closeBtn) closeBtn.click();
                }''')
                await asyncio.sleep(0.6)
                if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
                continue
            
            await page.evaluate('''() => {
                const confirmBtn = document.querySelector('.sweet-alert button.confirm, .sweet-alert .confirm, button.confirm');
                if (confirmBtn) confirmBtn.click();
            }''')
            await asyncio.sleep(1.2)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            
            await page.evaluate('''() => {
                const closeBtn = Array.from(document.querySelectorAll('button, a')).find(b => 
                    (b.innerText || '').includes('목록으로') || 
                    (b.innerText || '').includes('닫기') ||
                    (b.innerText || '').includes('List')
                );
                if (closeBtn) closeBtn.click();
            }''')
            await asyncio.sleep(1.2)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')

        print(f"  5.4 Tìm kiếm lại Layout '{layout_name}' để tiến hành Edit...")
        await page.evaluate(f'''(layoutName) => {{
            const inputs = Array.from(document.querySelectorAll('input[type="text"]'));
            const searchInput = inputs.find(i => (i.placeholder || '').includes('검색') || (i.getAttribute('ng-model') || '').toLowerCase().includes('search')) || inputs[inputs.length - 1];
            if (searchInput) {{
                searchInput.value = layoutName;
                searchInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                searchInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                
                const searchBtn = Array.from(document.querySelectorAll('button, a, span')).find(b => (b.innerText || '').includes('검색'));
                if (searchBtn) searchBtn.click();
                else searchInput.dispatchEvent(new KeyboardEvent('keydown', {{'key': 'Enter'}}));
            }}
        }}''', layout_name)
        await asyncio.sleep(2.4)
        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
        
        print(f"  5.5 Mở màn hình Edit Layout '{layout_name}'...")
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
        await asyncio.sleep(2.4)
        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
        
        print(f"  5.6 Chuyển sang tab HTML (소스 편집)...")
        await page.evaluate('''() => {
            const headings = Array.from(document.querySelectorAll('uib-tab-heading'));
            const target = headings.find(h => h.textContent.includes('소스 편집') || h.textContent.includes('Source'));
            if (target) {
                const a = target.closest('a');
                if (a) a.click();
            }
        }''')
        await asyncio.sleep(1.8)
        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
        
        print(f"  5.7 So sánh nội dung HTML với file HTML chuẩn...")
        current_html = await page.evaluate('''() => {
            try {
                const cm = document.querySelector('.CodeMirror').CodeMirror;
                if (cm) return cm.getValue();
            } catch(e) {}
            return "";
        }''')

        if current_html.strip() != html_content.strip():
            print(f"  5.8 HTML chưa khớp → Cập nhật lại Layout '{layout_name}'...")
            try:
                success = await page.evaluate(f'''(html) => {{
                    const cm = document.querySelector('.CodeMirror').CodeMirror;
                    if (cm) {{
                        cm.setValue(html);
                        return true;
                    }}
                    return false;
                }}''', html_content)
                if success:
                    print(f"  Cập nhật HTML vào CodeMirror editor thành công.")
            except Exception as e:
                if str(e) == 'Deploy cancelled by user': raise
                print(f"  Error setting HTML: {e}")
                
            await asyncio.sleep(1.2)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            print(f"  Lưu lại thay đổi Layout...")
            await page.evaluate('''() => {
                const btn = document.querySelector('button[ng-click*="edit.save()"], button[x-ng-click*="edit.save()"]');
                if (btn) btn.click();
            }''')
            await asyncio.sleep(1.8)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
            
            await page.evaluate('''() => {
                const confirmBtn = document.querySelector('.sweet-alert button.confirm');
                if (confirmBtn) confirmBtn.click();
            }''')
            await asyncio.sleep(0.6)
            if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
        else:
            print(f"  ✓ HTML đã khớp với file chuẩn.")

        print(f"  5.9 Kiểm tra lại HTML để xác nhận đã khớp với file chuẩn...")
        cms_html = await page.evaluate('''() => {
            try {
                const cm = document.querySelector('.CodeMirror').CodeMirror;
                if (cm) return cm.getValue();
            } catch(e) {}
            return null;
        }''')
        
        if not cms_html or cms_html.strip() == "":
            raise Exception(f"Kiểm tra lại thất bại: Layout '{layout_name}' chưa được lưu HTML thành công vào CMS.")
        
        print(f"  ✓ 5.9 Kiểm tra lại THÀNH CÔNG: Layout '{layout_name}' HTML đã khớp hoàn tất!")
        
        await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('button, a'));
            const backBtn = btns.find(b => (b.textContent || '').includes('목록으로') || (b.textContent || '').includes('List'));
            if (backBtn) backBtn.click();
        }''')
        await asyncio.sleep(1.8)
        if is_cancelled and is_cancelled(): raise Exception('Deploy cancelled by user')
        
        print(f"  ✓ Đã xử lý xong Layout '{layout_name}'.")
        
    print("  ✓ Hoàn thành kiểm tra toàn bộ Layout.")

