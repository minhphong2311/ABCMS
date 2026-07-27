"""
routes/menu.py
All menu-related API routes: get, save, upload Excel.
"""
import json
import uuid
import time
from flask import Blueprint, request, jsonify

from routes.helpers import (
    load_data, save_data,
    get_config, make_unique_slug,
    assign_folders_from_roots, delete_menu_files
)

menu_bp = Blueprint('menu', __name__)


# ---------------------------------------------------------------------------
# GET menus
# ---------------------------------------------------------------------------

@menu_bp.route('/api/site/<site_id>/menus', methods=['GET'])
def api_get_menus(site_id):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'error': 'Site not found'}), 404
    menus = site.get('menus', [])
    return jsonify({'menus': menus})


# ---------------------------------------------------------------------------
# SAVE menus
# ---------------------------------------------------------------------------

@menu_bp.route('/api/site/<site_id>/menus/save', methods=['POST'])
def api_save_menus(site_id):
    menus_data = request.json
    if not isinstance(menus_data, list):
        return jsonify({'error': 'Invalid format, expected a list of menus'}), 400

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'error': 'Site not found'}), 404

    old_menus = {m['id']: m for m in site.get('menus', []) if 'id' in m}
    new_menus_ids = {m['id'] for m in menus_data if 'id' in m}
    deleted_ids = set(old_menus.keys()) - new_menus_ids

    for m_id in deleted_ids:
        menu = old_menus[m_id]
        menu_param = f"{menu.get('folder', '')}_{menu['slug']}" if menu.get('folder') else menu['slug']
        delete_menu_files(site_id, menu_param)

    assign_folders_from_roots(menus_data)
    site['menus'] = menus_data
    save_data(sites)
    return jsonify({'success': True, 'message': 'Menus saved successfully'})


# ---------------------------------------------------------------------------
# UPLOAD EXCEL → parse menus (preview only, not saved until user confirms)
# ---------------------------------------------------------------------------

@menu_bp.route('/api/site/<site_id>/menus/upload-excel', methods=['POST'])
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
        import re
        wb = openpyxl.load_workbook(file, data_only=True)
        sheet = wb.active

        new_menus = []
        headers = []
        depth_col_indices = []   # list of (level, col_idx, is_tab)
        other_col_indices = {}   # header_name -> col_idx
        header_row_index = -1
        last_seen_at_level = {}
        ignored_root = False

        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            row_strs = [str(c).lower().strip() if c is not None else '' for c in row]

            # 1. Identify the header row
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
                    continue  # Skip pre-header rows

            # 2. Skip fully empty rows
            if not any(row):
                continue

            if depth_col_indices:
                # --- Hierarchical structure ---
                #
                # State machine based on D1 value:
                #   header / footer  → ignore entire section
                #   main / 사용자    → enter active zone, skip the marker row itself
                #   empty D1         → inherit current ignored_root state (child rows)
                #   anything else    → normal menu item

                level0_col_idx = next((c for l, c, is_tab in depth_col_indices if l == 0), -1)
                skip_this_row = False

                if level0_col_idx != -1 and level0_col_idx < len(row):
                    val0 = row[level0_col_idx]
                    val0_str = str(val0).strip() if val0 is not None else ''
                    if val0_str:
                        val0_lower = val0_str.lower()
                        if val0_lower in ['header', 'footer']:
                            ignored_root = True
                            skip_this_row = True
                        elif val0_lower in ['main', '사용자']:
                            ignored_root = False
                            skip_this_row = True
                        else:
                            ignored_root = False

                if ignored_root or skip_this_row:
                    continue

                menus_on_this_row = []
                for level, col_idx, is_tab in depth_col_indices:
                    if col_idx >= len(row):
                        continue
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

                # Apply other column properties (slug, figma…) to the deepest menu on this row
                if menus_on_this_row:
                    deepest_menu = menus_on_this_row[-1]
                    for h, o_idx in other_col_indices.items():
                        if o_idx >= len(row):
                            continue
                        o_val = row[o_idx]
                        o_val_str = str(o_val).strip() if o_val is not None else ''
                        if not o_val_str:
                            continue
                        if h in ('id', 'menu id', 'code'):
                            deepest_menu['id'] = o_val_str
                        elif 'slug' in h or 'url' in h:
                            deepest_menu['slug'] = o_val_str
                        elif 'figma' in h or 'link' in h:
                            deepest_menu['figma_link'] = o_val_str

            else:
                # --- Flat structure fallback ---
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
                    if idx >= len(row):
                        continue
                    val = row[idx]
                    val_str = str(val).strip() if val is not None else ''
                    if not val_str:
                        continue
                    if h in ('id', 'menu id', 'code'):
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

        # --- Batch-generate missing slugs via Gemini AI ---
        missing_slug_menus = [m for m in new_menus if not m['slug']]
        if missing_slug_menus:
            input_dict = {m['id']: m['name'] for m in missing_slug_menus}
            config = get_config()
            api_key = config.get('gemini_api_key', '').strip()
            if api_key:
                try:
                    from google import genai
                    client = genai.Client(api_key=api_key)
                    prompt = (
                        'Translate these EXACTLY to short URL slugs (lowercase english words, hyphen separated).\n'
                        'Output NO other words, NO markdown, NO explanations. Just a valid JSON object '
                        'where keys are the same and values are the generated slugs. Max 3 words per slug.\n'
                        'Example Input: {"1": "부동산AI융합학과", "2": "회사 소개"}\n'
                        'Example Output: {"1": "real-estate-ai", "2": "about-us"}\n\n'
                        'Input: ' + json.dumps(input_dict, ensure_ascii=False) + '\nOutput:'
                    )
                    response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
                    output_text = response.text.strip()
                    if output_text.startswith('```'):
                        output_text = re.sub(r'^```[a-z]*\n|\n```$', '', output_text).strip()
                    # Extract JSON block in case model adds extra explanations
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
                    print('Batch slug generation failed:', e)

            # Fallback: timestamp-based slug for any still-empty
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
