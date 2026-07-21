import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating to CMS...")
        await page.goto('https://demo.jiniworks.com/_fox/index.do?siteId=test-phong#!/page')
        await page.wait_for_selector('input[name="userId"]')
        await page.fill('input[name="userId"]', 'admin')
        await page.fill('input[name="userPassword"]', '12dosemTjsej#$')
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        await page.evaluate("window.location.hash='!/page'")
        await asyncio.sleep(2)
        
        print("Clicking news...")
        await page.evaluate("document.getElementById('/test-phong/news_anchor').click()")
        await asyncio.sleep(2)
        
        print("Clicking test.jsp...")
        await page.evaluate('''
            var s = angular.element(document.querySelector('.page-list')).scope();
            var item = s.pg.pageList.find(i=>i.filename=='test.jsp');
            s.pg.listViewInterface.onClick(item);
        ''')
        await asyncio.sleep(1)
        
        print("Clicking edit...")
        await page.evaluate('''
            Array.from(document.querySelectorAll('a')).find(el => el.textContent.trim() === '편집').click();
        ''')
        await asyncio.sleep(5)
        
        print("Checking s.editor...")
        res = await page.evaluate('''(() => {
            let log = [];
            try {
                let els = Array.from(document.querySelectorAll('*'));
                for(let el of els) {
                    let s = window.angular && window.angular.element(el).scope();
                    if(s && s.editor) {
                        log.push("s.editor exists!");
                        log.push("setCodeValue type: " + typeof s.editor.setCodeValue);
                        log.push("item contentText: " + (s.editor.item.contentText ? s.editor.item.contentText.substring(0,50) : "empty"));
                        if(s.editor.cssTabList) log.push("cssTabList exists");
                        
                        // Let's also check Froala methods
                        let froala = document.querySelector('.fr-view');
                        if (froala) log.push("froala .fr-view exists!");
                        
                        let textarea = document.querySelector('.fr-code');
                        if (textarea) log.push(".fr-code textarea exists!");
                        break;
                    }
                }
            } catch(e) { log.push(e.message); }
            return log;
        })()''')
        print('Result:', res)
        await browser.close()

asyncio.run(test())
