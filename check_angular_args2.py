import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        await page.goto('https://demo.jiniworks.com/_fox/index.do?siteId=test-phong')
        await page.wait_for_selector('input[name="userId"]')
        await page.fill('input[name="userId"]', 'webadmin')
        await page.fill('input[name="userPassword"]', '12andvina#$')
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        await page.goto('https://demo.jiniworks.com/_fox/index.do?siteId=test-phong#!/menu')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        args = await page.evaluate('''() => {
            const service = window.angular.element(document.body).injector().get('menuService');
            return {
                update: service.update ? service.update.toString() : 'no',
                getMenuInfo: service.getMenuInfo ? service.getMenuInfo.toString() : 'no'
            };
        }''')
        print('update:', args['update'][:500])
        print('getMenuInfo:', args['getMenuInfo'][:500])
        
        await browser.close()

asyncio.run(main())
