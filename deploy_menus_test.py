import asyncio
import json
from deploy_menus import run_deploy_menus

def load_data():
    with open('data/sites.json', 'r', encoding='utf-8') as f:
        return json.load(f)

if __name__ == '__main__':
    sites = load_data()
    site_id = 'test-phong'
    site = next(s for s in sites if s['id'] == site_id)
    menus = site.get('menus', [])
    
    print("Running deploy_menus for test-phong...")
    res = run_deploy_menus(
        site_url=site['url'],
        site_id=site_id,
        username=site.get('username', ''),
        password=site.get('password', ''),
        menus=menus
    )
    print("Result:", res)
