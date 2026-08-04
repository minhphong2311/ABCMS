# Author: sawyer88
# Email: phongnguyen@andvina.com

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

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
    generate_slug_for_text,
    parse_folder_slug,
    OUTPUT_DIR
)

# ---------------------------------------------------------------------------
# Register Blueprints
# ---------------------------------------------------------------------------

from routes.generate import generate_bp
from routes.preview import preview_bp
from routes.deploy import deploy_bp
from routes.edit import edit_bp
from routes.delete import delete_bp
from routes.menu import menu_bp

app.register_blueprint(generate_bp)
app.register_blueprint(preview_bp)
app.register_blueprint(deploy_bp)
app.register_blueprint(edit_bp)
app.register_blueprint(delete_bp)
app.register_blueprint(menu_bp)

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


# ---------------------------------------------------------------------------
# Config API
# ---------------------------------------------------------------------------

@app.route('/api/config', methods=['GET'])
def api_get_config():
    config = get_config()
    return jsonify({
        'success': True,
        'gemini_api_key': config.get('gemini_api_key', ''),
        'figma_token': config.get('figma_token', ''),
        'show_ui': config.get('show_ui', True),
        'slug_method': config.get('slug_method', 'google')
    })


@app.route('/api/config', methods=['POST'])
def api_save_config():
    data = request.json or {}
    config = get_config()
    if 'gemini_api_key' in data:
        config['gemini_api_key'] = data['gemini_api_key']
    if 'figma_token' in data:
        config['figma_token'] = data['figma_token']
    if 'show_ui' in data:
        config['show_ui'] = bool(data['show_ui'])
    if 'slug_method' in data:
        config['slug_method'] = data['slug_method']
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
    structure_path = os.path.join(app.root_path, 'assets', 'ai_prompts', 'structure-template.html')
    table_path = os.path.join(app.root_path, 'assets', 'ai_prompts', 'table-template.html')

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
