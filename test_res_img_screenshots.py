import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    site_url = 'https://demo.jiniworks.com/_fox'
    site_id = 'test-phong'
    username = 'kookmin'
    password = 'kookmin_user'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        )
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
        
        target = f"{site_url}/index.do?siteId={site_id}#!/res-img"
        await page.goto(target)
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)
        
        await page.screenshot(path='screenshot_1_loaded.png')
        
        dom = await page.evaluate('document.body.innerHTML')
        with open('res_img_dom_final.html', 'w', encoding='utf-8') as f:
            f.write(dom)
            
        root_folder_id = f'/_res/kookmin/{site_id}/img/_anchor'
        try:
            await page.click(f'[id="{root_folder_id}"]')
            await asyncio.sleep(2)
            await page.screenshot(path='screenshot_2_clicked_root.png')
        except Exception as e:
            print("Could not click root folder:", e)
            
        try:
            await page.click(f'[id="{root_folder_id}"]', button='right')
            await asyncio.sleep(2)
            await page.screenshot(path='screenshot_3_right_clicked_root.png')
        except Exception as e:
            pass

        await browser.close()

asyncio.run(main())
