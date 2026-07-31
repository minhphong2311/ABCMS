# Author: sawyer88
# Email: phongnguyen@andvina.com

"""
routes/edit.py
Blueprint xử lý chức năng Edit (chỉnh sửa) menu/page trong site detail.
"""
from flask import Blueprint, request, redirect, url_for, flash, jsonify
from .helpers import load_data, save_data, parse_folder_slug

edit_bp = Blueprint('edit', __name__)


@edit_bp.route('/site/<site_id>/edit-menu/<menu_param>', methods=['POST'])
def edit_menu(site_id, menu_param):
    new_name = request.form.get('menu_name', '').strip()
    new_parent_id = request.form.get('parent_id', '').strip()
    new_slug = request.form.get('menu_slug', '').strip().strip('/')
    new_figma = request.form.get('figma_link', '').strip()
    new_layout = request.form.get('layout', 'sub-template').strip()

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)

    new_folder = ""
    if new_parent_id and site:
        parent_menu = next((m for m in site['menus'] if m['id'] == new_parent_id), None)
        if parent_menu:
            new_folder = parent_menu.get('slug', '')

    # Re-fetch site (same variable, but ensures freshness after potential migration)
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Site not found!', 'danger')
        return redirect(url_for('index'))

    old_folder, old_slug = parse_folder_slug(menu_param)
    menu = next(
        (m for m in site['menus'] if m.get('folder', '') == old_folder and m['slug'] == old_slug),
        None
    )
    if not menu:
        flash('Page not found!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    menu['name'] = new_name
    menu['slug'] = new_slug
    menu['folder'] = new_folder
    menu['figma_link'] = new_figma
    menu['layout'] = new_layout
    menu['parent_id'] = new_parent_id if new_parent_id else None

    save_data(sites)
    flash(f'Successfully updated page "{new_name}"!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))


@edit_bp.route('/site/<site_id>/update-layout/<menu_id>', methods=['POST'])
def update_layout(site_id, menu_id):
    data = request.get_json()
    new_layout = data.get('layout')

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'success': False, 'message': 'Site not found'})

    menu = next((m for m in site['menus'] if m['id'] == menu_id), None)
    if not menu:
        return jsonify({'success': False, 'message': 'Menu not found'})

    menu['layout'] = new_layout
    save_data(sites)

    return jsonify({'success': True})
