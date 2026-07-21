import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://demo.jiniworks.com/_fox")
        await page.wait_for_selector('input[name="userId"]', timeout=10000)
        await page.fill('input[name="userId"]', 'admin')
        await page.fill('input[name="userPassword"]', '1q2w3e4r1!')
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        
        await page.goto("https://demo.jiniworks.com/_fox/index.do?siteId=test-phong#!/page")
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)
        
        await page.evaluate('''() => {
            const els = Array.from(document.querySelectorAll('.page-list *'));
            const el = els.find(x => x.innerText && x.innerText.trim() === 'i01.jsp');
            if (el) el.click();
        }''')
        await asyncio.sleep(2)
        html = await page.content()
        with open('dom_dump.html', 'w', encoding='utf-8') as f:
            f.write(html)
        await browser.close()

asyncio.run(run())
