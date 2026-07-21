import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating to CMS...")
        await page.goto("https://temp.jiniworks.com/_fox")
        
        await page.fill('input[name="loginId"]', 'admin')
        await page.fill('input[name="loginPwd"]', 'temp$#@!')
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/index.do*")
        
        print("Navigating to page manager...")
        await page.goto("https://temp.jiniworks.com/_fox/index.do?siteId=phong01#!/page")
        await asyncio.sleep(5)
        
        print("Finding page 'i02.jsp' in folder 'intro'...")
        found = await page.evaluate('''async () => {
            return new Promise((resolve) => {
                const scope = angular.element(document.querySelector('.jstree')).scope();
                const pageItem = scope.pg.pageItemList.find(p => p.filename === 'i02.jsp');
                if (pageItem) {
                    scope.(() => {
                        scope.pg.listViewInterface.onDblclick(pageItem);
                    });
                    resolve(true);
                } else {
                    resolve(false);
                }
            });
        }''')
        
        if found:
            print("Opened i02 in editor. Waiting for load...")
            await asyncio.sleep(5)
            
            await page.evaluate('''async () => {
                const iframe = document.querySelector('iframe.layout-preview');
                if(iframe) {
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    const cmsContent = doc.getElementById('cms-content');
                    if(cmsContent) {
                        cmsContent.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: iframe.contentWindow }));
                    }
                }
            }''')
            await asyncio.sleep(2)
            
            await page.evaluate('''() => {
                const btns = Array.from(document.querySelectorAll('a, button'));
                const btn = btns.find(x => x.innerText && (x.innerText.includes('Bien t?p') || x.innerText.includes('ÆíÁý')));
                if(btn) btn.click();
            }''')
            await asyncio.sleep(2)
            
            filepath = await page.evaluate('''() => {
                const els = Array.from(document.querySelectorAll('*'));
                for (const el of els) {
                    const s = angular.element(el).scope();
                    if (s && s.editor) {
                        return s.editor.filepath || s.editor.contentFilepath || JSON.stringify(Object.keys(s.editor));
                    }
                }
                return "Editor not found";
            }''')
            print("Editor Info:", filepath)
        else:
            print("Page i02 not found!")
            
        await browser.close()

asyncio.run(main())
