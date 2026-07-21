import os
import json
import time
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify, make_response

app = Flask(__name__)
app.secret_key = 'super-secret-key-for-cms-builder'

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'sites.json')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')

# Helper function to load data
def load_data():
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

# Helper function to save data
def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'data', 'config.json')

def get_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    sites = load_data()
    # Reverse the list so the newest sites (added last) appear first
    return render_template('index.html', sites=list(reversed(sites)))

@app.route('/add-site', methods=['POST'])
def add_site():
    site_id = request.form.get('site_id').strip()
    name = request.form.get('name').strip()
    url = request.form.get('url').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    sites = load_data()
    # Check if ID already exists
    if any(s['id'] == site_id for s in sites):
        flash(f'Site ID "{site_id}" đã tồn tại!', 'danger')
        return redirect(url_for('index'))

    new_site = {
        'id': site_id,
        'name': name,
        'url': url,
        'username': username,
        'password': password,
        'css_guide': request.form.get('css_guide', '').strip(),
        'menus': []
    }
    sites.append(new_site)
    save_data(sites)
    flash(f'Đã thêm site "{name}" thành công!', 'success')
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
        flash('Không tìm thấy site!', 'danger')
        return redirect(url_for('index'))
        
    site['name'] = name
    site['url'] = url
    site['username'] = username
    site['password'] = password
    site['css_guide'] = css_guide
    
    save_data(sites)
    flash(f'Đã cập nhật site "{name}" thành công!', 'success')
    return redirect(url_for('index'))

@app.route('/delete-site/<site_id>', methods=['POST'])
def delete_site(site_id):
    sites = load_data()
    updated_sites = [s for s in sites if s['id'] != site_id]
    save_data(updated_sites)
    
    # Delete corresponding site folder in output
    target_dir = os.path.join(OUTPUT_DIR, site_id)
    if os.path.exists(target_dir):
        try:
            import shutil
            shutil.rmtree(target_dir)
        except Exception:
            pass
            
    flash(f'Đã xóa site thành công!', 'success')
    return redirect(url_for('index'))

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/site/<site_id>')
def site_detail(site_id):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash(f'Không tìm thấy site với ID: {site_id}', 'danger')
        return redirect(url_for('index'))
    
    # Initialize folders list if missing
    if 'folders' not in site:
        site['folders'] = []
    
    # Auto-sync existing folders from page items to site folders
    modified = False
    for menu in site.get('menus', []):
        f = menu.get('folder', '').strip()
        if f and f not in site['folders']:
            site['folders'].append(f)
            modified = True
            
    if modified:
        save_data(sites)
        
    return render_template('site_detail.html', site=site)

@app.route('/site/<site_id>/add-folder', methods=['POST'])
def add_folder(site_id):
    folder_name = request.form.get('folder_name', '').strip().strip('/')
    if not folder_name:
        flash('Tên thư mục không được để trống!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Không tìm thấy site!', 'danger')
        return redirect(url_for('index'))

    if 'folders' not in site:
        site['folders'] = []

    if folder_name in site['folders']:
        flash(f'Thư mục "{folder_name}" đã tồn tại!', 'warning')
        return redirect(url_for('site_detail', site_id=site_id))

    site['folders'].append(folder_name)
    save_data(sites)

    # Create directory physically
    os.makedirs(os.path.join(OUTPUT_DIR, site_id, folder_name), exist_ok=True)

    flash(f'Đã tạo thư mục "{folder_name}" thành công!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))

@app.route('/site/<site_id>/edit-folder/<old_folder>', methods=['POST'])
def edit_folder(site_id, old_folder):
    new_folder = request.form.get('new_folder_name', '').strip().strip('/')
    if not new_folder:
        flash('Tên thư mục mới không được để trống!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Không tìm thấy site!', 'danger')
        return redirect(url_for('index'))

    if 'folders' not in site or old_folder not in site['folders']:
        flash('Không tìm thấy thư mục cần sửa!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    if new_folder in site['folders'] and new_folder != old_folder:
        flash(f'Tên thư mục "{new_folder}" đã tồn tại!', 'warning')
        return redirect(url_for('site_detail', site_id=site_id))

    # Update metadata folder name
    idx = site['folders'].index(old_folder)
    site['folders'][idx] = new_folder

    # Update folder references for all pages
    for menu in site.get('menus', []):
        if menu.get('folder', '') == old_folder:
            menu['folder'] = new_folder

    save_data(sites)

    # Rename physical directory on disk
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

    flash(f'Đã đổi tên thư mục "{old_folder}" thành "{new_folder}"!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))

@app.route('/site/<site_id>/delete-folder/<folder_name>', methods=['POST'])
def delete_folder(site_id, folder_name):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Không tìm thấy site!', 'danger')
        return redirect(url_for('index'))

    if 'folders' not in site or folder_name not in site['folders']:
        flash('Không tìm thấy thư mục cần xóa!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    # Remove from site folders metadata
    site['folders'] = [f for f in site['folders'] if f != folder_name]

    # Move pages inside deleted folder to root
    for menu in site.get('menus', []):
        if menu.get('folder', '') == folder_name:
            menu['folder'] = ""

    save_data(sites)

    # Move files physically on disk
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

    flash(f'Đã xóa thư mục "{folder_name}". Các trang con bên trong được di chuyển về thư mục gốc!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))

@app.route('/site/<site_id>/reorder-folder/<folder_name>/<direction>', methods=['POST'])
def reorder_folder(site_id, folder_name, direction):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Không tìm thấy site!', 'danger')
        return redirect(url_for('index'))
        
    if 'folders' not in site or folder_name not in site['folders']:
        flash('Không tìm thấy thư mục!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))
        
    folders = site['folders']
    idx = folders.index(folder_name)
    
    if direction == 'up' and idx > 0:
        folders[idx], folders[idx - 1] = folders[idx - 1], folders[idx]
    elif direction == 'down' and idx < len(folders) - 1:
        folders[idx], folders[idx + 1] = folders[idx + 1], folders[idx]
        
    save_data(sites)
    flash('Đã thay đổi vị trí thư mục con thành công!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))

@app.route('/site/<site_id>/add-menu', methods=['POST'])
def add_menu(site_id):
    menu_name = request.form.get('menu_name', '').strip()
    folder = request.form.get('folder', '').strip().strip('/')
    menu_slug = request.form.get('menu_slug', '').strip().strip('/')
    figma_link = request.form.get('figma_link', '').strip()
    layout = request.form.get('layout', 'sub-template').strip()

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Không tìm thấy site!', 'danger')
        return redirect(url_for('index'))

    # Check if folder + slug composite exists in site menus
    if any(m.get('folder', '') == folder and m['slug'] == menu_slug for m in site['menus']):
        flash(f'Đường dẫn thư mục "{folder}" và file "{menu_slug}" đã tồn tại!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))

    new_menu = {
        'name': menu_name,
        'folder': folder,
        'slug': menu_slug,
        'figma_link': figma_link,
        'layout': layout,
        'generated': False
    }
    site['menus'].insert(0, new_menu)
    save_data(sites)
    flash(f'Đã thêm trang "{menu_name}"!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))

def parse_figma_url(url):
    try:
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        file_key = None
        if len(path_parts) >= 2:
            if path_parts[0] in ['design', 'file']:
                file_key = path_parts[1]
        
        queries = urlparse.parse_qs(parsed.query)
        node_id = queries.get('node-id', [None])[0]
        if node_id:
            node_id = node_id.replace('-', ':')
        return file_key, node_id
    except Exception:
        return None, None

def fetch_figma_node(file_key, node_id, token):
    # 1. Check local figma cache first
    cache_path = os.path.join('data', 'figma_cache.json')
    if os.path.exists(cache_path):
        try:
            import json
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            cache_key = f"{file_key}:{node_id}"
            if cache_key in cache_data:
                print(f"[Figma] Loaded from cache: {cache_key}")
                return cache_data[cache_key]
        except Exception as e:
            print(f"[Figma] Cache error: {e}")

    # 2. Try network call
    if not token:
        print("[Figma] No token provided, skipping API call.")
        return None
    try:
        import requests
        headers = {'X-Figma-Token': token}
        url = f"https://api.figma.com/v1/files/{file_key}/nodes?ids={node_id}"
        print(f"[Figma] Fetching: {url}")
        r = requests.get(url, headers=headers, timeout=30)
        print(f"[Figma] Status code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            # Save to cache
            try:
                import json
                cache_path = os.path.join('data', 'figma_cache.json')
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                existing = {}
                if os.path.exists(cache_path):
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                existing[f"{file_key}:{node_id}"] = data
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(existing, f, ensure_ascii=False)
            except Exception as ce:
                print(f"[Figma] Failed to save cache: {ce}")
            return data
        else:
            print(f"[Figma] API error: {r.status_code} - {r.text[:200]}")
    except Exception as e:
        print(f"[Figma] Request exception: {e}")
    return None

def extract_used_image_refs(node, used_refs=None):
    if used_refs is None:
        used_refs = set()
    
    fills = node.get('fills', [])
    for fill in fills:
        if fill.get('type') == 'IMAGE' and 'imageRef' in fill:
            used_refs.add(fill['imageRef'])
            
    for child in node.get('children', []):
        extract_used_image_refs(child, used_refs)
        
    return used_refs

def fetch_figma_images(file_key, token):
    try:
        import requests
        headers = {'X-Figma-Token': token}
        url = f"https://api.figma.com/v1/files/{file_key}/images"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json().get('meta', {}).get('images', {})
    except Exception:
        pass
    return {}

def download_and_map_figma_images(image_map, target_dir, menu_slug, used_refs=None):
    if not image_map:
        return {}
    import urllib.request
    import json
    
    images_dir = os.path.join(target_dir, "images", menu_slug)
    os.makedirs(images_dir, exist_ok=True)
    
    map_file = os.path.join(images_dir, '.image_refs.json')
    ref_to_filename = {}
    if os.path.exists(map_file):
        try:
            with open(map_file, 'r', encoding='utf-8') as f:
                ref_to_filename = json.load(f)
        except Exception:
            pass
            
    max_idx = 0
    for fname in ref_to_filename.values():
        base = fname.rsplit('.', 1)[0]
        if '-' in base:
            idx_str = base.split('-')[-1]
            if idx_str.isdigit():
                max_idx = max(max_idx, int(idx_str))
                
    local_image_map = {}
    
    for ref, url in image_map.items():
        if used_refs is not None and ref not in used_refs:
            continue
        if url:
            try:
                if ref in ref_to_filename:
                    filename = ref_to_filename[ref]
                    local_path = os.path.join(images_dir, filename)
                    if not os.path.exists(local_path):
                        with urllib.request.urlopen(url) as response:
                            with open(local_path, 'wb') as f:
                                f.write(response.read())
                else:
                    with urllib.request.urlopen(url) as response:
                        content_type = response.headers.get('Content-Type', '')
                        ext = 'jpg' if 'jpeg' in content_type.lower() or 'jpg' in content_type.lower() else 'png'
                        max_idx += 1
                        filename = f"{menu_slug}-{max_idx:02d}.{ext}"
                        ref_to_filename[ref] = filename
                        
                        local_path = os.path.join(images_dir, filename)
                        with open(local_path, 'wb') as f:
                            f.write(response.read())
                            
                local_image_map[ref] = f"./images/{menu_slug}/{filename}"
            except Exception as e:
                print(f"Failed to download image {ref}: {e}")
                local_image_map[ref] = url
                
    try:
        with open(map_file, 'w', encoding='utf-8') as f:
            json.dump(ref_to_filename, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save image ref map: {e}")
        
    return local_image_map

def export_figma_icons(file_key, document, token, target_dir, menu_slug):
    """Export icon nodes from Figma as PNG files.
    Icons are identified as non-text nodes with both width and height <= 48px."""
    import requests
    import urllib.request
    import os

    icon_nodes = []  # list of (node_id, clean_name)
    seen_ids = set()

    def find_icon_nodes(node):
        node_id = node.get('id', '')
        name = node.get('name', '')
        t = node.get('type', '')
        bb = node.get('absoluteBoundingBox', {})
        w = bb.get('width', 0)
        h = bb.get('height', 0)
        fills = node.get('fills', [])
        has_image_fill = any(f.get('type') == 'IMAGE' for f in fills)
        # Icon: small node (<=48px), not a bitmap image fill, not just text
        if (
            node_id
            and node_id not in seen_ids
            and t not in ('TEXT', 'DOCUMENT', 'CANVAS', 'PAGE')
            and w > 0 and h > 0
            and w <= 48 and h <= 48
            and not has_image_fill
        ):
            clean_name = "".join([c if c.isalnum() or c in ['-', '_'] else '_' for c in name])
            if not clean_name:
                clean_name = f"icon_{node_id.replace(':', '_')}"
            if not clean_name.lower().endswith('.png'):
                clean_name += '.png'
            seen_ids.add(node_id)
            icon_nodes.append((node_id, clean_name))
            return  # don't descend into icon children
        for child in node.get('children', []):
            find_icon_nodes(child)

    find_icon_nodes(document)
    
    icon_map = {}
    if not icon_nodes:
        return icon_map
        
    print(f"[Figma] Exporting {len(icon_nodes)} icon nodes as PNG...")
    headers = {'X-Figma-Token': token}
    images_dir = os.path.join(target_dir, "images", menu_slug)
    os.makedirs(images_dir, exist_ok=True)

    # Figma API can handle up to ~200 ids at once; process in batches
    batch_size = 100
    for batch_start in range(0, len(icon_nodes), batch_size):
        batch = icon_nodes[batch_start:batch_start + batch_size]
        ids_str = ",".join(nid for nid, _ in batch)
        url = f"https://api.figma.com/v1/images/{file_key}?ids={ids_str}&format=png&scale=2"
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code != 200:
                print(f"[Figma] Icon export API error: {r.status_code} {r.text[:200]}")
                continue
            images_resp = r.json().get('images', {})
            for node_id, clean_name in batch:
                img_url = images_resp.get(node_id)
                if not img_url:
                    continue
                local_path = os.path.join(images_dir, clean_name)
                try:
                    with urllib.request.urlopen(img_url) as resp:
                        with open(local_path, 'wb') as f:
                            f.write(resp.read())
                    print(f"[Figma] Saved icon: {clean_name}")
                    icon_map[node_id] = f"./images/{menu_slug}/{clean_name}"
                except Exception as e:
                    print(f"[Figma] Failed to download icon {clean_name}: {e}")
        except Exception as e:
            print(f"[Figma] Failed to export icons batch: {e}")

    return icon_map

def parse_figma_fill(fills, image_map=None):
    if not fills:
        return None, "transparent"
        
    for fill in reversed(fills):
        if not fill.get('visible', True): continue
        if fill.get('type') == 'IMAGE':
            ref = fill.get('imageRef')
            url = image_map.get(ref) if image_map else None
            if url: return "image", f"url('{url}')"
            return "image", f"url('http://localhost:3845/assets/{ref}.png')"
            
    for fill in reversed(fills):
        if not fill.get('visible', True): continue
        if fill.get('type') in ['GRADIENT_LINEAR', 'GRADIENT_RADIAL']:
            stops = fill.get('gradientStops', [])
            stop_strs = []
            for stop in stops:
                color = stop.get('color', {})
                r = int(color.get('r', 0) * 255)
                g = int(color.get('g', 0) * 255)
                b = int(color.get('b', 0) * 255)
                a = color.get('a', 1.0)
                pos = int(stop.get('position', 0) * 100)
                stop_strs.append(f"rgba({r}, {g}, {b}, {a}) {pos}%")
            if stop_strs:
                return "gradient", f"linear-gradient(90deg, {', '.join(stop_strs)})"
                
    for fill in reversed(fills):
        if not fill.get('visible', True): continue
        if fill.get('type') == 'SOLID':
            color = fill.get('color', {})
            r = int(color.get('r', 0) * 255)
            g = int(color.get('g', 0) * 255)
            b = int(color.get('b', 0) * 255)
            a = fill.get('opacity', color.get('a', 1.0))
            return "solid", f"rgba({r}, {g}, {b}, {a})"
            
    return None, "transparent"

def strip_inline_styles(html_content, css_content):
    """Move all inline style attributes from HTML into the CSS file.
    This ensures no style=\"...\" remains in the HTML output."""
    import re
    extra_css_rules = []
    counter = [0]

    def replace_inline_style(m):
        tag_prefix = m.group(1)   # e.g. '<div '
        style_val = m.group(2)    # e.g. 'background-color: red; padding: 8px;'
        rest = m.group(3)         # rest of tag up to >

        # Check if there's already a class attribute
        class_match = re.search(r'class=["\']([^"\']*)["\']', rest)
        if class_match:
            existing_classes = class_match.group(1).strip()
            counter[0] += 1
            new_class = f'inline-style-{counter[0]}'
            new_classes = f'{existing_classes} {new_class}'
            new_rest = rest[:class_match.start()] + f'class="{new_classes}"' + rest[class_match.end():]
        else:
            counter[0] += 1
            new_class = f'inline-style-{counter[0]}'
            new_rest = f'class="{new_class}" ' + rest

        # Handle background-image specially — keep url(...) intact
        extra_css_rules.append(f'.{new_class} {{ {style_val} }}')
        return tag_prefix + new_rest

    # Match opening tags that have a style attribute
    # Handles both style="..." before and after class
    pattern = re.compile(
        r'(<\w+\s)'
        r'(?:[^>]*?\s)?'
        r'style=["\']([^"\']*)["\']'
        r'([^>]*)'
        r'(?=>)',
        re.DOTALL
    )

    def replacer(m):
        full = m.group(0)
        style_val = m.group(2).strip().rstrip(';')
        if not style_val:
            return full.replace(m.group(0), full[:full.index('style=')] + full[full.index('>', full.index('style=')):]).strip()

        counter[0] += 1
        new_class = f'is-{counter[0]}'
        extra_css_rules.append(f'.{new_class} {{ {style_val}; }}')

        # Remove style attr and add new class
        tag_no_style = re.sub(r'\s*style=["\'][^"\']*["\']', '', full)
        class_m = re.search(r'class=["\']([^"\']*)["\']', tag_no_style)
        if class_m:
            new_tag = tag_no_style[:class_m.start()] + f'class="{class_m.group(1).strip()} {new_class}"' + tag_no_style[class_m.end():]
        else:
            # Insert class right after tag name
            new_tag = re.sub(r'^(<\w+)', rf'\1 class="{new_class}"', tag_no_style)
        return new_tag

    new_html = pattern.sub(replacer, html_content)

    if extra_css_rules:
        css_content = css_content + '\n' + '\n'.join(extra_css_rules)

    return new_html, css_content

def compile_figma_node_to_html_css(design_data, node_id, image_map=None):
    html_snippets = []
    css_rules = []
    
    nodes = design_data.get('nodes', {})
    target_node = nodes.get(node_id, {})
    document = target_node.get('document', {})
    
    if not document:
        return None
        
    def clean_class_name(nid):
        return "fg-" + nid.replace(':', '-').replace(';', '-')

    def compile_node(node, parent=None, is_root=False):
        nid = node.get('id', '')
        ntype = node.get('type', '')
        name = node.get('name', '')
        class_name = clean_class_name(nid)
        
        styles = []
        
        box = node.get('absoluteBoundingBox', {})
        width = box.get('width')
        height = box.get('height')
        
        styles.append("box-sizing: border-box;")
        
        # Corner radius & borders
        if 'cornerRadius' in node:
            styles.append(f"border-radius: {node['cornerRadius']}px;")
        if node.get('strokes'):
            _, border_color = parse_figma_fill(node.get('strokes'), image_map)
            
            # Individual stroke weights in Figma
            indiv_strokes = node.get('individualStrokeWeights')
            if indiv_strokes:
                top = indiv_strokes.get('top', 0)
                right = indiv_strokes.get('right', 0)
                bottom = indiv_strokes.get('bottom', 0)
                left = indiv_strokes.get('left', 0)
                if top > 0:
                    styles.append(f"border-top: {top}px solid {border_color};")
                if right > 0:
                    styles.append(f"border-right: {right}px solid {border_color};")
                if bottom > 0:
                    styles.append(f"border-bottom: {bottom}px solid {border_color};")
                if left > 0:
                    styles.append(f"border-left: {left}px solid {border_color};")
            elif 'strokeWeight' in node and node['strokeWeight'] > 0:
                styles.append(f"border: {node['strokeWeight']}px solid {border_color};")
                
        # Background color or fill (skip for TEXT, as fills represent text color)
        if ntype != 'TEXT':
            fill_type, fill_val = parse_figma_fill(node.get('fills'), image_map)
            if fill_type == 'image':
                styles.append(f"background-image: {fill_val};")
                styles.append("background-size: cover;")
                styles.append("background-position: center;")
            elif fill_type == 'gradient':
                styles.append(f"background: {fill_val};")
            elif fill_val != "transparent":
                styles.append(f"background-color: {fill_val};")
            
        if is_root:
            styles.append("margin: 0 auto;")
            styles.append("position: relative;")
            if width and height:
                styles.append(f"width: {width}px; height: {height}px;")
            else:
                styles.append("width: 100%; min-height: 100vh;")
            
        # Positioning & Layout
        parent_has_layout = False
        if parent:
            parent_has_layout = bool(parent.get('layoutMode') and parent.get('layoutMode') != 'NONE')
            
        is_absolute = False
        if not is_root:
            if not parent_has_layout or node.get('layoutPositioning') == 'ABSOLUTE':
                is_absolute = True
                
        if is_absolute:
            if parent:
                parent_box = parent.get('absoluteBoundingBox', {})
                px = parent_box.get('x', 0)
                py = parent_box.get('y', 0)
                cx = box.get('x', 0)
                cy = box.get('y', 0)
                styles.append("position: absolute;")
                styles.append(f"left: {cx - px}px;")
                styles.append(f"top: {cy - py}px;")
        
        # Flexbox child properties & Sizing
        if not is_absolute and parent_has_layout and not is_root:
            parent_mode = parent.get('layoutMode')
            hz_sizing = node.get('layoutSizingHorizontal')
            vt_sizing = node.get('layoutSizingVertical')
            
            # Infer sizing from legacy layout properties if missing
            if not hz_sizing:
                if parent_mode == 'HORIZONTAL' and node.get('layoutGrow') == 1: hz_sizing = 'FILL'
                elif parent_mode == 'VERTICAL' and node.get('layoutAlign') == 'STRETCH': hz_sizing = 'FILL'
                else: hz_sizing = 'FIXED'
            
            if not vt_sizing:
                if parent_mode == 'VERTICAL' and node.get('layoutGrow') == 1: vt_sizing = 'FILL'
                elif parent_mode == 'HORIZONTAL' and node.get('layoutAlign') == 'STRETCH': vt_sizing = 'FILL'
                else: vt_sizing = 'FIXED'
                
            # Apply flex properties
            if parent_mode == 'HORIZONTAL':
                if hz_sizing == 'FILL': styles.append("flex-grow: 1;")
                if vt_sizing == 'FILL': styles.append("align-self: stretch;")
            elif parent_mode == 'VERTICAL':
                if vt_sizing == 'FILL': styles.append("flex-grow: 1;")
                if hz_sizing == 'FILL': styles.append("align-self: stretch;")
                
            # Apply fixed sizing
            if hz_sizing == 'FIXED' and width is not None: styles.append(f"width: {width}px;")
            elif hz_sizing == 'HUG': styles.append("width: fit-content;")
            
            if vt_sizing == 'FIXED' and height is not None: styles.append(f"height: {height}px;")
            elif vt_sizing == 'HUG': styles.append("height: fit-content;")
        elif not is_root:
            # For absolute or non-layout children
            if width is not None: styles.append(f"width: {width}px;")
            if height is not None: styles.append(f"height: {height}px;")

        if ntype == 'TEXT':
            char_text = node.get('characters', '')
            text_style = node.get('style', {})
            font_family = text_style.get('fontFamily', 'Pretendard')
            font_size = text_style.get('fontSize', 16)
            font_weight = text_style.get('fontWeight', 400)
            line_height = text_style.get('lineHeightPx')
            align_h = text_style.get('textAlignHorizontal', 'LEFT').lower()
            
            styles.append(f"font-family: '{font_family}', sans-serif;")
            styles.append(f"font-size: {font_size}px;")
            styles.append(f"font-weight: {font_weight};")
            if line_height:
                styles.append(f"line-height: {line_height}px;")
            if align_h in ['center', 'right', 'justify']:
                styles.append(f"text-align: {align_h};")
            
            _, text_color = parse_figma_fill(node.get('fills'), image_map)
            if text_color != "transparent":
                styles.append(f"color: {text_color};")

            css_rules.append(f".{class_name} {{ { ' '.join(styles) } }}")
            
            tag = "div"
            if font_size >= 28:
                tag = "h1"
            elif font_size >= 22:
                tag = "h2"
            elif font_size >= 18:
                tag = "h3"
            
            import html
            safe_text = html.escape(char_text).replace('\n', '<br>')
            return f"<{tag} class='{class_name}'>{safe_text}</{tag}>\n"
            
        elif ntype in ['FRAME', 'GROUP', 'COMPONENT', 'INSTANCE']:
            layout_mode = node.get('layoutMode', 'NONE')
            if layout_mode and layout_mode != 'NONE':
                styles.append("display: flex;")
                if layout_mode == 'VERTICAL':
                    styles.append("flex-direction: column;")
                else:
                    styles.append("flex-direction: row;")
                    
                if node.get('layoutWrap') == 'WRAP':
                    styles.append("flex-wrap: wrap;")
                    
                item_spacing = node.get('itemSpacing')
                if item_spacing:
                    styles.append(f"gap: {item_spacing}px;")
                    
                pt = node.get('paddingTop', 0)
                pr = node.get('paddingRight', 0)
                pb = node.get('paddingBottom', 0)
                pl = node.get('paddingLeft', 0)
                if pt or pr or pb or pl:
                    styles.append(f"padding: {pt}px {pr}px {pb}px {pl}px;")
                    
                align_items = node.get('counterAxisAlignItems')
                justify_content = node.get('primaryAxisAlignItems')
                
                align_map = {'MIN': 'flex-start', 'CENTER': 'center', 'MAX': 'flex-end'}
                justify_map = {'MIN': 'flex-start', 'CENTER': 'center', 'MAX': 'flex-end', 'SPACE_BETWEEN': 'space-between'}
                
                if align_items in align_map:
                    styles.append(f"align-items: {align_map[align_items]};")
                if justify_content in justify_map:
                    styles.append(f"justify-content: {justify_map[justify_content]};")
            else:
                if not is_absolute and parent_has_layout:
                    styles.append("position: relative;")
                elif is_root:
                    styles.append("position: relative;")

            # If this node is mapped to an image/icon, output an img tag instead of traversing children
            if nid in (image_map or {}):
                img_src = image_map[nid]
                # Still output css_rules for positioning and layout, but use an img tag
                css_rules.append(f".{class_name} {{ { ' '.join(styles) } }}")
                return f"<img class='{class_name}' src='{img_src}' alt='{name}'>\n"

            css_rules.append(f".{class_name} {{ { ' '.join(styles) } }}")
            
            children_html = ""
            for child in node.get('children', []):
                children_html += compile_node(child, parent=node)
                
            return f"<div class='{class_name}'>\n{children_html}</div>\n"
            
        else:
            styles.append("display: block;")
            if width and (is_absolute or not parent_has_layout or node.get('layoutAlign') != 'STRETCH'):
                styles.append(f"width: {width}px;")
            if height and (is_absolute or not parent_has_layout):
                styles.append(f"height: {height}px;")
            if ntype == 'ELLIPSE':
                styles.append("border-radius: 50%;")
            css_rules.append(f".{class_name} {{ { ' '.join(styles) } }}")
            return f"<div class='{class_name}'></div>\n"

    html_result = compile_node(document, is_root=True)
    css_result = "\n".join(css_rules)
    return html_result, css_result

def parse_folder_slug(param):
    if '--' in param:
        parts = param.split('--', 1)
        return parts[0], parts[1]
    return "", param

def apply_dynamic_css_feedback(css_content, feedback, figma_json=None):
    config = get_config()
    api_key = config.get('gemini_api_key', '').strip()
    
    if not api_key:
        print("No Gemini API key configured. Using fallback regex.")
        import re
        pattern = r'([.#\w\-]+)\s+([\w\-]+)\s*:\s*([^;]+)'
        matches = re.findall(pattern, feedback)
        for selector, prop, val in matches:
            selector = selector.strip()
            prop = prop.strip()
            val = val.strip().rstrip(';')
            
            escaped_selector = re.escape(selector)
            block_pattern = rf'({escaped_selector}\s*\{{[^}}]*\}})'
            block_match = re.search(block_pattern, css_content, re.IGNORECASE)
            if block_match:
                original_block = block_match.group(1)
                prop_pattern = rf'({re.escape(prop)}\s*:\s*[^;}}]+;?)'
                if re.search(prop_pattern, original_block, re.IGNORECASE):
                    new_block = re.sub(prop_pattern, f'{prop}: {val};', original_block, flags=re.IGNORECASE)
                    css_content = css_content.replace(original_block, new_block)
                else:
                    new_block = original_block.replace('}', f'\n    {prop}: {val};\n}}')
                    css_content = css_content.replace(original_block, new_block)
            else:
                css_content += f"\n{selector} {{\n    {prop}: {val};\n}}\n"
        return css_content

    # Use Gemini API
    try:
        from google import genai as _genai
        client = _genai.Client(api_key=api_key)
        
        figma_context = ""
        if figma_json:
            import json
            def simplify_node(node):
                if not isinstance(node, dict): return node
                result = {
                    "n": node.get("name"),
                    "t": node.get("type")
                }
                for key in ['layoutMode', 'layoutSizingHorizontal', 'layoutSizingVertical', 'layoutAlign', 'layoutGrow', 'characters']:
                    if key in node: result[key] = node[key]
                if 'absoluteBoundingBox' in node:
                    result['box'] = node['absoluteBoundingBox']
                if 'children' in node:
                    result['c'] = [simplify_node(c) for c in node['children']]
                return result
            
            simplified = simplify_node(figma_json.get("document", figma_json))
            json_str = json.dumps(simplified, ensure_ascii=False)
            if len(json_str) > 50000: json_str = json_str[:50000] + "...(truncated)"
            figma_context = f"\nHere is the original Figma JSON structure (simplified layout tree):\n```json\n{json_str}\n```\n"

        prompt = f"""
You are an expert frontend developer.
The user has provided a natural language request to modify some CSS.
User Request: {feedback}

{figma_context}
Here is the current CSS:
```css
{css_content}
```

Return ONLY the full updated CSS code. Make sure you apply the requested changes intelligently. 
If the user complains that it doesn't look like the design, rely on your frontend expertise to tweak margins, paddings, fonts, or colors to make it look professional and beautiful.
Do not wrap it in markdown block if it causes extra characters, but if you do, I will strip them. Just return valid CSS.
"""
        response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
        text = response.text.strip()
        
        # Clean up markdown tags if present
        if text.startswith('```css'):
            text = text[6:]
        elif text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
            
        return text.strip()
    except Exception as e:
        print(f"Gemini API error: {e}")
        return css_content

def compare_and_fix_visuals(token, figma_link, html, css, css_links, menu_name, gemini_api_key, task_id=None):
    import urllib.parse, requests, os, json, asyncio
    from playwright.async_api import async_playwright
    from google import genai
    import PIL.Image

    print(f"[{menu_name}] --- Visual Reflection Start ---")
    try:
        parts = figma_link.split('/design/')[1].split('/')
        file_key = parts[0]
        query = urllib.parse.urlparse(figma_link).query
        params = urllib.parse.parse_qs(query)
        node_id = params['node-id'][0].replace('-', ':')
    except Exception as e:
        print(f"[{menu_name}] Error parsing figma link: {e}")
        return html, css

    url = f'https://api.figma.com/v1/images/{file_key}?ids={node_id}&format=png&scale=1'
    headers = {'X-Figma-Token': token}
    r = requests.get(url, headers=headers)
    data = r.json()
    if 'err' in data and data['err']:
        print(f"[{menu_name}] Figma Image Error: {data['err']}")
        return html, css

    img_url = data['images'].get(node_id)
    if not img_url:
        print(f"[{menu_name}] No image returned from Figma.")
        return html, css

    base_dir = os.path.dirname(__file__)
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    target_img_path = os.path.join(output_dir, f'temp_target_{menu_name}.png')
    with open(target_img_path, 'wb') as f:
        f.write(requests.get(img_url).content)

    try:
        target_pil = PIL.Image.open(target_img_path)
    except Exception as e:
        print(f"[{menu_name}] PIL Error: {e}")
        return html, css

    client = genai.Client(api_key=gemini_api_key)
    
    MAX_ITERATIONS = 3
    for iteration in range(1, MAX_ITERATIONS + 1):
        if task_id:
            GENERATE_TASKS[task_id]['message'] = f"Đang kiểm tra giao diện bằng AI (Lần {iteration}/{MAX_ITERATIONS})..."

        temp_html_path = os.path.join(output_dir, f'temp_render_{menu_name}.html')
        css_guide_tags = "".join([f'\n    <link rel="stylesheet" href="{link}">' for link in css_links])
        full_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">{css_guide_tags}
    <link rel="stylesheet" href="style.css">
    <style>
        body {{ margin: 0; padding: 0; }}
        {css}
    </style>
</head>
<body>
    {html}
</body>
</html>"""
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(full_html)

        render_img_path = os.path.join(output_dir, f'temp_render_{menu_name}.png')
        
        async def capture():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                file_url = 'file:///' + temp_html_path.replace('\\', '/')
                await page.goto(file_url)
                await asyncio.sleep(2)
                await page.screenshot(path=render_img_path, full_page=True)
                await browser.close()

        try:
            # Create a new event loop for this thread to run Playwright
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(capture())
            loop.close()
        except Exception as e:
            print(f"[{menu_name}] Playwright Error: {e}")
            return html, css

        try:
            render_pil = PIL.Image.open(render_img_path)
        except Exception as e:
            print(f"[{menu_name}] PIL Error: {e}")
            return html, css

        print(f"[{menu_name}] Sending visual comparison to Gemini (Iteration {iteration})...")
        prompt = f"""Bạn là một chuyên gia Frontend Developer. Nhiệm vụ của bạn là so sánh 2 hình ảnh:
- Hình 1 (Bên trái/Đầu tiên): Thiết kế chuẩn từ Figma.
- Hình 2 (Bên phải/Thứ hai): Kết quả hiển thị của mã HTML/CSS hiện tại.

Hãy quan sát thật kỹ các khác biệt (nếu có) về:
1. Padding, Margin, khoảng cách giữa các phần tử. Bạn PHẢI dùng thước đo bằng mắt thật kỹ để chắc chắn khoảng cách giống hệt 100%, tuyệt đối không được lệch dù chỉ vài pixel.
2. Màu nền, hình nền, đường viền (border).
3. Kích thước và màu font chữ.
4. Vị trí sắp xếp (Flexbox, Grid).

NẾU 2 hình ảnh đã GIỐNG HỆT NHAU 100% (PerfectPixel), hãy trả về JSON với status "PERFECT":
{{
  "status": "PERFECT"
}}

Nếu có SỰ SAI LỆCH (dù là nhỏ nhất), hãy SỬA LẠI mã HTML/CSS hiện tại để nó KHỚP HOÀN TOÀN với Hình 1.
Lưu ý:
- KHÔNG XÓA các thẻ hình ảnh (img, background-image) đang có.
- Vẫn phải giữ nguyên định dạng CSS (mỗi rule 1 dòng, có xuống dòng).

Mã HTML hiện tại:
```html
{html}
```

Mã CSS hiện tại:
```css
{css}
```

Trả về JSON duy nhất chứa "status", "html" và "css". (Nếu status là "PERFECT" thì không cần "html" và "css").
{{
  "status": "FIXED",
  "html": "...",
  "css": "..."
}}"""
        
        try:
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=[prompt, target_pil, render_pil]
            )
            text = response.text.strip()
            if '```json' in text: text = text.split('```json')[1].split('```')[0].strip()
            elif text.startswith('```'): text = text.split('```')[1].split('```')[0].strip()
            
            result = json.loads(text)
            
            if result.get('status') == 'PERFECT':
                print(f"[{menu_name}] Visual match is PERFECT at iteration {iteration}!")
                break
                
            html = result.get('html', html)
            css = result.get('css', css)
            print(f"[{menu_name}] Visual correction applied (Iteration {iteration}).")
            
        except Exception as e:
            print(f"[{menu_name}] Gemini Vision Error: {e}")
            break # Exit loop on API error

    return html, css

GENERATE_TASKS = {}

def run_generate_async(task_id, site_id, menu_param, target_dir, figma_token, config, menu, site, feedback):
    GENERATE_TASKS[task_id] = {"status": "running", "message": "Đang kết nối Figma..."}
    try:
        import time
        time.sleep(2.5) # Giả lập thời gian kết nối
        
        if GENERATE_TASKS.get(task_id, {}).get('status') == 'cancelled':
            return

        folder, menu_slug = parse_folder_slug(menu_param)
        figma_html_css = None
        warning_msg = None
        design_data = None
        
        if menu.get('figma_link'):
            file_key, node_id = parse_figma_url(menu['figma_link'])
            if file_key and node_id:
                design_data = fetch_figma_node(file_key, node_id, figma_token)
                if GENERATE_TASKS.get(task_id, {}).get('status') == 'cancelled': return
                if design_data:
                    nodes = design_data.get('nodes', {})
                    target_node = nodes.get(node_id, {})
                    document = target_node.get('document', {})
                    used_refs = extract_used_image_refs(document) if document else set()
                    
                    GENERATE_TASKS[task_id]['message'] = "Đang tải ảnh từ Figma..."
                    image_map = fetch_figma_images(file_key, figma_token) if figma_token else {}
                    local_image_map = download_and_map_figma_images(image_map, target_dir, menu_slug, used_refs)
                    
                    if figma_token:
                        icon_map = export_figma_icons(file_key, document, figma_token, target_dir, menu_slug)
                        local_image_map.update(icon_map)
                    
                    if GENERATE_TASKS.get(task_id, {}).get('status') == 'cancelled': return
                    
                    GENERATE_TASKS[task_id]['message'] = "Đang biên dịch HTML/CSS..."
                    figma_html_css = compile_figma_node_to_html_css(design_data, node_id, local_image_map)

        if GENERATE_TASKS.get(task_id, {}).get('status') == 'cancelled': return

        if figma_html_css:
            f_html, f_css = figma_html_css
            
            css_guide_raw = site.get('css_guide', '').strip()
            css_links = [link.strip() for link in css_guide_raw.split('\n') if link.strip()]
            
            api_key = config.get('gemini_api_key', '').strip()
            if api_key:
                try:
                    GENERATE_TASKS[task_id]['message'] = "Đang gọi AI Gemini Refactor..."
                    from google import genai as _genai
                    client = _genai.Client(api_key=api_key)
                    
                    structure_template = ''
                    table_template = ''
                    structure_path = os.path.join(app.root_path, 'data', 'ai_templates', 'structure-template.html')
                    table_path = os.path.join(app.root_path, 'data', 'ai_templates', 'table-template.html')
                    if os.path.exists(structure_path):
                        with open(structure_path, 'r', encoding='utf-8') as tf:
                            structure_template = tf.read()
                    if os.path.exists(table_path):
                        with open(table_path, 'r', encoding='utf-8') as tf:
                            table_template = tf.read()

                    css_guide_instruction = f"\n\nQUY TẮC BẮT BUỘC:\n0. TUYỆT ĐỐI KHÔNG dùng thuộc tính style=\"...\" trong HTML. Mọi CSS phải viết trong file CSS, không được để bất kỳ inline style nào trong HTML.\n1. Dự án sử dụng CSS chuẩn tại: " + ", ".join(css_links) + f".\nGIỮ NGUYÊN MÀU NỀN (background-color), màu chữ (color), đường viền (border), bo góc (border-radius) ĐÚNG Y HỆT CSS ĐẦU VÀO TỪ FIGMA — phải viết chúng vào CSS class, không viết inline.\n2. FORMAT CSS: Mỗi rule CSS phải nằm trên 1 dòng riêng biệt, có XUỐNG DÒNG giữa các rule.\n3. BẢO TOÀN HÌNH ẢNH: Giữ chính xác đường dẫn background-image và img src từ HTML/CSS đầu vào. KHÔNG ĐƯỢC xoá ảnh.\n4. SỬ DỤNG ẢNH PNG CHO ICON: Dùng thẻ <img src=\"./images/{menu_slug}/icon_name.png\" alt=\"...\"> cho icon, không dùng span hay font icon." if css_links else f"\n\nQUY TẮC BẮT BUỘC:\n0. TUYỆT ĐỐI KHÔNG dùng style=\"...\" inline trong HTML. Mọi CSS phải viết trong file CSS.\n1. FORMAT CSS: Mỗi rule CSS phải nằm trên 1 dòng riêng biệt.\n2. BẢO TOÀN HÌNH ẢNH: Giữ chính xác đường dẫn ảnh. KHÔNG ĐƯỢC xoá ảnh.\n3. SỬ DỤNG ẢNH PNG CHO ICON: Dùng thẻ <img src=\"./images/{menu_slug}/icon_name.png\"> cho icon."

                    prompt = f"""Bạn là một chuyên gia Frontend Developer.
Người dùng vừa import một thiết kế từ Figma. Mã HTML hiện tại chỉ là các div định vị tuyệt đối không có cấu trúc tốt.
Hãy cấu trúc lại HTML/CSS này sao cho nó tuân thủ CHUẨN CẤU TRÚC SUB-TEMPLATE sau đây:

Mẫu cấu trúc giao diện chung:
```html
{structure_template}
```
Mẫu bảng (nếu có dữ liệu dạng bảng):
```html
{table_template}
```

Mã HTML từ Figma hiện tại:
```html
{f_html}
```

Mã CSS từ Figma hiện tại:
```css
{f_css}
```{css_guide_instruction}

Nhiệm vụ:
1. Đọc và phân tích thiết kế Figma gốc (qua HTML/CSS đầu vào) để tái tạo chính xác layout, màu sắc, font chữ và hình ảnh. BẮT BUỘC phải thiết lập "max-width" cho khối bao ngoài cùng (container tổng) bằng đúng chiều rộng (width) của Frame Figma gốc và căn giữa (margin: 0 auto;). Các kích thước, khoảng cách và màu nền bên trong cũng phải y hệt thiết kế gốc!
2. Nếu thành phần là bảng (table) hoặc đoạn văn bản tiêu chuẩn, hãy áp dụng class từ SUB-TEMPLATE. Nếu là thiết kế đặc thù (khác với template), bạn phải viết HTML/CSS tuỳ chỉnh để GIỮ NGUYÊN GIAO DIỆN Y HỆT THIẾT KẾ GỐC (bao gồm màu nền, viền, font).
3. Mục tiêu: Giao diện cuối cùng phải giống thiết kế Figma 100% về mặt thị giác.
4. QUY TẮC CLASS ĐẶC BIỆT: Thẻ <p> hoặc div (box) nằm ở vị trí CUỐI CÙNG trong một khối (container) bắt buộc phải có thêm class "no-pd" để tránh khoảng trống thừa (giống như trong template). Các đoạn văn bản bắt đầu bằng ký tự "*" hoặc "※" bắt buộc phải dùng thẻ <p class="mark-p">. ĐẶC BIỆT LƯU Ý: Vì CSS của class "mark-p" đã tự động hiển thị dấu "※" (qua pseudo-element ::before), bạn BẮT BUỘC PHẢI XÓA BỎ dấu "*" hoặc "※" đó ra khỏi nội dung HTML (ví dụ: thay vì viết <p class="mark-p">* Ghi chú...</p>, bạn PHẢI viết là <p class="mark-p">Ghi chú...</p>). TUY NHIÊN, đối với TẤT CẢ CÁC THẺ (kể cả mark-p), nếu màu chữ (color), kích thước (font-size) hoặc khoảng cách trên Figma KHÁC với định dạng mặc định của template, bạn PHẢI tạo class riêng hoặc viết thêm rule CSS cho nó vào file .css để ghi đè, đảm bảo nó giống thiết kế Figma 100%.

Trả về JSON chứa "html" và "css" (không bọc trong markdown):
{{
  "html": "toàn bộ nội dung HTML đã tái cấu trúc",
  "css": "toàn bộ CSS đã tái cấu trúc"
}}"""
                    response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    text = response.text.strip()
                    import json as _json
                    if '```json' in text:
                        text = text.split('```json')[1].split('```')[0].strip()
                    elif text.startswith('```'):
                        text = text.split('```')[1].split('```')[0].strip()
                    result = _json.loads(text)
                    f_html = result.get('html', f_html)
                    f_css = result.get('css', f_css)
                    # Post-process: strip any remaining inline styles and move to CSS
                    f_html, f_css = strip_inline_styles(f_html, f_css)
                except Exception as e:
                    print(f"[AI Refactor] Error: {e}")
                    
            if GENERATE_TASKS.get(task_id, {}).get('status') == 'cancelled': return
            
            if menu.get('figma_link'):
                GENERATE_TASKS[task_id] = {"status": "running", "message": "Đang chụp ảnh và so sánh giao diện bằng AI..."}
                f_html, f_css = compare_and_fix_visuals(figma_token, menu['figma_link'], f_html, f_css, css_links, menu['name'], config.get('gemini_api_key', ''), task_id)
                # Gemini might have injected inline styles to fix visuals, so strip them again!
                f_html, f_css = strip_inline_styles(f_html, f_css)

            if GENERATE_TASKS.get(task_id, {}).get('status') == 'cancelled': return

            css_guide_tags = "".join([f'\n    <link rel="stylesheet" href="{link}">' for link in css_links])
            html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{menu['name']} - {site['name']}</title>{css_guide_tags}
    <link rel="stylesheet" href="{menu['slug']}.css">
    <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
</head>
<body>
    {f_html}
</body>
</html>
"""
            css_content = f_css
            js_content = "console.log('Dynamic figma page compiled.');"
        else:
            warning_msg = 'Không thể kết nối đến Figma API hoặc Token không hợp lệ, và không có bản lưu cache cho trang này.'
            html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{menu['name']} - {site['name']}</title>
    <link rel="stylesheet" href="{menu['slug']}.css">
</head>
<body>
    <div class="fallback-error">
        <h2>Không thể tải thiết kế Figma</h2>
        <p>Vui lòng kiểm tra lại Figma Personal Access Token hoặc kết nối mạng.</p>
        <p>Link Figma: <a href="{menu.get('figma_link', '#')}" target="_blank">{menu.get('figma_link', 'Chưa có')}</a></p>
    </div>
</body>
</html>
"""
            css_content = """
body { background-color: #f8fafc; }
.fallback-error {
    font-family: sans-serif;
    text-align: center;
    padding: 50px;
}
"""
            js_content = "console.error('Figma compilation failed.');"

        if not figma_html_css:
            err_detail = 'Không thể kết nối Figma API'
            if not figma_token:
                err_detail = 'Chưa có Figma Token (kiểm tra trang Cài đặt Hệ thống)'
            elif not menu.get('figma_link'):
                err_detail = 'Trang chưa được cấu hình Figma Link'
            elif not design_data:
                err_detail = 'Figma API trả về lỗi hoặc Token không hợp lệ. Xem console Flask để biết chi tiết.'
            else:
                err_detail = 'Bộ biên dịch không đọc được cấu trúc node từ Figma (node rỗng hoặc không hỗ trợ)'
            GENERATE_TASKS[task_id] = {"status": "error", "message": f'Tạo trang thất bại: {err_detail}'}
            return

        GENERATE_TASKS[task_id]['message'] = "Đang lưu files..."

        if feedback:
            css_content = apply_dynamic_css_feedback(css_content, feedback, figma_json=design_data)

        html_content = html_content.replace('href="style.css"', f'href="{menu_slug}.css"')
        html_content = html_content.replace('src="script.js"', f'src="{menu_slug}.js"')

        # Check if CSS has content
        has_css = bool(css_content and css_content.strip())
        
        # Check if JS has content and is not just the default placeholder
        default_placeholders = [
            "console.log('Dynamic figma page compiled.');",
            "console.error('Figma compilation failed.');"
        ]
        has_js = bool(js_content and js_content.strip() and js_content.strip() not in default_placeholders)

        if not has_css:
            # Remove link tag referencing this CSS
            import re
            html_content = re.sub(rf'<link\s+[^>]*href=["\']{re.escape(menu_slug)}\.css["\'][^>]*>', '', html_content)
            html_content = re.sub(rf'<link\s+[^>]*href=["\']style\.css["\'][^>]*>', '', html_content)
            
        if not has_js:
            # Remove script tag referencing this JS
            import re
            html_content = re.sub(rf'<script\s+[^>]*src=["\']{re.escape(menu_slug)}\.js["\'][^>]*>\s*</script>', '', html_content)
            html_content = re.sub(rf'<script\s+[^>]*src=["\']script\.js["\'][^>]*>\s*</script>', '', html_content)

        with open(os.path.join(target_dir, f'{menu_slug}.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        if has_css:
            with open(os.path.join(target_dir, f'{menu_slug}.css'), 'w', encoding='utf-8') as f:
                f.write(css_content)
        else:
            # Clean up existing CSS file if it exists
            try:
                css_file = os.path.join(target_dir, f'{menu_slug}.css')
                if os.path.exists(css_file):
                    os.remove(css_file)
            except Exception:
                pass

        if has_js:
            with open(os.path.join(target_dir, f'{menu_slug}.js'), 'w', encoding='utf-8') as f:
                f.write(js_content)
        else:
            # Clean up existing JS file if it exists
            try:
                js_file = os.path.join(target_dir, f'{menu_slug}.js')
                if os.path.exists(js_file):
                    os.remove(js_file)
            except Exception:
                pass

        sites = load_data()
        updated_site = next((s for s in sites if s['id'] == site_id), None)
        if updated_site:
            updated_menu = next((m for m in updated_site['menus'] if m.get('folder', '') == folder and m['slug'] == menu_slug), None)
            if updated_menu:
                updated_menu['generated'] = True
                save_data(sites)

        GENERATE_TASKS[task_id] = {"status": "success", "message": f'Đã tạo thành công trang "{menu["name"]}"!'}
    except Exception as e:
        GENERATE_TASKS[task_id] = {"status": "error", "message": f'Lỗi hệ thống: {str(e)}'}

@app.route('/site/<site_id>/generate/<menu_param>', methods=['POST'])
def generate_files(site_id, menu_param):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'success': False, 'message': 'Không tìm thấy site!'}), 404

    folder, menu_slug = parse_folder_slug(menu_param)
    menu = next((m for m in site['menus'] if m.get('folder', '') == folder and m['slug'] == menu_slug), None)
    if not menu:
        return jsonify({'success': False, 'message': 'Không tìm thấy trang!'}), 404

    if folder:
        target_dir = os.path.join(OUTPUT_DIR, site_id, folder)
    else:
        target_dir = os.path.join(OUTPUT_DIR, site_id)
    os.makedirs(target_dir, exist_ok=True)
    
    config = get_config()
    figma_token = config.get('figma_token', '').strip()
    feedback = request.args.get('feedback', '').strip()
    
    task_id = f"gen--{site_id}--{folder}--{menu_slug}"
    
    if GENERATE_TASKS.get(task_id, {}).get('status') == 'running':
        return jsonify({'success': False, 'message': 'Trang này đang được biên dịch!'})
        
    thread = threading.Thread(target=run_generate_async, args=(task_id, site_id, menu_param, target_dir, figma_token, config, menu, site, feedback))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'task_id': task_id, 'message': 'Bắt đầu quá trình biên dịch.'})

@app.route('/api/generate_status', methods=['GET'])
def api_generate_status():
    return jsonify(GENERATE_TASKS)

@app.route('/api/generate_cancel/<task_id>', methods=['POST'])
def api_generate_cancel(task_id):
    if task_id in GENERATE_TASKS and GENERATE_TASKS[task_id]['status'] == 'running':
        GENERATE_TASKS[task_id] = {"status": "cancelled", "message": "Quá trình biên dịch đã bị hủy bởi người dùng."}
        return jsonify({'success': True, 'message': 'Đã gửi yêu cầu hủy!'})
    return jsonify({'success': False, 'message': 'Tiến trình không tồn tại hoặc đã kết thúc.'})

@app.route('/preview/<site_id>/<menu_param>/')
def preview_index(site_id, menu_param):
    folder, menu_slug = parse_folder_slug(menu_param)
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    menu_name = menu_slug
    if site:
        menu = next((m for m in site.get('menus', []) if m.get('folder', '') == folder and m['slug'] == menu_slug), None)
        if menu:
            menu_name = menu['name']
    return render_template('preview_frame.html', site_id=site_id, menu_param=menu_param, menu_name=menu_name, site_name=site['name'] if site else site_id)

@app.route('/preview/<site_id>/<menu_param>/raw')
def preview_raw(site_id, menu_param):
    folder, menu_slug = parse_folder_slug(menu_param)
    
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    
    dir_path = os.path.join(OUTPUT_DIR, site_id, folder) if folder else os.path.join(OUTPUT_DIR, site_id)
    html_path = os.path.join(dir_path, f'{menu_slug}.html')
    
    if not os.path.exists(html_path):
        return "File not found", 404
        
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    # Dynamically inject CSS Guide if present and not already in HTML
    if site and site.get('css_guide'):
        css_guide_raw = site['css_guide'].strip()
        css_links = [link.strip() for link in css_guide_raw.split('\n') if link.strip()]
        
        inject_tags = []
        for link in css_links:
            if link not in html_content:
                inject_tags.append(f'\n    <link rel="stylesheet" href="{link}">')
                
        if inject_tags:
            combined_tags = "".join(inject_tags)
            if '</head>' in html_content:
                html_content = html_content.replace('</head>', f'{combined_tags}\n</head>')
            else:
                html_content = f'{combined_tags}\n' + html_content
    
    # Inject cache-buster for local css/js to ensure preview updates instantly
    import time
    t = int(time.time() * 1000)
    html_content = html_content.replace(f'href="{menu_slug}.css"', f'href="{menu_slug}.css?t={t}"')
    html_content = html_content.replace(f'href="style.css"', f'href="style.css?t={t}"')
    html_content = html_content.replace(f'src="{menu_slug}.js"', f'src="{menu_slug}.js?t={t}"')
    html_content = html_content.replace(f'src="script.js"', f'src="script.js?t={t}"')
                
    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/preview/<site_id>/<menu_param>/<path:filename>')
def preview_static(site_id, menu_param, filename):
    folder, menu_slug = parse_folder_slug(menu_param)
    dir_path = os.path.join(OUTPUT_DIR, site_id, folder) if folder else os.path.join(OUTPUT_DIR, site_id)
    # If the request is for style.css or script.js, map to the slug-specific name
    if filename == 'style.css':
        filename = f'{menu_slug}.css'
    elif filename == 'script.js':
        filename = f'{menu_slug}.js'
    response = send_from_directory(dir_path, filename)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/site/<site_id>/edit-menu/<menu_param>', methods=['POST'])
def edit_menu(site_id, menu_param):
    new_name = request.form.get('menu_name', '').strip()
    new_folder = request.form.get('folder', '').strip().strip('/')
    new_slug = request.form.get('menu_slug', '').strip().strip('/')
    new_figma = request.form.get('figma_link', '').strip()
    new_layout = request.form.get('layout', 'sub-template').strip()
    
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Không tìm thấy site!', 'danger')
        return redirect(url_for('index'))
        
    old_folder, old_slug = parse_folder_slug(menu_param)
    menu = next((m for m in site['menus'] if m.get('folder', '') == old_folder and m['slug'] == old_slug), None)
    if not menu:
        flash('Không tìm thấy trang!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))
        
    # Check if folder or slug changed and new composite key is already taken
    if new_slug != old_slug or new_folder != old_folder:
        if any(m.get('folder', '') == new_folder and m['slug'] == new_slug for m in site['menus']):
            flash(f'Đường dẫn thư mục "{new_folder}" và file "{new_slug}" đã tồn tại!', 'danger')
            return redirect(url_for('site_detail', site_id=site_id))
            
        # Move and rename output files if they exist
        if menu.get('generated'):
            old_dir = os.path.join(OUTPUT_DIR, site_id, old_folder)
            new_dir = os.path.join(OUTPUT_DIR, site_id, new_folder)
            
            if old_dir != new_dir:
                os.makedirs(new_dir, exist_ok=True)
                
            for ext in ['.html', '.css', '.js']:
                old_file = os.path.join(old_dir, f"{old_slug}{ext}")
                new_file = os.path.join(new_dir, f"{new_slug}{ext}")
                if os.path.exists(old_file):
                    try:
                        import shutil
                        shutil.move(old_file, new_file)
                    except Exception:
                        pass
            
            # Clean up old directory if empty and not root
            if old_folder and os.path.exists(old_dir) and not os.listdir(old_dir):
                try:
                    os.rmdir(old_dir)
                except Exception:
                    pass
                
    # Update properties
    menu['name'] = new_name
    menu['folder'] = new_folder
    menu['slug'] = new_slug
    menu['figma_link'] = new_figma
    menu['layout'] = new_layout
    
    save_data(sites)
    flash(f'Đã cập nhật trang "{new_name}" thành công!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))

@app.route('/site/<site_id>/delete-menu/<menu_param>', methods=['POST'])
def delete_menu(site_id, menu_param):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Không tìm thấy site!', 'danger')
        return redirect(url_for('index'))
        
    folder, menu_slug = parse_folder_slug(menu_param)
    menu = next((m for m in site['menus'] if m.get('folder', '') == folder and m['slug'] == menu_slug), None)
    if not menu:
        flash('Không tìm thấy trang!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))
        
    site['menus'] = [m for m in site['menus'] if not (m.get('folder', '') == folder and m['slug'] == menu_slug)]
    
    # Delete page files from target dir
    dir_path = os.path.join(OUTPUT_DIR, site_id, folder)
    for ext in ['.html', '.css', '.js']:
        fpath = os.path.join(dir_path, f"{menu_slug}{ext}")
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception:
                pass
                
    # Clean up directory if empty and not root
    if folder and os.path.exists(dir_path) and not os.listdir(dir_path):
        try:
            os.rmdir(dir_path)
        except Exception:
            pass
            
    save_data(sites)
    flash('Đã xóa trang thành công!', 'success')
    return redirect(url_for('site_detail', site_id=site_id))

from automation import run_deploy
import threading

DEPLOY_TASKS = {}

def run_deploy_async(task_id, site_url, site_id, username, password, folder, slug, layout, html_content, css_content, js_content):
    DEPLOY_TASKS[task_id] = {"status": "running"}
    try:
        result = run_deploy(
            site_url=site_url,
            site_id=site_id,
            username=username,
            password=password,
            folder=folder,
            slug=slug,
            layout=layout,
            html_content=html_content,
            css_content=css_content,
            js_content=js_content
        )
        DEPLOY_TASKS[task_id] = {"status": "success" if result.get('success') else "error", "message": result.get('message', '')}
    except Exception as e:
        DEPLOY_TASKS[task_id] = {"status": "error", "message": str(e)}

@app.route('/api/deploy', methods=['POST'])
def api_deploy():
    data = request.json or {}
    site_id = data.get('site_id')
    menu_slug = data.get('menu_slug')
    folder = data.get('folder', '')
    
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'success': False, 'message': 'Không tìm thấy site!'})

    menu = next((m for m in site['menus'] if m.get('folder', '') == folder and m['slug'] == menu_slug), None)
    if not menu:
        return jsonify({'success': False, 'message': 'Không tìm thấy trang!'})
        
    task_id = f"{site_id}--{folder}--{menu_slug}"
    if DEPLOY_TASKS.get(task_id, {}).get('status') == 'running':
        return jsonify({'success': False, 'message': 'Trang này đang được Deploy!'})
        
    # Read generated files — folder may or may not exist
    if folder:
        target_dir = os.path.join(OUTPUT_DIR, site_id, folder)
    else:
        target_dir = os.path.join(OUTPUT_DIR, site_id)
    html_file = os.path.join(target_dir, f"{menu_slug}.html")
    css_file  = os.path.join(target_dir, f"{menu_slug}.css")
    js_file   = os.path.join(target_dir, f"{menu_slug}.js")

    html_content = ""
    css_content  = ""
    js_content   = ""

    if os.path.exists(html_file):
        import re as _re
        with open(html_file, 'r', encoding='utf-8') as f:
            raw_html = f.read()
        # CMS expects only the BODY content, not the full HTML document
        body_match = _re.search(r'<body[^>]*>(.*?)</body>', raw_html, _re.DOTALL | _re.IGNORECASE)
        html_content = body_match.group(1).strip() if body_match else raw_html

    if os.path.exists(css_file):
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()

    if os.path.exists(js_file):
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
            
    # Run playwright automation in background
    thread = threading.Thread(
        target=run_deploy_async,
        args=(task_id, site['url'], site_id, site.get('username', ''), site.get('password', ''), folder, menu_slug, menu.get('layout', 'sub-template'), html_content, css_content, js_content)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Đã bắt đầu deploy ngầm'})

@app.route('/api/deploy_status', methods=['GET'])
def api_deploy_status():
    return jsonify(DEPLOY_TASKS)

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

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json or {}
    user_message = data.get('message', '').strip()
    site_id = data.get('site_id', '').strip()
    menu_param = data.get('menu_param', '').strip()

    if not user_message:
        return jsonify({'success': False, 'reply': 'Vui lòng nhập yêu cầu.'}), 400

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
            'reply': '⚠️ Chưa cấu hình Gemini API Key. Vui lòng vào trang Chi tiết Site và nhập API Key.'
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
        css_guide_instruction = f"\n\nĐẶC BIỆT LƯU Ý VỀ CẤU TRÚC CSS:\n1. Dự án sử dụng CSS chuẩn tại: " + ", ".join(css_links) + ".\nTUYỆT ĐỐI TUÂN THỦ khoảng cách (margin, padding) đã định nghĩa trong guide. Không thêm margin/padding dư thừa làm sai lệch giao diện gốc (ví dụ: nếu guide dùng padding-bottom, đừng thêm margin-bottom).\n2. BẮT BUỘC FORMAT CSS: Mỗi rule CSS (selector + thuộc tính) phải nằm trọn trên 1 dòng riêng biệt và phải có XUỐNG DÒNG (\n) giữa các rule khác nhau. (VD:\n.class1 {{ font-size: 20px; color: #333; }}\n.class2 {{ margin-bottom: 15px; }}\n)\nTuyệt đối không gộp toàn bộ file thành 1 dòng duy nhất, và tuyệt đối KHÔNG xuống dòng bên trong dấu ngoặc nhọn {{}}.\n3. SỬ DỤNG ẢNH PNG CHO ICON: BẮT BUỘC sử dụng thẻ <img> với định dạng PNG (vd: <img src=\"./images/{menu_slug}/icon_name.png\" alt=\"icon\">) cho tất cả các icon thay vì sử dụng thẻ span hay font icon." if css_links else "\n\nĐẶC BIỆT LƯU Ý FORMAT CSS:\nBẮT BUỘC FORMAT CSS: Mỗi rule CSS phải nằm trên 1 dòng riêng biệt và có XUỐNG DÒNG (\n) giữa các rule. (VD:\n.class1 {{ font-size: 20px; }}\n.class2 {{ margin: 0; }}\n)\nTuyệt đối không gộp toàn bộ file thành 1 dòng, và tuyệt đối KHÔNG xuống dòng bên trong ngoặc nhọn {{}}.\n3. SỬ DỤNG ẢNH PNG CHO ICON: BẮT BUỘC sử dụng thẻ <img> định dạng PNG cho tất cả icon."

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

        response = client.models.generate_content(model='gemini-3.1-flash-lite', contents=prompt)
        text = response.text.strip()

        import json as _json
        # Clean markdown code blocks if present
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



if __name__ == '__main__':
    app.run(debug=True, port=5000)
