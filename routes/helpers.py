# Author: sawyer88
# Email: phongnguyen@andvina.com

"""
routes/helpers.py
Shared utilities dùng chung cho toàn bộ app.
"""
import os
import json
import uuid
import time

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sites.json')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'config.json')


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            sites = json.load(f)
            # Migration to hierarchical menus
            needs_save = False
            for site in sites:
                if 'menus' in site:
                    for idx, menu in enumerate(site['menus']):
                        if 'id' not in menu:
                            menu['id'] = str(uuid.uuid4())
                            needs_save = True
                        if 'parent_id' not in menu:
                            menu['parent_id'] = None
                            needs_save = True
                        if 'order' not in menu:
                            menu['order'] = idx
                            needs_save = True

            if needs_save:
                with open(DATA_FILE, 'w', encoding='utf-8') as f_out:
                    json.dump(sites, f_out, ensure_ascii=False, indent=4)

            return sites
    except Exception:
        return []


def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

def make_unique_slug(slug, existing_slugs):
    new_slug = slug
    counter = 2
    while new_slug in existing_slugs:
        new_slug = f"{slug}-{counter}"
        counter += 1
    return new_slug


def generate_slug_for_text(text):
    if not text:
        return ''
    
    config = get_config()
    slug_method = config.get('slug_method', 'google')
    
    try:
        from slugify import slugify
        
        if slug_method == 'google':
            from deep_translator import GoogleTranslator
            # Dịch ngôn ngữ đầu vào (Hàn/Việt...) sang tiếng Anh bằng deep-translator
            translated = GoogleTranslator(source='auto', target='en').translate(text)
            
            # Google Translate web endpoint đôi khi trả về trang lỗi 500 nếu bị rate limit
            if translated and ('500 server error' in translated.lower() or 'that\'s an error' in translated.lower() or 'that’s an error' in translated.lower()):
                print("Google Translate bị lỗi 500, tự động fallback về bỏ dấu.")
                slug = slugify(text)
            else:
                slug = slugify(translated)
            
        elif slug_method == 'gemini':
            # Dùng Gemini API
            api_key = config.get('gemini_api_key', '').strip()
            if not api_key:
                slug = slugify(text)  # Fallback
            else:
                from google import genai
                import re
                client = genai.Client(api_key=api_key)
                prompt = f'''Translate this EXACTLY to a short URL slug (lowercase english words, hyphen separated).
Output ONLY the slug, nothing else. No explanations, no markdown, no punctuation.
Examples:
- 부동산AI융합학과 -> real-estate-ai
- 회사 소개 -> about-us
- 학과/학생활동 -> student-activities
Input: {text}
Output:'''
                response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
                slug_raw = response.text.strip().lower()
                slug_raw = slug_raw.split('\n')[0].strip()
                slug = re.sub(r'[^a-z0-9\-]+', '', slug_raw)
                
        else: # 'none'
            # Chỉ loại bỏ dấu, không dịch (ví dụ: Giới Thiệu -> gioi-thieu)
            slug = slugify(text)
        
        if not slug:
            import urllib.parse
            return urllib.parse.quote(text).lower()
        return slug
    except Exception as e:
        print('Error auto generating slug:', e)
        import urllib.parse
        return urllib.parse.quote(text).lower()


# ---------------------------------------------------------------------------
# URL / path helpers
# ---------------------------------------------------------------------------

def parse_folder_slug(param):
    """Parse a menu_param string into (folder, slug) tuple.

    Format: 'folder--slug' or just 'slug'
    """
    if '--' in param:
        parts = param.split('--', 1)
        return parts[0], parts[1]
    return "", param


# ---------------------------------------------------------------------------
# File cleanup
# ---------------------------------------------------------------------------

def delete_menu_files(site_id, menu_param):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, 'output', site_id)
    if not os.path.exists(output_dir):
        output_dir = os.path.join(base_dir, 'output')

    files_to_delete = [
        f'temp_render_{menu_param}.html',
        f'temp_render_{menu_param}.png',
        f'temp_target_{menu_param}.png'
    ]
    for f in files_to_delete:
        path1 = os.path.join(output_dir, f)
        if os.path.exists(path1):
            try:
                os.remove(path1)
                print(f"Deleted {path1}")
            except Exception as e:
                print(f"Failed to delete {path1}: {e}")

        path2 = os.path.join(base_dir, 'output', site_id, f)
        if os.path.exists(path2):
            try:
                os.remove(path2)
                print(f"Deleted {path2}")
            except Exception:
                pass

    # Also delete generated code files (.html, .css, .js)
    folder, slug = parse_folder_slug(menu_param)

    if folder:
        target_dir = os.path.join(base_dir, 'output', site_id, folder)
    else:
        target_dir = os.path.join(base_dir, 'output', site_id)

    code_files = [f'{slug}.html', f'{slug}.css', f'{slug}.js']
    for f in code_files:
        p = os.path.join(target_dir, f)
        if os.path.exists(p):
            try:
                os.remove(p)
                print(f"Deleted {p}")
            except Exception:
                pass

    # If this menu itself was a root folder, delete its folder directory
    folder_dir = os.path.join(base_dir, 'output', site_id, slug)
    if os.path.isdir(folder_dir):
        import shutil
        try:
            shutil.rmtree(folder_dir)
            print(f"Deleted folder {folder_dir}")
        except Exception as e:
            print(f"Failed to delete folder {folder_dir}: {e}")


# ---------------------------------------------------------------------------
# Menu tree helpers
# ---------------------------------------------------------------------------

def assign_folders_from_roots(menus):
    """Assign the 'folder' field for every menu based on its root ancestor's slug.

    Root menus (parent_id is None) will be treated as folders.
    All descendants of a root menu will inherit that root's slug as their folder.
    """
    # Build id → menu map
    menu_map = {m['id']: m for m in menus if 'id' in m}

    # Find root menus (no parent)
    def get_root_slug(menu_id):
        m = menu_map.get(menu_id)
        if not m:
            return ''
        if not m.get('parent_id'):
            return m.get('slug', '')
        return get_root_slug(m['parent_id'])

    for m in menus:
        m['folder'] = get_root_slug(m['id'])
