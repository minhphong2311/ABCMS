# Author: sawyer88
# Email: phongnguyen@andvina.com

"""
routes/delete.py
Blueprint xử lý chức năng Delete (xóa) menu/page trong site detail.
"""
from flask import Blueprint, request, redirect, url_for, flash, jsonify
from .helpers import load_data, save_data, parse_folder_slug, delete_menu_files

delete_bp = Blueprint('delete', __name__)


@delete_bp.route('/site/<site_id>/delete-menu/<menu_param>', methods=['POST'])
def delete_menu(site_id, menu_param):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Site not found!', 'danger')
        return redirect(url_for('index'))

    folder, menu_slug = parse_folder_slug(menu_param)
    site['menus'] = [
        m for m in site['menus']
        if not (m.get('folder', '') == folder and m['slug'] == menu_slug)
    ]
    save_data(sites)

    # Delete generated temp files
    delete_menu_files(site_id, menu_param)
    flash('Successfully deleted page!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))


@delete_bp.route('/site/<site_id>/bulk-delete-menus', methods=['POST'])
def bulk_delete_menus(site_id):
    data = request.get_json()
    items = data.get('items', [])

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'success': False, 'message': 'Site not found'})

    deleted_count = 0
    for item in items:
        menu_id = item.get('id')
        param = item.get('param')

        original_length = len(site['menus'])
        site['menus'] = [m for m in site['menus'] if str(m.get('id')) != str(menu_id)]
        if len(site['menus']) < original_length:
            if param and param != '--':
                delete_menu_files(site_id, param)
            deleted_count += 1

    save_data(sites)
    return jsonify({'success': True, 'deleted_count': deleted_count})
