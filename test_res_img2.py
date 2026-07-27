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
        
        # Wait for navigation to dashboard
        try:
            await page.wait_for_selector('.navbar', timeout=10000)
        except:
            pass
        await asyncio.sleep(2)
        
        target_url = f'{site_url}/index.do?siteId={site_id}#!/res-img'
        await page.goto(target_url)
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)
        
        # Click the root folder
        root_folder_id = f'/_res/kookmin/{site_id}/img/_anchor'
        try:
            await page.click(f'[id="{root_folder_id}"]', timeout=5000)
            await asyncio.sleep(2)
            await page.screenshot(path='res_img_clicked.png')
        except Exception as e:
            print("Failed to click root folder:", e)
        
        # Right click the root folder
        try:
            await page.click(f'[id="{root_folder_id}"]', button='right', timeout=5000)
            await asyncio.sleep(2)
            await page.screenshot(path='res_img_right_clicked.png')
        except Exception as e:
            print("Failed to right click root folder:", e)
        
        dom = await page.evaluate('document.body.innerHTML')
        with open('res_img_dom_logged_in2.html', 'w', encoding='utf-8') as f:
            f.write(dom)
            
        await browser.close()

asyncio.run(main())
