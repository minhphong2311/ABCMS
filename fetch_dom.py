import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        print('Logging in...')
        await page.goto('https://demo.jiniworks.com/_fox/index.do?siteId=test-phong')
        await page.wait_for_selector('input[name="userId"]')
        await page.fill('input[name="userId"]', 'webadmin')
        await page.fill('input[name="userPassword"]', '12andvina#$')
        await page.click('button[type="submit"]')
        
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        print('Navigating to menu...')
        await page.goto('https://demo.jiniworks.com/_fox/index.do?siteId=test-phong#!/menu')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)
        
        html = await page.content()
        with open('menu_dom.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Saved DOM to menu_dom.html')
        await browser.close()

asyncio.run(main())
