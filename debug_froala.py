import asyncio
from playwright.async_api import async_playwright

async def debug_froala():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://demo.jiniworks.com/_fox/index.do?siteId=test-phong#!/page')
        await page.wait_for_selector('input[name="userId"]')
        await page.fill('input[name="userId"]', 'admin')
        await page.fill('input[name="userPassword"]', '12dosemTjsej#$')
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        await page.evaluate("window.location.hash='!/page'")
        await asyncio.sleep(2)
        
        await page.evaluate("document.getElementById('/test-phong/news_anchor').click()")
        await asyncio.sleep(2)
        
        await page.evaluate('''
            var s = angular.element(document.querySelector('.page-list')).scope();
            var item = s.pg.pageList.find(i=>i.filename=='test.jsp');
            s.pg.listViewInterface.onClick(item);
        ''')
        await asyncio.sleep(1)
        await page.evaluate('''
            Array.from(document.querySelectorAll('a')).find(el => el.textContent.trim() === '편집').click();
        ''')
        await asyncio.sleep(5)
        
        res = await page.evaluate('''(() => {
            let log = [];
            
            // Try Froala v2 API
            try {
                if (window.$) {
                    let $el = $('textarea[froala]');
                    if ($el.length) {
                        $el.froalaEditor('html.set', 'FROALA API TEST V2');
                        log.push("Froala API v2 (textarea): OK");
                    }
                    let $el2 = $('.fr-view');
                    if ($el2.length) {
                        $el2.froalaEditor('html.set', 'FROALA API TEST V2');
                        log.push("Froala API v2 (fr-view): OK");
                    }
                }
            } catch(e) { log.push("V2_ERR:" + e.message); }
            
            // Try Froala v3 API
            try {
                let editor = document.querySelector('.fr-view').__froala_editor;
                if (editor) {
                    editor.html.set('FROALA API TEST V3');
                    log.push("Froala API v3: OK");
                }
            } catch(e) { log.push("V3_ERR:" + e.message); }
            
            return log.join(" | ");
        })()''')
        print("DEBUG RESULT:", res)
        await browser.close()

asyncio.run(debug_froala())
