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
        
        # Select i04 row like the real script
        await page.evaluate(f'''async (filename) => {{
            const el = document.querySelector('.page-list');
            if (el) {{
                const s = angular.element(el).scope();
                if (s && s.pg && s.pg.pageList) {{
                    const pItem = s.pg.pageList.find(item => item.filename === filename);
                    if (pItem && s.pg.listViewInterface && s.pg.listViewInterface.onClick) {{
                        s.$apply(() => {{ s.pg.listViewInterface.onClick(pItem); }});
                    }}
                }}
            }}
        }}''', 'i04.jsp')
        await asyncio.sleep(1)

        # Print all edit buttons in the whole document
        print(await page.evaluate('''() => {
            const anchors = Array.from(document.querySelectorAll("a, button"));
            const editBtns = anchors.filter(a => 
                (a.getAttribute('data-original-title') || '').includes('에디터편집') || 
                (a.getAttribute('data-original-title') || '').includes('Biên tập') || 
                a.textContent.includes('편집') || 
                a.textContent.includes('Biên tập')
            );
            return editBtns.map(a => a.outerHTML);
        }'''))
        await browser.close()
asyncio.run(test())
