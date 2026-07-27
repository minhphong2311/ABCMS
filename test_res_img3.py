import asyncio
from playwright.async_api import async_playwright

async def main():
    site_url = 'https://demo.jiniworks.com/_fox'
    site_id = 'test-phong'
    username = 'kookmin'
    password = 'kookmin_user'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        await page.goto(site_url)
        await asyncio.sleep(2)
        await page.fill('input[name="userId"]', username)
        await page.fill('input[name="userPassword"]', password)
        await page.click('button[type="submit"]')
        
        try:
            await page.wait_for_selector('.navbar', timeout=15000)
        except:
            pass
        await asyncio.sleep(2)
        
        # Navigate using JS to bypass hash issues
        target = f"{site_url}/index.do?siteId={site_id}#!/res-img"
        await page.evaluate(f"window.location.href = '{target}';")
        await asyncio.sleep(2)
        await page.reload()
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)
        
        # wait for jstree to load
        try:
            await page.wait_for_selector('.jstree-anchor', timeout=15000)
            print('Found jstree-anchor!')
        except Exception as e:
            print('Failed to find jstree-anchor:', e)
            
        dom = await page.evaluate('document.body.innerHTML')
        with open('res_img_dom3.html', 'w', encoding='utf-8') as f:
            f.write(dom)
            
        await browser.close()

asyncio.run(main())
