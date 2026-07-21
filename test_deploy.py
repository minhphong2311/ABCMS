import asyncio
from automation import deploy_to_cms_task
import json

site_id = "test-phong"
sites = json.load(open('d:/Projects/test04/data/sites.json', encoding='utf-8'))
site = [s for s in sites if s['id'] == site_id][0]

async def main():
    res = await deploy_to_cms_task(
        site['url'], site_id, site['username'], site['password'],
        'intro', 'intro01', 'layout', '<h1>test existing page</h1>', 'body {}', 'console.log("test");'
    )
    print("Result:", res)

asyncio.run(main())
