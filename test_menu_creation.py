import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        # Intercept network requests
        def on_request(request):
            if 'addMenu' in request.url or 'updateMenuInfo' in request.url:
                print(f'REQ: {request.url}')
                print(f'METHOD: {request.method}')
                print(f'POST DATA: {request.post_data}')
                
        page.on('request', on_request)
        
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
        await asyncio.sleep(3)
        
        print('Creating a test menu...')
        # Execute menuService.addMenu
        await page.evaluate('''() => {
            const service = window.angular.element(document.body).injector().get('menuService');
            service.addMenu('test-phong', 'Test AI Menu');
        }''')
        
        await asyncio.sleep(3)
        
        # Let's get the list of menus to find the one we just created
        menus = await page.evaluate('''() => {
            const service = window.angular.element(document.body).injector().get('menuService');
            return service.getTreeList('test-phong');
        }''')
        print(f"Menus: {menus}")
        
        await browser.close()

asyncio.run(main())
