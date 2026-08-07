# Author: sawyer88
# Email: phongnguyen@andvina.com

import asyncio
import sys
from playwright.async_api import async_playwright
import os
import traceback

from routes.helpers import get_config

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


import re

def replace_image_paths_for_cms(content, slug, site_id, res_org='kookmin'):
    if not content:
        return content
    cms_img_base = f'/_res/{res_org}/{site_id}/img/content'
    pattern = rf'(\./)?images/({re.escape(slug)}/)?([a-zA-Z0-9_\-\.]+\.(?:jpg|png|jpeg|gif|svg|webp))'
    return re.sub(pattern, lambda m: f'{cms_img_base}/{m.group(3)}', content, flags=re.IGNORECASE)


async def upload_page_images_to_cms(page, site_url, site_id, folder, slug):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, 'output')
    
    candidate_dirs = [
        os.path.join(output_dir, site_id, folder or '', 'images', slug),
        os.path.join(output_dir, site_id, 'images', slug),
        os.path.join(output_dir, site_id, folder or '', 'images'),
        os.path.join(output_dir, site_id, 'images')
    ]
    
    local_images = []
    for d in candidate_dirs:
        if os.path.exists(d) and os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().startswith('source_image.'):
                    continue
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
                    full_p = os.path.join(d, f)
                    if os.path.isfile(full_p) and full_p not in [x[0] for x in local_images]:
                        local_images.append((full_p, f))

    if not local_images:
        print(f'[{slug}] No local images found to upload for page {slug}.')
        return 'kookmin'

    print(f'[{slug}] Found {len(local_images)} local image(s) to upload: {[x[1] for x in local_images]}')
    
    target_res_url = f'{site_url}/index.do?siteId={site_id}#!/res-img'
    print(f'[{slug}] Navigating to image manager: {target_res_url}')
    await page.goto(target_res_url, wait_until='domcontentloaded')
    await asyncio.sleep(3)

    suffix = f"/{site_id}/img/_anchor"
    root_selector = f'[id$="{suffix}"]'
    
    try:
        await page.wait_for_selector(root_selector, timeout=10000)
        root_folder_id = await page.locator(root_selector).get_attribute('id')
    except Exception as e:
        print(f'[{slug}] Root image folder selector error: {e}')
        root_folder_id = None
        
    if root_folder_id:
        res_org = root_folder_id.split('/_res/')[1].split('/')[0]
    else:
        res_org = 'kookmin'
    print(f'[{slug}] Detected res_org: {res_org}')

    root_folder_id = f'/_res/{res_org}/{site_id}/img/_anchor'
    content_folder_id = f'/_res/{res_org}/{site_id}/img/content_anchor'

    content_exists = await page.locator(f'[id="{content_folder_id}"]').count() > 0
    if not content_exists:
        print(f'[{slug}] Folder "content" does not exist. Creating folder "content"...')
        await page.evaluate(f'''() => {{
            try {{
                const injector = window.angular.element(document.body).injector();
                const svc = injector.has('resImgService') ? injector.get('resImgService') : 
                           (injector.has('fileService') ? injector.get('fileService') : null);
                if (svc && svc.addFolder) {{
                    svc.addFolder("{site_id}", "/_res/{res_org}/{site_id}/img/", "content");
                }}
            }} catch(e) {{ console.error(e); }}
        }}''')
        await asyncio.sleep(2)
        await page.reload(wait_until='domcontentloaded')
        await asyncio.sleep(2)

    print(f'[{slug}] Opening folder "content"...')
    try:
        await page.wait_for_selector(f'[id="{content_folder_id}"]', timeout=5000)
        await page.click(f'[id="{content_folder_id}"]')
    except Exception:
        await page.evaluate(f'''() => {{
            const el = document.getElementById("{content_folder_id}");
            if (el) el.click();
        }}''')
    await asyncio.sleep(2)

    missing_images = []
    for img_path, img_name in local_images:
        img_exists = await page.evaluate(f'''(fname) => {{
            return document.body.innerText.includes(fname);
        }}''', img_name)

        if img_exists:
            print(f'[{slug}] Image "{img_name}" already exists on CMS.')
        else:
            missing_images.append((img_path, img_name))

    if missing_images:
        print(f'[{slug}] Found {len(missing_images)} missing image(s) to upload: {[x[1] for x in missing_images]}')
        # Try batch upload with new selectors, if input supports multiple
        try:
            await page.click('button[ng-click="img.upload()"]')
            await asyncio.sleep(1.2)
            
            missing_paths = [x[0] for x in missing_images]
            file_input = page.locator('input[type="file"][flow-btn]').first
            
            # This might fail if the input doesn't support multiple files
            await file_input.set_input_files(missing_paths)
            print(f'[{slug}] Set {len(missing_paths)} image file(s) into file input.')
            await asyncio.sleep(1.2)
            
            upload_confirm = page.locator('button:has(.fa-cloud-upload), button:has-text("업로드")').first
            await upload_confirm.click()
            print(f'[{slug}] Clicked start upload for missing images. Waiting for upload...')
            await asyncio.sleep(5)
        except Exception as e:
            print(f'[{slug}] Batch upload error (might not support multiple): {e}')

        # Fallback individual retry if any file is still missing
        for img_path, img_name in missing_images:
            img_exists = await page.evaluate(f'''(fname) => {{
                return document.body.innerText.includes(fname);
            }}''', img_name)
            if not img_exists:
                print(f'[{slug}] Retry uploading single image "{img_name}"...')
                try:
                    await page.click('button[ng-click="img.upload()"]')
                    await asyncio.sleep(1.2)
                    
                    file_input = page.locator('input[type="file"][flow-btn]').first
                    await file_input.set_input_files(img_path)
                    await asyncio.sleep(1.2)
                    
                    upload_confirm = page.locator('button:has(.fa-cloud-upload), button:has-text("업로드")').first
                    await upload_confirm.click()
                    await asyncio.sleep(2.4)
                except Exception as single_err:
                    print(f'[{slug}] Error uploading {img_name}: {single_err}')

    return res_org


async def deploy_to_cms_task(site_url, site_id, username, password, folder, slug, layout, html_content, css_content, js_content):
    config = get_config()
    show_ui = bool(config.get('show_ui', True))
    headless_mode = not show_ui

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless_mode, slow_mo=200)
        context = await browser.new_context(no_viewport=True, ignore_https_errors=True)
        page = await context.new_page()
        page.on('dialog', lambda dialog: asyncio.create_task(dialog.accept()))

        try:
            # STEP 1: LOGIN
            print(f'[{slug}] Logging in to CMS: {site_url}')
            await page.goto(site_url)
            await page.wait_for_selector('input[name="userId"]', timeout=15000)
            await page.fill('input[name="userId"]', username)
            await page.fill('input[name="userPassword"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)

            # Verify login succeeded
            current_url = page.url
            if 'login' in current_url.lower():
                body = await page.evaluate('document.body.innerText')
                raise Exception(f'Login failed! Still on login page: {current_url}. Body snippet: {body[:200]}')

            # STEP 1.5: UPLOAD IMAGES TO CMS & UPDATE PATHS
            print(f'[{slug}] Checking and uploading local images to CMS...')
            res_org = await upload_page_images_to_cms(page, site_url, site_id, folder, slug)
            html_content = replace_image_paths_for_cms(html_content, slug, site_id, res_org)
            css_content = replace_image_paths_for_cms(css_content, slug, site_id, res_org)

            # STEP 2: NAVIGATE TO PAGE MANAGER
            target_url = f'{site_url}/index.do?siteId={site_id}#!/page'
            print(f'[{slug}] Navigating to: {target_url}')
            try:
                await page.goto(target_url, wait_until='domcontentloaded', timeout=15000)
            except Exception:
                await page.evaluate('window.location.hash = \"!/page\";')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            try:
                await page.wait_for_function('() => !!document.querySelector(\".jstree-anchor\")', timeout=30000)
            except Exception as e:
                print(f'[{slug}] Folder tree not found! URL: {page.url}')
                raise e

            # Click "페이지" tab to ensure page list is active
            print(f'[{slug}] Selecting "페이지" (Page) tab...')
            await page.evaluate('''() => {
                const tabs = Array.from(document.querySelectorAll('.nav-tabs li a, uib-tab-heading, a'));
                const pageTab = tabs.find(x => (x.innerText || x.textContent || '').trim().includes('페이지'));
                if (pageTab) pageTab.click();
            }''')
            await asyncio.sleep(2)

            # STEP 3: SELECT FOLDER
            if folder:
                folder_anchor_id = f'/{site_id}/{folder}_anchor'
                print(f'[{slug}] Selecting folder: {folder}')
                try:
                    # Wait up to 8 seconds for the folder anchor to render in the DOM
                    await page.wait_for_selector(f'[id=\"{folder_anchor_id}\"]', timeout=8000)
                    folder_el = True
                except Exception:
                    folder_el = False

                if not folder_el:
                    print(f'[{slug}] Folder not found in tree. Creating folder...')
                    await page.evaluate(f'window.angular.element(document.body).injector().get(\"pageService\").addFolder(\"{site_id}\", \"/{site_id}\", \"{folder}\")')
                    await asyncio.sleep(3)
                    print(f'[{slug}] Reloading page to sync tree...')
                    await page.reload(wait_until='domcontentloaded')
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_function('() => !!document.querySelector(\".jstree-anchor\")', timeout=20000)
                    
                    # Re-select "페이지" tab
                    await page.evaluate('''() => {
                        const tabs = Array.from(document.querySelectorAll('.nav-tabs li a, uib-tab-heading, a'));
                        const pageTab = tabs.find(x => (x.innerText || x.textContent || '').trim().includes('페이지'));
                        if (pageTab) pageTab.click();
                    }''')
                    await asyncio.sleep(2)
                    await page.wait_for_selector(f'[id=\"{folder_anchor_id}\"]', timeout=10000)

                await page.evaluate(f'(() => {{ const el = document.getElementById(\"{folder_anchor_id}\"); if (el) el.click(); }})()')
                await asyncio.sleep(2)

            # STEP 4: CHECK PAGE EXISTS
            print(f'[{slug}] Checking if {slug}.jsp exists...')
            page_exists = await page.evaluate(f'''() => {{
                return new Promise((resolve) => {{
                    let n = 0;
                    const check = () => {{
                        n++;
                        const els = Array.from(document.querySelectorAll('.page-list, [ng-controller]'));
                        for (const el of els) {{
                            const s = window.angular && window.angular.element(el).scope();
                            if (s) {{
                                const list = s.list || (s.pg && s.pg.list) || (s.pg && s.pg.pageList);
                                if (list && list.length > 0) {{
                                    return resolve(!!list.find(i => i && i.filename === '{slug}.jsp'));
                                }}
                            }}
                        }}
                        if (n > 60) return resolve(false);
                        setTimeout(check, 100);
                    }};
                    check();
                }});
            }}''')
            print(f'[{slug}] page_exists={page_exists}')

            editor_page = None

            if page_exists:
                # PAGE EXISTS: select page by physically clicking the card and then click the "Biên tập" button on the toolbar
                print(f'[{slug}] Page exists. Selecting page card in DOM...')
                card_click_res = await page.evaluate(f'''(slug) => {{
                    const cardEl = Array.from(document.querySelectorAll('*')).find(el => {{
                        const s = window.angular && window.angular.element(el).scope();
                        return s && s.item && s.item.filename === slug + '.jsp';
                    }});
                    if (cardEl) {{
                        cardEl.click();
                        return 'clicked card';
                    }}
                    return 'card not found';
                }}''', slug)
                print(f'[{slug}] Card click result: {card_click_res}')
                await asyncio.sleep(1.5)

                print(f'[{slug}] Clicking the "Biên tập" (Edit) button on the toolbar...')
                new_pages = []
                def on_page(p):
                    new_pages.append(p)
                context.on('page', on_page)

                await page.evaluate('''() => {
                    const anchors = Array.from(document.querySelectorAll("a, button"));
                    const editBtn = anchors.find(a => 
                        (a.getAttribute('data-original-title') || '').includes('Biên tập') || 
                        (a.getAttribute('data-original-title') || '').includes('에디터') || 
                        a.textContent.includes('Biên tập') ||
                        a.textContent.includes('에디터')
                    );
                    if (editBtn) editBtn.click();
                }''')

                # Wait up to 3 seconds for a new page to open
                for _ in range(30):
                    if new_pages:
                        break
                    await asyncio.sleep(0.1)

                if new_pages:
                    editor_page = new_pages[0]
                    print(f'[{slug}] Editor tab (new page): {editor_page.url}')
                else:
                    editor_page = page
                    print(f'[{slug}] Editor (same tab): {editor_page.url}')

                try:
                    context.remove_listener('page', on_page)
                except Exception:
                    pass
            else:
                # PAGE NOT EXISTS: create page, click save+edit -> same tab editor
                print(f'[{slug}] Creating new page...')
                await page.evaluate('''() => {
                    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && (b.innerText.includes('페이지 등록') || b.innerText.includes('Thêm')));
                    if (btn) btn.click();
                }''')
                await page.wait_for_selector('.modal-dialog, .modal-content', timeout=10000)
                await asyncio.sleep(2)

                # Fill form: Title and Filename
                await page.evaluate(f'''(slug) => {{
                    const set = (sel, val) => {{
                        const el = document.querySelector(sel);
                        if (!el) return;
                        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                        setter.call(el, val);
                        el.dispatchEvent(new Event('input', {{bubbles:true}}));
                        el.dispatchEvent(new Event('change', {{bubbles:true}}));
                    }};
                    set('input[name="title"]', slug);
                    set('input[name="filename"]', slug);
                    set('input[ng-model="pg.data.filename"]', slug);
                }}''', slug)
                await asyncio.sleep(1)

                # Select HTML Header and Layout template
                await page.evaluate(f'''() => {{
                    const headEl = document.querySelector('[name="headTemplate"]');
                    if (headEl) {{
                        const s = window.angular.element(headEl).scope();
                        const item = s.pg.headTemplateList.find(t => t.filename === 'common.jsp' && t.siteId === '{site_id}') || s.pg.headTemplateList.find(t => t.filename === 'common.jsp');
                        if (item) window.angular.element(headEl).controller('uiSelect').select(item);
                    }}
                    const layoutEl = document.querySelector('[name="layoutTemplate"]');
                    if (layoutEl) {{
                        const s = window.angular.element(layoutEl).scope();
                        const item = s.pg.layoutTemplateList.find(t => t.filename === '{layout}.jsp' && t.siteId === '{site_id}') || s.pg.layoutTemplateList.find(t => t.filename === '{layout}.jsp');
                        if (item) window.angular.element(layoutEl).controller('uiSelect').select(item);
                    }}
                }}''')
                await asyncio.sleep(1)

                # Force ng-if conditions on ALL scopes containing pg
                print(f'[{slug}] Forcing STATIC + hasMainContent on all pg scopes...')
                await page.evaluate('''() => {
                    // Try every angular element's scope
                    Array.from(document.querySelectorAll('[ng-controller], .modal, .modal-content, .modal-dialog, form')).forEach(el => {
                        try {
                            const s = window.angular && window.angular.element(el).scope();
                            if (s && s.pg) {
                                s.pg.hasMainContent = true;
                                if (!s.pg.data) s.pg.data = {};
                                s.pg.data.pageKind = 'STATIC';
                                s.$apply();
                            }
                        } catch(e) {}
                    });

                    // Also try $rootScope broadcast
                    try {
                        const rs = window.angular.element(document.body).scope().$root;
                        if (rs && rs.pg) {
                            rs.pg.hasMainContent = true;
                            if (!rs.pg.data) rs.pg.data = {};
                            rs.pg.data.pageKind = 'STATIC';
                            rs.$apply();
                        }
                    } catch(e) {}
                }''')
                await asyncio.sleep(1)

                # Use try/except to wait for button and click it
                try:
                    await page.wait_for_function(
                        '''() => !!document.querySelector('button[ng-click*="content-edit"]') || Array.from(document.querySelectorAll('button')).some(b=>b.innerText&&b.innerText.includes("저장 후 편집"))''',
                        timeout=8000
                    )
                    print(f'[{slug}] Button appeared! Clicking...')
                    clicked = await page.evaluate('''() => {
                        // Try by ng-click
                        let btn = document.querySelector('button[ng-click*="content-edit"]');
                        if (!btn) btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes("저장 후 편집"));
                        if (btn) { btn.click(); return 'clicked: ' + btn.getAttribute('ng-click'); }
                        return 'not found';
                    }''')
                    print(f'[{slug}] Click result: {clicked}')
                except Exception as e:
                    print(f'[{slug}] Button never appeared ({e}). Calling pg.save() directly...')
                    await page.evaluate('''() => {
                        // Search all scopes for pg.save
                        const els = Array.from(document.querySelectorAll('[ng-controller], .modal, form'));
                        for (const el of els) {
                            try {
                                const s = window.angular && window.angular.element(el).scope();
                                if (s && s.pg && typeof s.pg.save === 'function') {
                                    s.pg.saveMode = 'content-edit';
                                    s.$apply();
                                    s.pg.save();
                                    return 'called pg.save()';
                                }
                            } catch(e) {}
                        }
                        return 'pg.save not found';
                    }''')

                # Editor opens in SAME TAB after save - wait for modal to close
                print(f'[{slug}] Waiting for modal to close and editor to load...')
                try:
                    await page.wait_for_function(
                        """() => !document.querySelector('.modal-backdrop') && !document.querySelector('.modal.in, .modal.show')""",
                        timeout=15000
                    )
                except Exception:
                    pass
                await asyncio.sleep(1)

                # The editor is in the same tab
                editor_page = page
                print(f'[{slug}] Editor should be in same tab: {page.url}')

            if editor_page is None:
                raise Exception('Could not open editor tab!')

            # STEP 6: WAIT FOR EDITOR
            print(f'[{slug}] Editor tab URL: {editor_page.url}')
            try:
                await editor_page.wait_for_load_state('domcontentloaded', timeout=15000)
            except Exception:
                pass
            await editor_page.wait_for_function(f'''() => {{
                try {{
                    return Array.from(document.querySelectorAll('*')).some(el => {{
                        const s = window.angular && window.angular.element(el).scope();
                        return s && s.editor && s.editor.item && s.editor.item.filename === '{slug}.jsp';
                    }});
                }} catch(e) {{ return false; }}
            }}''', timeout=25000)
            print(f'[{slug}] Editor ready!')

            # STEP 7: HTML
            print(f'[{slug}] Injecting HTML...')
            try:
                await editor_page.wait_for_selector('.fr-command[data-cmd=\"html\"]', timeout=15000)
                await editor_page.locator('.fr-command[data-cmd=\"html\"]').first.click(force=True)
                await asyncio.sleep(1)
                await editor_page.evaluate('''(html) => {
                    const cm = document.querySelector('.fr-box .CodeMirror') || document.querySelector('.tab-pane.active .CodeMirror');
                    if (cm && cm.CodeMirror) { cm.CodeMirror.setValue(html); return; }
                    const ta = document.querySelector('textarea.fr-code');
                    if (ta) { ta.value = html; ta.dispatchEvent(new Event('input',{bubbles:true})); }
                }''', html_content)
                await asyncio.sleep(1)
                # Also set via Angular scope
                await editor_page.evaluate('''(html) => {
                    Array.from(document.querySelectorAll('*')).some(el => {
                        const s = window.angular && window.angular.element(el).scope();
                        if (s && s.editor && s.editor.item) { s.$apply(() => { s.editor.item.contentText = html; }); return true; }
                    });
                }''', html_content)
                await editor_page.locator('.fr-command[data-cmd=\"html\"]').first.click(force=True)
                await asyncio.sleep(1)
            except Exception as e:
                print(f'[{slug}] HTML inject error: {e}')

            # STEP 8: CSS
            print(f'[{slug}] Switching to CSS tab...')
            await editor_page.evaluate('''() => {
                const t = Array.from(document.querySelectorAll('.nav-tabs li a, uib-tab-heading')).find(x => (x.innerText||x.textContent||'').trim() === 'CSS 편집');
                if (t) t.click();
            }''')
            await asyncio.sleep(1)
            await editor_page.evaluate('''(css) => {
                const cmEl = document.querySelector('[ui-codemirror="editor.codeMirrorCssOpt"] .CodeMirror');
                if (cmEl && cmEl.CodeMirror) { cmEl.CodeMirror.setValue(css); }
                Array.from(document.querySelectorAll('*')).some(el => {
                    const s = window.angular && window.angular.element(el).scope();
                    if (s && s.editor && s.editor.item) {
                        s.$apply(() => {
                            s.editor.item.cssText = css;
                            if (s.editor.cssTabList && s.editor.cssTabList[0]) {
                                s.editor.cssTabList[0].text = css;
                                s.editor.cssTabList[0].modified = true;
                            }
                        });
                        return true;
                    }
                });
            }''', css_content)
            await asyncio.sleep(1)

            # STEP 9: JS
            print(f'[{slug}] Switching to JS tab...')
            await editor_page.evaluate('''() => {
                const t = Array.from(document.querySelectorAll('.nav-tabs li a, uib-tab-heading')).find(x => (x.innerText||x.textContent||'').trim() === 'JS 편집');
                if (t) t.click();
            }''')
            await asyncio.sleep(1)
            await editor_page.evaluate('''(js) => {
                const cmEl = document.querySelector('[ui-codemirror="editor.codeMirrorJsOpt"] .CodeMirror');
                if (cmEl && cmEl.CodeMirror) { cmEl.CodeMirror.setValue(js); }
                Array.from(document.querySelectorAll('*')).some(el => {
                    const s = window.angular && window.angular.element(el).scope();
                    if (s && s.editor && s.editor.item) {
                        s.$apply(() => {
                            s.editor.item.jsText = js;
                            if (s.editor.jsTabList && s.editor.jsTabList[0]) {
                                s.editor.jsTabList[0].text = js;
                                s.editor.jsTabList[0].modified = true;
                            }
                        });
                        return true;
                    }
                });
            }''', js_content)
            await asyncio.sleep(1)

            # STEP 10: SAVE
            print(f'[{slug}] Saving...')
            await editor_page.evaluate('''() => {
                const btn = Array.from(document.querySelectorAll('button,a')).find(b => b.innerText && b.innerText.trim() === '저장' && b.offsetParent);
                if (btn) { btn.click(); return; }
                Array.from(document.querySelectorAll('*')).some(el => {
                    const s = window.angular && window.angular.element(el).scope();
                    if (s && s.editor && typeof s.editor.save === 'function') { s.editor.save(); return true; }
                });
            }''')
            await asyncio.sleep(8)

            print(f'[{slug}] Deploy completed!')
            return {'success': True, 'message': 'Deploy thanh cong!'}

        except Exception as e:
            print(f'[{slug}] ERROR: {e}')
            traceback.print_exc()
            print(f'[{slug}] Keeping browser open 60s...')
            await asyncio.sleep(60)
            return {'success': False, 'message': f'Loi deploy: {str(e)}'}


def run_deploy(site_url, site_id, username, password, folder, slug, layout, html_content, css_content, js_content):
    return asyncio.run(deploy_to_cms_task(site_url, site_id, username, password, folder, slug, layout, html_content, css_content, js_content))
