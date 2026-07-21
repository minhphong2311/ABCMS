import asyncio
from playwright.async_api import async_playwright
import json

async def check():
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
        
        print("Clicking edit...")
        await page.evaluate('''
            var s = angular.element(document.querySelector('.page-list')).scope();
            var item = s.pg.pageList.find(i=>i.filename=='test.jsp');
            if (s.pg.listViewInterface && s.pg.listViewInterface.onClick) {
                s.pg.listViewInterface.onClick(item);
            }
        ''')
        await asyncio.sleep(1)
        await page.evaluate('''
            Array.from(document.querySelectorAll('a')).find(el => el.textContent.trim() === '편집').click();
        ''')
        await asyncio.sleep(5)
        
        html = await page.evaluate('''(() => {
            let fr = document.querySelector('.fr-view');
            return fr ? fr.innerHTML.substring(0, 500) : "no fr-view";
        })()''')
        print("CMS HTML IS:")
        print(html)
        await browser.close()

asyncio.run(check())
