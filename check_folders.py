import asyncio, json
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://demo.jiniworks.com/_fox')
        await page.fill('input[name="userId"]', 'admin')
        await page.fill('input[name="userPassword"]', '12dosemTjsej#$')
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        await page.goto('https://demo.jiniworks.com/_fox/index.do?siteId=test-phong#!/page')
        await asyncio.sleep(4)
        print(await page.evaluate('''() => {
            const anchors = document.querySelectorAll('.jstree-anchor');
            return Array.from(anchors).map(a => a.id).join(', ');
        }'''))
        await browser.close()
asyncio.run(test())
