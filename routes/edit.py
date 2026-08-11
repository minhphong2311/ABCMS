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
from .helpers import load_data, save_data, parse_folder_slug, assign_folders_from_roots

edit_bp = Blueprint('edit', __name__)

def handle_multiple_image_upload(site_id, menu_id, image_files):
    paths = []
    if not image_files:
        return paths
        
    from flask import current_app
    import os
    from werkzeug.utils import secure_filename
    
    upload_dir = os.path.join(current_app.root_path, 'data', 'uploads', site_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    for idx, image_file in enumerate(image_files):
        if image_file and image_file.filename:
            # Handle empty filenames just in case
            if image_file.filename.strip() == '':
                continue
            # Generate unique filename for each image to prevent overwriting if same names
            ext = os.path.splitext(image_file.filename)[1]
            # Use original filename but prepend menu_id and index to avoid conflicts
            base_name = secure_filename(os.path.splitext(image_file.filename)[0])
            if not base_name:
                base_name = f"image_{idx}"
            filename = f"{menu_id}_{idx}_{base_name}{ext}"
            save_path = os.path.join(upload_dir, filename)
            image_file.save(save_path)
            paths.append(f"data/uploads/{site_id}/{filename}")
            
    return paths

@edit_bp.route('/site/<site_id>/add-menu', methods=['POST'])
def add_menu(site_id):
    menu_name = request.form.get('menu_name', '').strip()
    parent_id = request.form.get('parent_id', '').strip()
    menu_slug = request.form.get('menu_slug', '').strip().strip('/')
    figma_link = request.form.get('figma_link', '').strip()
    ai_hint = request.form.get('ai_hint', '').strip()
    layout = request.form.get('layout', 'sub-template').strip()
    image_files = request.files.getlist('image_files')

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Site not found!', 'danger')
        return redirect(url_for('index'))

    new_menu = {
        'id': str(uuid.uuid4()),
        'name': menu_name,
        'slug': menu_slug,
        'folder': "",
        'figma_link': figma_link,
        'ai_hint': ai_hint,
        'layout': layout,
        'parent_id': parent_id if parent_id else None,
        'generated': False,
        'order': len(site.get('menus', []))
    }

    image_paths = handle_multiple_image_upload(site_id, new_menu['id'], image_files)
    if image_paths:
        new_menu['image_paths'] = image_paths
    else:
        new_menu['image_paths'] = []

    if 'menus' not in site:
        site['menus'] = []
    site['menus'].append(new_menu)

    assign_folders_from_roots(site['menus'])
    save_data(sites)
    flash(f'Successfully added page "{menu_name}"!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))

@edit_bp.route('/site/<site_id>/edit-menu/<menu_id>', methods=['POST'])
def edit_menu(site_id, menu_id):
    new_name = request.form.get('menu_name', '').strip()
    new_parent_id = request.form.get('parent_id', '').strip()
    new_slug = request.form.get('menu_slug', '').strip().strip('/')
    new_figma = request.form.get('figma_link', '').strip()
    new_ai_hint = request.form.get('ai_hint', '').strip()
    new_layout = request.form.get('layout', 'sub-template').strip()
    image_files = request.files.getlist('image_files')

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Site not found!', 'danger')
        return redirect(url_for('index'))

    menu = next(
        (m for m in site['menus'] if m.get('id') == menu_id),
        None
    )
    if not menu:
        flash('Page not found!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    menu['name'] = new_name
    menu['slug'] = new_slug
    menu['folder'] = ""
    menu['figma_link'] = new_figma
    menu['ai_hint'] = new_ai_hint
    menu['layout'] = new_layout
    menu['parent_id'] = new_parent_id if new_parent_id else None

    # Determine existing image paths (backward compatibility)
    existing_paths = menu.get('image_paths', [])
    if not existing_paths and menu.get('image_path'):
        existing_paths = [menu.get('image_path')]

    import json
    images_to_remove_str = request.form.get('images_to_remove', '[]').strip()
    try:
        images_to_remove = json.loads(images_to_remove_str) if images_to_remove_str else []
    except json.JSONDecodeError:
        images_to_remove = []

    # Filter out removed paths and delete them from disk
    new_existing_paths = []
    for path in existing_paths:
        if path in images_to_remove or path.split('/')[-1] in images_to_remove or path.split('\\')[-1] in images_to_remove:
            try:
                abs_path = path
                if not os.path.isabs(abs_path):
                    from flask import current_app
                    abs_path = os.path.join(current_app.root_path, abs_path)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
            except Exception:
                pass
        else:
            new_existing_paths.append(path)

    # Check if there are valid new files uploaded
    valid_files = [f for f in image_files if f and f.filename and f.filename.strip() != '']
    if valid_files:
        # Save new images and append to the remaining existing ones
        new_uploaded_paths = handle_multiple_image_upload(site_id, menu['id'], image_files)
        menu['image_paths'] = new_existing_paths + new_uploaded_paths
    else:
        menu['image_paths'] = new_existing_paths

    if 'image_path' in menu:
        del menu['image_path']

    assign_folders_from_roots(site['menus'])
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
