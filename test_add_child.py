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
        
        res = await page.evaluate('''async () => {
            const s = window.angular.element(document.body).injector().get('menuService');
            try {
                const tree = await s.getTreeList('test-phong');
                const root = tree.items.find(i => i.depth === 1);
                if (!root) return 'no root found';
                const childRes = await s.addChildMenu('test-phong', root.menuCd, 'Test Child AI');
                return { success: true, rootCd: root.menuCd, childRes };
            } catch (e) {
                return { success: false, error: e.message || String(e) };
            }
        }''')
        print('Result:', res)
        await browser.close()

asyncio.run(main())
