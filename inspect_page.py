import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Logging in...")
        await page.goto("https://demo.jiniworks.com/_fox")
        await page.wait_for_selector('input[name="userId"]', timeout=10000)
        await page.fill('input[name="userId"]', 'webadmin')
        await page.fill('input[name="userPassword"]', '1q2w3e4r1!')
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        
        print("Navigating to test-phong pages...")
        await page.goto("https://demo.jiniworks.com/_fox/index.do?siteId=test-phong#!/page")
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)
        
        print("Extracting first pageItem properties...")
        item_keys = await page.evaluate('''() => {
            const el = document.querySelector('.page-list') || document.querySelector('.jstree');
            const scope = window.angular.element(el).scope();
            if (scope && scope.pg && scope.pg.pageList && scope.pg.pageList.length > 0) {
                return JSON.stringify(scope.pg.pageList[0]);
            }
            if (scope && scope.pg && scope.pg.pageItemList && scope.pg.pageItemList.length > 0) {
                return JSON.stringify(scope.pg.pageItemList[0]);
            }
            return "Found scope pg but no pageList: " + Object.keys(scope.pg || {}).join(", ");
        }''')
        
        print("Item:", item_keys)
        await browser.close()

asyncio.run(main())
