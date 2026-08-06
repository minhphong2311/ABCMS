# Author: sawyer88
# Email: phongnguyen@andvina.com

"""
routes/preview.py
Blueprint xử lý chức năng Preview trang đã generate.
"""
import os
import time

from flask import Blueprint, render_template, make_response, send_from_directory
from .helpers import load_data, parse_folder_slug, OUTPUT_DIR

preview_bp = Blueprint('preview', __name__)

def render_preview_index(site_id, folder, menu_slug):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    menu_name = menu_slug
    figma_link = ''
    image_path = ''
    
    if site:
        menu = next(
            (m for m in site.get('menus', [])
             if m.get('folder', '') == folder and m['slug'] == menu_slug),
            None
        )
        if menu:
            menu_name = menu['name']
            figma_link = menu.get('figma_link', '')
            image_path = menu.get('image_path', '')
            
    return render_template(
        'preview_frame.html',
        site_id=site_id,
        menu_param=f"{folder}--{menu_slug}",
        folder=folder,
        menu_slug=menu_slug,
        menu_name=menu_name,
        site_name=site['name'] if site else site_id,
        figma_link=figma_link,
        image_path=image_path
    )


@preview_bp.route('/preview/<site_id>/<folder>/<slug>.do')
def preview_index(site_id, folder, slug):
    return render_preview_index(site_id, folder, slug)


@preview_bp.route('/preview/<site_id>/<slug>.do')
def preview_index_no_folder(site_id, slug):
    return render_preview_index(site_id, slug, slug)


@preview_bp.route('/preview/raw/<site_id>/<folder>/<slug>.html')
def preview_raw(site_id, folder, slug):
    dir_path = os.path.join(OUTPUT_DIR, site_id, folder)
    html_path = os.path.join(dir_path, f'{slug}.html')

    if not os.path.exists(html_path):
        return "File not found", 404

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    t = int(time.time() * 1000)
    html_content = html_content.replace(
        f'href="{slug}.css"',
        f'href="{slug}.css?t={t}"'
    )

    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@preview_bp.route('/preview/raw/<site_id>/<slug>.html')
def preview_raw_no_folder(site_id, slug):
    return preview_raw(site_id, slug, slug)


@preview_bp.route('/preview/raw/<site_id>/<folder>/<path:filename>')
def preview_asset_folder(site_id, folder, filename):
    dir_path = os.path.join(OUTPUT_DIR, site_id, folder)
    file_path = os.path.join(dir_path, filename)
    if os.path.exists(file_path):
        return send_from_directory(dir_path, filename)
    
    site_root = os.path.join(OUTPUT_DIR, site_id)
    return send_from_directory(site_root, filename)


@preview_bp.route('/preview/raw/<site_id>/<path:filename>')
def preview_asset_no_folder(site_id, filename):
    site_root = os.path.join(OUTPUT_DIR, site_id)
    return send_from_directory(site_root, filename)
