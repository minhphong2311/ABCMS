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
        await asyncio.sleep(5)
        
        # Take a screenshot of the menu manager
        await page.screenshot(path='menu_manager.png')
        print("Took menu_manager.png")
        
        # Let's inspect the HTML of the menu tree
        html = await page.content()
        with open('menu_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Wrote menu_page.html")
        
        await browser.close()

asyncio.run(main())
