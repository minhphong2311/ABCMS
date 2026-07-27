"""
Test script: kiểm tra full flow upload ảnh lên CMS
"""
import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    site_url = 'https://demo.jiniworks.com/_fox'
    site_id = 'test-phong'
    username = 'webadmin'
    password = '12andvina#$'
    res_org = 'kookmin'
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(base_dir, 'data', 'img', 'content', 'img-ready.png')
    print(f"Image path: {image_path}")
    print(f"Image exists: {os.path.exists(image_path)}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        print("Logging in...")
        await page.goto(site_url)
        await page.wait_for_selector('input[name="userId"]', timeout=15000)
        await page.fill('input[name="userId"]', username)
        await page.fill('input[name="userPassword"]', password)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        print("Navigating to res-img...")
        await page.goto(f"{site_url}/index.do?siteId={site_id}#!/res-img")
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)
        
        root_folder_id = f'/_res/{res_org}/{site_id}/img/_anchor'
        content_folder_id = f'/_res/{res_org}/{site_id}/img/content_anchor'
        
        print(f"Waiting for root folder: {root_folder_id}")
        try:
            await page.wait_for_selector(f'[id="{root_folder_id}"]', timeout=10000)
            print("Root folder found!")
        except Exception as e:
            print(f"Root folder NOT found: {e}")
            await page.screenshot(path='test_fail_root.png')
            await browser.close()
            return
        
        # Check if content folder exists
        content_count = await page.locator(f'[id="{content_folder_id}"]').count()
        print(f"Content folder exists: {content_count > 0}")
        
        if content_count == 0:
            print("Creating 'content' folder via right-click...")
            await page.click(f'[id="{root_folder_id}"]', button='right')
            await asyncio.sleep(1)
            await page.locator('.vakata-context li a:has(.fa-plus), .jstree-contextmenu li a:has(.fa-plus)').first.click()
            await asyncio.sleep(1)
            await page.locator('.jstree-rename-input').fill('content')
            await asyncio.sleep(0.3)
            await page.keyboard.press('Enter')
            await asyncio.sleep(3)
            print("Folder 'content' created.")
        
        # Click content folder - try ID first, fallback to text
        print("Clicking content folder...")
        try:
            await page.wait_for_selector(f'[id="{content_folder_id}"]', timeout=5000)
            await page.click(f'[id="{content_folder_id}"]')
            print("Clicked content folder by ID.")
        except Exception:
            print("ID selector failed, using text fallback...")
            await page.locator('.jstree-anchor').filter(has_text='content').last.click()
            print("Clicked content folder by text.")
        await asyncio.sleep(2)
        
        print("Clicking upload button...")
        await page.click('button[ng-click="img.upload()"]')
        await asyncio.sleep(2)
        
        await page.screenshot(path='test_modal_open.png')
        print("Screenshot saved: test_modal_open.png")
        
        print("Setting file input...")
        file_input = page.locator('input[type="file"][flow-btn]').first
        await file_input.set_input_files(image_path)
        await asyncio.sleep(2)
        
        await page.screenshot(path='test_file_selected.png')
        print("Screenshot saved: test_file_selected.png")
        
        print("Clicking upload confirm button...")
        upload_confirm = page.locator('button:has(.fa-cloud-upload), button:text("업로드")').first
        await upload_confirm.click()
        await asyncio.sleep(4)
        
        await page.screenshot(path='test_after_upload.png')
        print("Screenshot saved: test_after_upload.png")
        print("DONE!")
        
        await browser.close()

asyncio.run(main())
