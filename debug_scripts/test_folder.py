import asyncio
import re
from playwright.async_api import async_playwright

async def run_test():
    async with async_playwright() as p:
        # Launch browser WITH UI so you can see it and enter OTP!
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(no_viewport=True, ignore_https_errors=True)
        page = await context.new_page()

        print("Opening login page...")
        await page.goto("https://demo.jiniworks.com/_fox")
        
        print(">>> PLEASE LOGIN AND ENTER OTP ON THE BROWSER <<<")
        print("Script will wait until you successfully log in and reach the Dashboard.")
        
        # Wait until the URL changes away from the login page
        await page.wait_for_url(lambda url: "login" not in url.lower() and "/_fox" in url, timeout=120000)
        await page.wait_for_load_state('networkidle')
        print("Login successful! Going to Page Manager...")

        site_id = "test-phong03"
        folder_name = "test-ai-folder"

        target_url = f"https://demo.jiniworks.com/_fox/index.do?siteId={site_id}#!/page"
        await page.goto(target_url, wait_until='domcontentloaded')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)
        
        # Click the "Page" tab
        print("Opening Page tab...")
        await page.evaluate('''() => {
            const tabs = Array.from(document.querySelectorAll('.nav-tabs li a, uib-tab-heading, a'));
            const pageTab = tabs.find(x => (x.innerText || x.textContent || '').trim().includes('페이지') || (x.innerText || '').includes('Page'));
            if (pageTab) pageTab.click();
        }''')
        await asyncio.sleep(2)
        
        # Check if jstree-anchor is present
        await page.wait_for_selector('.jstree-anchor', timeout=15000)
        
        print(f"Checking folder '{folder_name}'...")
        folder_anchor_id = await page.evaluate(f'''(folderName) => {{
            const anchors = Array.from(document.querySelectorAll('.jstree-anchor'));
            const folderNode = anchors.find(a => (a.innerText || a.textContent || '').trim() === folderName);
            return folderNode ? folderNode.id : null;
        }}''', folder_name)
        
        if folder_anchor_id:
            print(f"Folder '{folder_name}' already exists! Clicking...")
            await page.evaluate(f'(() => {{ const el = document.getElementById("{folder_anchor_id}"); if (el) el.click(); }})()')
        else:
            print(f"Folder '{folder_name}' not found. Creating via UI...")
            
            # 1. Right click the ROOT folder
            await page.locator('.jstree-anchor').first.click(button="right", force=True)
            await asyncio.sleep(1)
            
            # 2. Click Add Folder
            await page.locator('.vakata-context a', has_text=re.compile(r'Thêm|추가|Add|createFolder', re.IGNORECASE)).first.click()
            await asyncio.sleep(1)
            
            # 3. Fill form
            inputs = page.locator('.modal-content input[type="text"]')
            await inputs.nth(0).fill(folder_name)
            await inputs.nth(1).fill(folder_name)
            
            # 4. Save
            await page.locator('.modal-content button', has_text=re.compile(r'Lưu|저장|Save|primary', re.IGNORECASE)).first.click()
            await asyncio.sleep(2)
            
            print(f"Folder '{folder_name}' created successfully!")

        print("Test complete! Keeping browser open for 15s...")
        await asyncio.sleep(15)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run_test())
