import os
import json
import time
import threading
import uuid
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify, make_response

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = 'super-secret-key-for-cms-builder'

# ---------------------------------------------------------------------------
# Import shared helpers
# ---------------------------------------------------------------------------

from routes.helpers import (
    load_data, save_data,
    get_config, save_config,
    make_unique_slug, generate_slug_for_text,
    parse_folder_slug, delete_menu_files,
    DATA_FILE, OUTPUT_DIR, CONFIG_FILE
)

# ---------------------------------------------------------------------------
# Register Blueprints
# ---------------------------------------------------------------------------

from routes.generate import generate_bp
from routes.preview import preview_bp
from routes.deploy import deploy_bp
from routes.edit import edit_bp
from routes.delete import delete_bp

app.register_blueprint(generate_bp)
app.register_blueprint(preview_bp)
app.register_blueprint(deploy_bp)
app.register_blueprint(edit_bp)
app.register_blueprint(delete_bp)

# ---------------------------------------------------------------------------
# Slug API
# ---------------------------------------------------------------------------

@app.route('/api/generate-slug', methods=['POST'])
def generate_slug():
    data = request.json
    text = data.get('text', '').strip()
    slug = generate_slug_for_text(text)
    return jsonify({'slug': slug})

# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    sites = load_data()
    return render_template('index.html', sites=list(reversed(sites)))

# ---------------------------------------------------------------------------
# Site CRUD
# ---------------------------------------------------------------------------

@app.route('/add-site', methods=['POST'])
def add_site():
    site_id = request.form.get('site_id').strip()
    name = request.form.get('name').strip()
    url = request.form.get('url').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    js_guide = request.form.get('js_guide', '').strip()

    sites = load_data()
    if any(s['id'] == site_id for s in sites):
        flash(f'Site ID "{site_id}" already exists!', 'danger')
        return redirect(url_for('index'))

    new_site = {
        'id': site_id,
        'name': name,
        'url': url,
        'username': username,
        'password': password,
        'css_guide': request.form.get('css_guide', '').strip(),
        'js_guide': js_guide,
        'menus': []
    }
    sites.append(new_site)
    save_data(sites)
    flash(f'Successfully added site "{name}"!', 'success')
    return redirect(url_for('index'))


@app.route('/edit-site/<site_id>', methods=['POST'])
def edit_site(site_id):
    name = request.form.get('name').strip()
    url = request.form.get('url').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    css_guide = request.form.get('css_guide', '').strip()

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Site not found!', 'danger')
        return redirect(url_for('index'))

    site['name'] = name
    site['url'] = url
    site['username'] = username
    site['password'] = password
    site['css_guide'] = css_guide

    save_data(sites)
    flash(f'Successfully updated site "{name}"!', 'success')
    return redirect(url_for('index'))


@app.route('/delete-site/<site_id>', methods=['POST'])
def delete_site(site_id):
    sites = load_data()
    updated_sites = [s for s in sites if s['id'] != site_id]
    save_data(updated_sites)

    target_dir = os.path.join(OUTPUT_DIR, site_id)
    if os.path.exists(target_dir):
        try:
            import shutil
            shutil.rmtree(target_dir)
        except Exception:
            pass

    flash('Successfully deleted site!', 'success')
    return redirect(url_for('index'))

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@app.route('/settings')
def settings():
    return render_template('settings.html')

# ---------------------------------------------------------------------------
# Site Detail
# ---------------------------------------------------------------------------

@app.route('/site/<site_id>')
def site_detail(site_id):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash(f'Site with ID: {site_id} not found', 'danger')
        return redirect(url_for('index'))

    if 'folders' not in site:
        site['folders'] = []

    modified = False
    for menu in site.get('menus', []):
        f = menu.get('folder', '').strip()
        if f and f not in site['folders']:
            site['folders'].append(f)
            modified = True

    if modified:
        save_data(sites)

    return render_template('site_detail.html', site=site)

# ---------------------------------------------------------------------------
# Folder management
# ---------------------------------------------------------------------------

@app.route('/site/<site_id>/add-folder', methods=['POST'])
def add_folder(site_id):
    folder_name = request.form.get('folder_name', '').strip().strip('/')
    if not folder_name:
        flash('Folder name cannot be empty!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Site not found!', 'danger')
        return redirect(url_for('index'))

    if 'folders' not in site:
        site['folders'] = []

    if any(m.get('is_folder') and m.get('name') == folder_name for m in site['menus']):
        flash(f'Folder "{folder_name}" already exists!', 'warning')
        return redirect(url_for('site_detail', site_id=site_id))

    new_folder_menu = {
        'id': f"folder_{int(time.time())}",
        'name': folder_name,
        'is_folder': True
    }
    site['menus'].append(new_folder_menu)
    save_data(sites)
    flash(f'Successfully created folder "{folder_name}"!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))


@app.route('/site/<site_id>/edit-folder/<old_folder>', methods=['POST'])
def edit_folder(site_id, old_folder):
    new_folder = request.form.get('new_folder_name', '').strip().strip('/')
    if not new_folder:
        flash('New folder name cannot be empty!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Site not found!', 'danger')
        return redirect(url_for('index'))

    if 'folders' not in site or old_folder not in site['folders']:
        flash('Folder not found!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    if new_folder in site['folders'] and new_folder != old_folder:
        flash(f'Folder "{new_folder}" already exists!', 'warning')
        return redirect(url_for('site_detail', site_id=site_id))

    idx = site['folders'].index(old_folder)
    site['folders'][idx] = new_folder

    save_data(sites)

    old_dir = os.path.join(OUTPUT_DIR, site_id, old_folder)
    new_dir = os.path.join(OUTPUT_DIR, site_id, new_folder)
    if os.path.exists(old_dir):
        try:
            if os.path.exists(new_dir):
                for fname in os.listdir(old_dir):
                    import shutil
                    shutil.move(os.path.join(old_dir, fname), os.path.join(new_dir, fname))
                os.rmdir(old_dir)
            else:
                os.rename(old_dir, new_dir)
        except Exception:
            pass

    flash(f'Successfully renamed folder "{old_folder}" to "{new_folder}"!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))


@app.route('/site/<site_id>/delete-folder/<folder_name>', methods=['POST'])
def delete_folder(site_id, folder_name):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Site not found!', 'danger')
        return redirect(url_for('index'))

    if 'folders' not in site or folder_name not in site['folders']:
        flash('Folder not found!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    site['folders'] = [f for f in site['folders'] if f != folder_name]

    for menu in site.get('menus', []):
        if menu.get('folder', '') == folder_name:
            menu['folder'] = ""

    save_data(sites)

    src_dir = os.path.join(OUTPUT_DIR, site_id, folder_name)
    dst_dir = os.path.join(OUTPUT_DIR, site_id)
    if os.path.exists(src_dir):
        try:
            for fname in os.listdir(src_dir):
                import shutil
                shutil.move(os.path.join(src_dir, fname), os.path.join(dst_dir, fname))
            os.rmdir(src_dir)
        except Exception:
            pass

    flash(f'Deleted folder "{folder_name}". Pages moved to root!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))


@app.route('/site/<site_id>/reorder-folder/<folder_name>/<direction>', methods=['POST'])
def reorder_folder(site_id, folder_name, direction):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Site not found!', 'danger')
        return redirect(url_for('index'))

    if 'folders' not in site or folder_name not in site['folders']:
        flash('Folder not found!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    folders = site['folders']
    idx = folders.index(folder_name)

    if direction == 'up' and idx > 0:
        folders[idx], folders[idx - 1] = folders[idx - 1], folders[idx]
    elif direction == 'down' and idx < len(folders) - 1:
        folders[idx], folders[idx + 1] = folders[idx + 1], folders[idx]

    save_data(sites)
    flash('Folder reordered successfully!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))

# ---------------------------------------------------------------------------
# Menu management (Add)
# ---------------------------------------------------------------------------

def assign_folders_from_roots(menus):
    menu_dict = {m['id']: m for m in menus if 'id' in m}
    for m in menus:
        if 'id' not in m:
            continue
        current = m
        visited = set()
        while current.get('parent_id') and current['parent_id'] in menu_dict:
            if current['id'] in visited:
                break
            visited.add(current['id'])
            current = menu_dict[current['parent_id']]
        m['folder'] = current.get('slug', '')


@app.route('/site/<site_id>/add-menu', methods=['POST'])
def add_menu(site_id):
    menu_name = request.form.get('menu_name', '').strip()
    parent_id = request.form.get('parent_id', '').strip()

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)

    folder = ""
    if parent_id and site:
        parent_menu = next((m for m in site['menus'] if m['id'] == parent_id), None)
        if parent_menu:
            folder = parent_menu.get('slug', '')

    menu_slug = request.form.get('menu_slug', '').strip().strip('/')
    figma_link = request.form.get('figma_link', '').strip()
    layout = request.form.get('layout', 'sub-template').strip()

    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Site not found!', 'danger')
        return redirect(url_for('index'))

    if not menu_slug and menu_name:
        menu_slug = generate_slug_for_text(menu_name)
        if not menu_slug:
            menu_slug = 'auto-' + str(int(time.time() * 1000))

    existing_slugs = {m['slug'] for m in site['menus'] if m.get('slug')}
    menu_slug = make_unique_slug(menu_slug, existing_slugs)

    if any(m.get('folder', '') == folder and m['slug'] == menu_slug for m in site['menus']):
        flash(f'Path "{folder}" and slug "{menu_slug}" already exists!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    new_menu = {
        'name': menu_name,
        'folder': folder,
        'slug': menu_slug,
        'figma_link': figma_link,
        'layout': layout,
        'id': str(uuid.uuid4()),
        'generated': False,
        'parent_id': parent_id if parent_id else None
    }
    site['menus'].insert(0, new_menu)
    save_data(sites)
    flash(f'Added page "{menu_name}"!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))

# ---------------------------------------------------------------------------
# Menu API (get / save / upload)
# ---------------------------------------------------------------------------

@app.route('/api/site/<site_id>/menus', methods=['GET'])
def api_get_menus(site_id):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'error': 'Site not found'}), 404
    menus = site.get('menus', [])
    return jsonify({'menus': menus})


@app.route('/api/site/<site_id>/menus/save', methods=['POST'])
def api_save_menus(site_id):
    menus_data = request.json
    if not isinstance(menus_data, list):
        return jsonify({'error': 'Invalid format, expected a list of menus'}), 400

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'error': 'Site not found'}), 404

    old_menus = {m['id']: m for m in site.get('menus', []) if 'id' in m}
    new_menus = {m['id'] for m in menus_data if 'id' in m}
    deleted_ids = set(old_menus.keys()) - new_menus

    for m_id in deleted_ids:
        menu = old_menus[m_id]
        menu_param = f"{menu.get('folder', '')}_{menu['slug']}" if menu.get('folder') else menu['slug']
        delete_menu_files(site_id, menu_param)

    assign_folders_from_roots(menus_data)
    site['menus'] = menus_data
    save_data(sites)
    return jsonify({'success': True, 'message': 'Menus saved successfully'})


@app.route('/api/site/<site_id>/menus/upload-excel', methods=['POST'])
def api_upload_menus_excel(site_id):
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'error': 'Site not found'}), 404

    try:
        import openpyxl
        wb = openpyxl.load_workbook(file, data_only=True)
        sheet = wb.active

        new_menus = []
        headers = []
        depth_col_indices = []
        other_col_indices = {}
        header_row_index = -1
        last_seen_at_level = {}
        ignored_root = False
        import re

        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            row_strs = [str(c).lower().strip() if c is not None else '' for c in row]
            
            # 1. Identify header row
            if header_row_index == -1:
                has_depth = any(re.match(r'^(?:d|depth|tab)\s*\d+$', h) for h in row_strs)
                if has_depth or 'name' in row_strs or 'title' in row_strs:
                    header_row_index = i
                    headers = row_strs
                    level = 0
                    for idx, h in enumerate(headers):
                        if re.match(r'^(?:d|depth)\s*\d+$', h):
                            depth_col_indices.append((level, idx, False))
                            level += 1
                        elif re.match(r'^tab\s*\d+$', h):
                            depth_col_indices.append((level, idx, True))
                            level += 1
                        elif h:
                            other_col_indices[h] = idx
                    continue
                else:
                    continue # Skip pre-header rows
            
            # 2. Process data rows
            if not any(row):
                continue

            if depth_col_indices:
                # Hierarchical structure processing
                
                # Check level 0 to determine if this branch should be ignored
                # Only update ignored_root when D1 has a non-empty value
                level0_col_idx = next((c for l, c, is_tab in depth_col_indices if l == 0), -1)
                skip_this_row = False
                if level0_col_idx != -1 and level0_col_idx < len(row):
                    val0 = row[level0_col_idx]
                    val0_str = str(val0).strip() if val0 is not None else ''
                    if val0_str:
                        val0_lower = val0_str.lower()
                        if val0_lower in ['header', 'footer']:
                            # This whole section is header/footer — ignore everything under it
                            ignored_root = True
                            skip_this_row = True
                        elif val0_lower in ['main', '사용자']:
                            # These are structural markers — switch to active zone but don't create a menu item
                            ignored_root = False
                            skip_this_row = True
                        else:
                            # Normal D1 value — create menu
                            ignored_root = False
                    # If val0_str is empty, keep current ignored_root state (child rows)
                            
                if ignored_root or skip_this_row:
                    continue
                    
                menus_on_this_row = []
                for level, col_idx, is_tab in depth_col_indices:
                    if col_idx >= len(row): continue
                    val = row[col_idx]
                    val_str = str(val).strip() if val is not None else ''
                    
                    if not val_str:
                        continue

                    menu_item = {
                        'id': str(uuid.uuid4()),
                        'parent_id': None,
                        'name': val_str,
                        'slug': '',
                        'figma_link': '',
                        'layout': 'sub-template-tab' if is_tab else 'sub-template',
                        'order': len(new_menus),
                        'generated': False
                    }
                    
                    # Find the closest parent level
                    parent_level = -1
                    for k in sorted(last_seen_at_level.keys(), reverse=True):
                        if k < level:
                            parent_level = k
                            break
                            
                    if parent_level != -1:
                        menu_item['parent_id'] = last_seen_at_level[parent_level]['id']
                        
                    last_seen_at_level[level] = menu_item
                    keys_to_delete = [k for k in last_seen_at_level if k > level]
                    for k in keys_to_delete:
                        del last_seen_at_level[k]
                        
                    menus_on_this_row.append(menu_item)
                    new_menus.append(menu_item)
                
                # Apply other column properties (like slug, figma) to the deepest menu created on this row
                if menus_on_this_row:
                    deepest_menu = menus_on_this_row[-1]
                    for h, o_idx in other_col_indices.items():
                        if o_idx >= len(row): continue
                        o_val = row[o_idx]
                        o_val_str = str(o_val).strip() if o_val is not None else ''
                        if not o_val_str: continue
                        
                        if 'id' == h or 'menu id' in h or 'code' in h:
                            deepest_menu['id'] = o_val_str
                        elif 'slug' in h or 'url' in h:
                            deepest_menu['slug'] = o_val_str
                        elif 'figma' in h or 'link' in h:
                            deepest_menu['figma_link'] = o_val_str
            else:
                # Flat structure processing (fallback)
                menu_item = {
                    'id': str(uuid.uuid4()),
                    'parent_id': None,
                    'name': f'Menu {len(new_menus)}',
                    'slug': '',
                    'figma_link': '',
                    'layout': 'sub-template',
                    'order': len(new_menus),
                    'generated': False
                }
                for h, idx in other_col_indices.items():
                    if idx >= len(row): continue
                    val = row[idx]
                    val_str = str(val).strip() if val is not None else ''
                    if not val_str: continue
                    
                    if 'id' == h or 'menu id' in h or 'code' in h:
                        menu_item['id'] = val_str
                    elif 'parent' in h:
                        menu_item['parent_id'] = val_str
                    elif 'name' in h or 'title' in h:
                        menu_item['name'] = val_str
                    elif 'slug' in h or 'url' in h:
                        menu_item['slug'] = val_str
                    elif 'figma' in h or 'link' in h:
                        menu_item['figma_link'] = val_str
                
                new_menus.append(menu_item)

        # Batch generate missing slugs
        missing_slug_menus = [m for m in new_menus if not m['slug']]
        if missing_slug_menus:
            input_dict = {m['id']: m['name'] for m in missing_slug_menus}

            config = get_config()
            api_key = config.get('gemini_api_key', '').strip()
            if api_key:
                try:
                    from google import genai
                    import re
                    client = genai.Client(api_key=api_key)
                    prompt = (
                        'Translate these EXACTLY to short URL slugs (lowercase english words, hyphen separated).\n'
                        'Output NO other words, NO markdown, NO explanations. Just a valid JSON object where keys are the same and values are the generated slugs. Max 3 words per slug.\n'
                        'Example Input: {"1": "부동산AI융합학과", "2": "회사 소개"}\n'
                        'Example Output: {"1": "real-estate-ai", "2": "about-us"}\n\n'
                        'Input: ' + json.dumps(input_dict, ensure_ascii=False) + '\nOutput:'
                    )
                    response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
                    output_text = response.text.strip()
                    if output_text.startswith('```'):
                        output_text = re.sub(r'^```[a-z]*\n|\n```$', '', output_text).strip()
                    # Try to find JSON in the output in case model adds extra text
                    json_match = re.search(r'\{[^}]+\}', output_text, re.DOTALL)
                    if json_match:
                        output_text = json_match.group(0)

                    slug_dict = json.loads(output_text)
                    existing_slugs = {m['slug'] for m in site.get('menus', []) if m.get('slug')}
                    for m in new_menus:
                        if m.get('slug'):
                            existing_slugs.add(m['slug'])

                    for m in missing_slug_menus:
                        if m['id'] in slug_dict:
                            slug = slug_dict[m['id']].lower()
                            slug = re.sub(r'[^a-z0-9\-]+', '', slug)
                            slug = make_unique_slug(slug, existing_slugs)
                            m['slug'] = slug
                            existing_slugs.add(slug)
                except Exception as e:
                    print("Batch slug generation failed:", e)

            base_time = int(time.time() * 1000)
            for idx, m in enumerate(missing_slug_menus):
                if not m['slug']:
                    m['slug'] = 'auto-' + str(base_time + idx)

        assign_folders_from_roots(new_menus)
        return jsonify({
            'success': True, 
            'message': f'Parsed {len(new_menus)} menus from Excel. Please review and click Save Changes to confirm.', 
            'new_menus': new_menus
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------------------------------------------------------------------------
# Config API
# ---------------------------------------------------------------------------

@app.route('/api/config', methods=['GET'])
def api_get_config():
    config = get_config()
    return jsonify({
        'success': True,
        'gemini_api_key': config.get('gemini_api_key', ''),
        'figma_token': config.get('figma_token', '')
    })


@app.route('/api/config', methods=['POST'])
def api_save_config():
    data = request.json
    config = get_config()
    if 'gemini_api_key' in data:
        config['gemini_api_key'] = data['gemini_api_key']
    if 'figma_token' in data:
        config['figma_token'] = data['figma_token']
    save_config(config)
    return jsonify({'success': True, 'message': 'Config saved'})

# ---------------------------------------------------------------------------
# Chat AI API
# ---------------------------------------------------------------------------

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json or {}
    user_message = data.get('message', '').strip()
    site_id = data.get('site_id', '').strip()
    menu_param = data.get('menu_param', '').strip()

    if not user_message:
        return jsonify({'success': False, 'reply': 'Please enter a request.'}), 400

    folder, menu_slug = parse_folder_slug(menu_param)
    if folder:
        base_dir = os.path.join(OUTPUT_DIR, site_id, folder)
    else:
        base_dir = os.path.join(OUTPUT_DIR, site_id)

    css_path = os.path.join(base_dir, f'{menu_slug}.css')
    html_path = os.path.join(base_dir, f'{menu_slug}.html')

    current_css = ''
    current_html = ''

    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            current_css = f.read()
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            current_html = f.read()

    config = get_config()
    api_key = config.get('gemini_api_key', '').strip()

    if not api_key:
        return jsonify({
            'success': False,
            'reply': '⚠️ Gemini API Key not configured. Please go to Site Details and enter the API Key.'
        }), 400

    structure_template = ''
    table_template = ''
    structure_path = os.path.join(app.root_path, 'data', 'ai_templates', 'structure-template.html')
    table_path = os.path.join(app.root_path, 'data', 'ai_templates', 'table-template.html')

    if os.path.exists(structure_path):
        with open(structure_path, 'r', encoding='utf-8') as f:
            structure_template = f.read()
    if os.path.exists(table_path):
        with open(table_path, 'r', encoding='utf-8') as f:
            table_template = f.read()

    try:
        from google import genai as _genai
        client = _genai.Client(api_key=api_key)

        sites = load_data()
        site = next((s for s in sites if s['id'] == site_id), {})
        css_guide_raw = site.get('css_guide', '').strip()
        css_links = [link.strip() for link in css_guide_raw.split('\n') if link.strip()]
        if css_links:
            css_guide_instruction = (
                f"\n\nĐẶC BIỆT LƯU Ý VỀ CẤU TRÚC CSS:\n1. Dự án sử dụng CSS chuẩn tại: "
                + ", ".join(css_links) +
                ".\nTUYỆT ĐỐI TUÂN THỦ khoảng cách (margin, padding) đã định nghĩa trong guide. Không thêm margin/padding dư thừa làm sai lệch giao diện gốc (ví dụ: nếu guide dùng padding-bottom, đừng thêm margin-bottom).\n"
                "2. BẮT BUỘC FORMAT CSS: Mỗi rule CSS (selector + thuộc tính) phải nằm trọn trên 1 dòng riêng biệt và phải có XUỐNG DÒNG (\\n) giữa các rule khác nhau. (VD:\n.class1 {{ font-size: 20px; color: #333; }}\n.class2 {{ margin-bottom: 15px; }}\n)\n"
                "Tuyệt đối không gộp toàn bộ file thành 1 dòng duy nhất, và tuyệt đối KHÔNG xuống dòng bên trong dấu ngoặc nhọn {{}}.\n"
                f"3. SỬ DỤNG ẢNH PNG CHO ICON: BẮT BUỘC sử dụng thẻ <img> với định dạng PNG (vd: <img src=\"./images/{menu_slug}/icon_name.png\" alt=\"icon\">) cho tất cả các icon thay vì sử dụng thẻ span hay font icon."
            )
        else:
            css_guide_instruction = (
                "\n\nĐẶC BIỆT LƯU Ý FORMAT CSS:\nBẮT BUỘC FORMAT CSS: Mỗi rule CSS phải nằm trên 1 dòng riêng biệt và có XUỐNG DÒNG (\\n) giữa các rule. (VD:\n.class1 {{ font-size: 20px; }}\n.class2 {{ margin: 0; }}\n)\n"
                "Tuyệt đối không gộp toàn bộ file thành 1 dòng, và tuyệt đối KHÔNG xuống dòng bên trong ngoặc nhọn {{}}.\n"
                "3. SỬ DỤNG ẢNH PNG CHO ICON: BẮT BUỘC sử dụng thẻ <img> định dạng PNG cho tất cả icon."
            )

        prompt = f"""Bạn là một chuyên gia Frontend Developer.
Người dùng đang xem preview một trang web và muốn điều chỉnh giao diện.
Bạn có thể thay đổi cả HTML lẫn CSS để đáp ứng yêu cầu.

Yêu cầu của người dùng: "{user_message}"

Nội dung HTML hiện tại của trang:
```html
{current_html[:6000]}
```

Nội dung CSS hiện tại:
```css
{current_css[:5000]}
```{css_guide_instruction}

TÀI LIỆU THAM KHẢO VỀ CẤU TRÚC VÀ SUB-TEMPLATE MÀ BẠN NÊN ÁP DỤNG NẾU NGƯỜI DÙNG YÊU CẦU:

Mẫu cấu trúc giao diện chung (structure-template.html):
```html
{structure_template}
```

Mẫu bảng (table-template.html):
```html
{table_template}
```

Nhiệm vụ:
1. Phân tích yêu cầu (có thể là thay đổi thẻ HTML (đổi tag, class, nội dung), thay đổi CSS (màu sắc, kích thước, khoảng cách), hoặc cả hai. Áp dụng các mẫu template nếu phù hợp.
2. TUYỆT ĐỐI KHÔNG SỬ DỤNG INLINE STYLE TRONG HTML (`style="..."`). TẤT CẢ CÁC STYLE MỚI PHẢI ĐƯỢC VIẾT VÀO NỘI DUNG CSS ĐƯỢC TRẢ VỀ.
3. Thực hiện thay đổi chính xác theo yêu cầu.
4. Trả về TOÀN BỘ nội dung HTML và CSS sau khi đã thay đổi.

Trả lời theo định dạng JSON sau (không thêm gì ngoài JSON, không bọc trong markdown):
{{
  "explanation": "Giải thích ngắn gọn bằng tiếng Việt những gì đã thay đổi",
  "html": "toàn bộ nội dung HTML mới (hoặc chuỗi rỗng nếu không thay đổi HTML)",
  "css": "toàn bộ nội dung CSS mới (hoặc chuỗi rỗng nếu không thay đổi CSS)"
}}"""

        response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
        text = response.text.strip()

        import json as _json
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif text.startswith('```'):
            text = text.split('```')[1].split('```')[0].strip()

        result = _json.loads(text)
        new_html = result.get('html', '').strip()
        new_css = result.get('css', '').strip()
        explanation = result.get('explanation', 'Đã cập nhật.')

        updated = False

        if new_html and os.path.exists(html_path):
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(new_html)
            updated = True

        if new_css and os.path.exists(css_path):
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(new_css)
            updated = True

        return jsonify({
            'success': True,
            'reply': explanation,
            'css_updated': updated
        })

    except Exception as e:
        print(f"[Chat AI] Error: {e}")
        return jsonify({
            'success': False,
            'reply': f'❌ Lỗi kết nối AI: {str(e)}'
        }), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, port=5000)
