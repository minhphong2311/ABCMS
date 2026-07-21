import asyncio
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
        
        # Select i04 row
        await page.evaluate(f'''async (filename) => {{
            const el = document.querySelector('.page-list');
            if (el) {{
                const s = window.angular && window.angular.element(el).scope();
                if (s && s.pg && s.pg.pageList) {{
                    const pItem = s.pg.pageList.find(item => item.filename === filename);
                    if (pItem && s.pg.listViewInterface && s.pg.listViewInterface.onClick) {{
                        s.$apply(() => {{ s.pg.listViewInterface.onClick(pItem); }});
                    }}
                }}
            }}
        }}''', 'i04.jsp')
        await asyncio.sleep(2)

        # Count visible edit buttons
        print(await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll("a, button")).filter(el => {
                const title = el.getAttribute('data-original-title') || '';
                const text = el.textContent || '';
                return title.includes('에디터편집') || title.includes('Biên tập') || text.includes('편집') || text.includes('Biên tập');
            });
            const visible = btns.filter(b => b.offsetWidth > 0 || b.offsetHeight > 0);
            return visible.length + " visible buttons found.";
        }'''))
        await browser.close()
asyncio.run(test())
