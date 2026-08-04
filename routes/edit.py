# Author: sawyer88
# Email: phongnguyen@andvina.com

"""
routes/edit.py
Blueprint xử lý chức năng Edit (chỉnh sửa) menu/page trong site detail.
"""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, request, redirect, url_for, flash, jsonify
from .helpers import load_data, save_data, parse_folder_slug

edit_bp = Blueprint('edit', __name__)

def handle_image_upload(site_id, menu_id, image_file):
    if image_file and image_file.filename:
        from flask import current_app
        import os
        from werkzeug.utils import secure_filename
        
        upload_dir = os.path.join(current_app.root_path, 'data', 'uploads', site_id)
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{menu_id}_{secure_filename(image_file.filename)}"
        save_path = os.path.join(upload_dir, filename)
        image_file.save(save_path)
        
        # Return a relative path for JSON storage
        return f"data/uploads/{site_id}/{filename}"
    return None

@edit_bp.route('/site/<site_id>/add-menu', methods=['POST'])
def add_menu(site_id):
    menu_name = request.form.get('menu_name', '').strip()
    parent_id = request.form.get('parent_id', '').strip()
    menu_slug = request.form.get('menu_slug', '').strip().strip('/')
    figma_link = request.form.get('figma_link', '').strip()
    layout = request.form.get('layout', 'sub-template').strip()
    image_file = request.files.get('image_file')

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Site not found!', 'danger')
        return redirect(url_for('index'))

    folder = ""
    if parent_id:
        parent_menu = next((m for m in site['menus'] if m['id'] == parent_id), None)
        if parent_menu:
            folder = parent_menu.get('slug', '')

    new_menu = {
        'id': str(uuid.uuid4()),
        'name': menu_name,
        'slug': menu_slug,
        'folder': folder,
        'figma_link': figma_link,
        'layout': layout,
        'parent_id': parent_id if parent_id else None,
        'generated': False,
        'order': len(site.get('menus', []))
    }

    image_path = handle_image_upload(site_id, new_menu['id'], image_file)
    if image_path:
        new_menu['image_path'] = image_path

    if 'menus' not in site:
        site['menus'] = []
    site['menus'].append(new_menu)

    save_data(sites)
    flash(f'Successfully added page "{menu_name}"!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))

@edit_bp.route('/site/<site_id>/edit-menu/<menu_param>', methods=['POST'])
def edit_menu(site_id, menu_param):
    new_name = request.form.get('menu_name', '').strip()
    new_parent_id = request.form.get('parent_id', '').strip()
    new_slug = request.form.get('menu_slug', '').strip().strip('/')
    new_figma = request.form.get('figma_link', '').strip()
    new_layout = request.form.get('layout', 'sub-template').strip()
    image_file = request.files.get('image_file')

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)

    new_folder = ""
    if new_parent_id and site:
        parent_menu = next((m for m in site['menus'] if m['id'] == new_parent_id), None)
        if parent_menu:
            new_folder = parent_menu.get('slug', '')

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

    remove_image = request.form.get('remove_image', '0')
    if remove_image == '1':
        if 'image_path' in menu:
            try:
                abs_path = menu['image_path']
                if not os.path.isabs(abs_path):
                    from flask import current_app
                    abs_path = os.path.join(current_app.root_path, abs_path)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
            except Exception:
                pass
            menu['image_path'] = ''
    else:
        image_path = handle_image_upload(site_id, menu['id'], image_file)
        if image_path:
            if 'image_path' in menu and menu['image_path'] and menu['image_path'] != image_path:
                try:
                    old_path = menu['image_path']
                    if not os.path.isabs(old_path):
                        from flask import current_app
                        old_path = os.path.join(current_app.root_path, old_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except Exception:
                    pass
            menu['image_path'] = image_path

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
