"""
routes/preview.py
Blueprint xử lý chức năng Preview trang đã generate.
"""
import os
import time

from flask import Blueprint, render_template, make_response
from .helpers import load_data, parse_folder_slug, OUTPUT_DIR

preview_bp = Blueprint('preview', __name__)


@preview_bp.route('/preview/<site_id>/<menu_param>/')
def preview_index(site_id, menu_param):
    folder, menu_slug = parse_folder_slug(menu_param)
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    menu_name = menu_slug
    if site:
        menu = next(
            (m for m in site.get('menus', [])
             if m.get('folder', '') == folder and m['slug'] == menu_slug),
            None
        )
        if menu:
            menu_name = menu['name']
    return render_template(
        'preview_frame.html',
        site_id=site_id,
        menu_param=menu_param,
        menu_name=menu_name,
        site_name=site['name'] if site else site_id
    )


@preview_bp.route('/preview/<site_id>/<menu_param>/raw')
def preview_raw(site_id, menu_param):
    folder, menu_slug = parse_folder_slug(menu_param)

    dir_path = os.path.join(OUTPUT_DIR, site_id, folder) if folder else os.path.join(OUTPUT_DIR, site_id)
    html_path = os.path.join(dir_path, f'{menu_slug}.html')

    if not os.path.exists(html_path):
        return "File not found", 404

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Inject cache-buster for local css/js to ensure preview updates instantly
    t = int(time.time() * 1000)
    html_content = html_content.replace(
        f'href="{menu_slug}.css"',
        f'href="{menu_slug}.css?t={t}"'
    )

    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response
