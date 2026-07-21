import asyncio
from playwright.async_api import async_playwright
import json
import os
from automation import deploy_to_cms_task

with open('data/sites.json', 'r', encoding='utf-8') as f:
    sites = json.load(f)

site = next(s for s in sites if s['id'] == 'test-phong')
menu = next(m for m in site['menus'] if m['slug'] == 'i01')

# Load files
dir_path = os.path.join('data', 'sites', 'test-phong', menu.get('folder', ''))
html_content = open(os.path.join(dir_path, 'i01.html'), 'r', encoding='utf-8').read() if os.path.exists(os.path.join(dir_path, 'i01.html')) else ''
css_content = open(os.path.join(dir_path, 'i01.css'), 'r', encoding='utf-8').read() if os.path.exists(os.path.join(dir_path, 'i01.css')) else ''
js_content = open(os.path.join(dir_path, 'i01.js'), 'r', encoding='utf-8').read() if os.path.exists(os.path.join(dir_path, 'i01.js')) else ''

print(f"Deploying i01 to {site['url']}")

asyncio.run(deploy_to_cms_task(
    site['url'],
    site['id'],
    site['username'],
    site['password'],
    menu.get('folder', ''),
    menu['slug'],
    menu.get('layout', ''),
    html_content,
    css_content,
    js_content
))
