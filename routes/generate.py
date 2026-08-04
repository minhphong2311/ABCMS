# Author: sawyer88
# Email: phongnguyen@andvina.com

"""
routes/generate.py
Blueprint xử lý chức năng Generate page từ Figma.
Bao gồm: Figma utilities, AI visual refinement, và async generation task management.
"""
import os
import json
import threading

from flask import Blueprint, request, jsonify
from .helpers import (
    load_data, save_data, get_config,
    parse_folder_slug, OUTPUT_DIR
)

generate_bp = Blueprint('generate', __name__)

# Task state dictionary (task_id -> status dict)
GENERATE_TASKS = {}


# ---------------------------------------------------------------------------
# Figma utilities
# ---------------------------------------------------------------------------

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
    cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'figma_cache.json')
    if os.path.exists(cache_path):
        try:
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
            return
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
        if not fill.get('visible', True):
            continue
        if fill.get('type') == 'IMAGE':
            ref = fill.get('imageRef')
            url = image_map.get(ref) if image_map else None
            if url:
                return "image", f"url('{url}')"
            return "image", f"url('http://localhost:3845/assets/{ref}.png')"

    for fill in reversed(fills):
        if not fill.get('visible', True):
            continue
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
        if not fill.get('visible', True):
            continue
        if fill.get('type') == 'SOLID':
            color = fill.get('color', {})
            r = int(color.get('r', 0) * 255)
            g = int(color.get('g', 0) * 255)
            b = int(color.get('b', 0) * 255)
            a = fill.get('opacity', color.get('a', 1.0))
            return "solid", f"rgba({r}, {g}, {b}, {a})"

    return None, "transparent"


def strip_inline_styles(html_content, css_content):
    """Move all inline style attributes from HTML into the CSS file."""
    import re
    extra_css_rules = []
    counter = [0]

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

        tag_no_style = re.sub(r'\s*style=["\'][^"\']*["\']', '', full)
        class_m = re.search(r'class=["\']([^"\']*)["\']', tag_no_style)
        if class_m:
            new_tag = tag_no_style[:class_m.start()] + f'class="{class_m.group(1).strip()} {new_class}"' + tag_no_style[class_m.end():]
        else:
            new_tag = re.sub(r'^(<\w+)', rf'\1 class="{new_class}"', tag_no_style)
        return new_tag

    new_html = pattern.sub(replacer, html_content)

    if extra_css_rules:
        css_content = css_content + '\n' + '\n'.join(extra_css_rules)

    return new_html, css_content


def compile_figma_node_to_html_css(design_data, node_id, image_map=None):
    html_snippets = []
    css_rules = []

    nodes = design_data.get('nodes', {}) if isinstance(design_data, dict) else {}
    target_node = (
        nodes.get(node_id) or
        nodes.get(node_id.replace(':', '-')) or
        nodes.get(node_id.replace('-', ':')) or
        (list(nodes.values())[0] if isinstance(nodes, dict) and nodes else {})
    )
    if isinstance(target_node, dict):
        document = target_node.get('document', {})
    else:
        document = {}

    if not document and isinstance(design_data, dict) and 'document' in design_data:
        document = design_data['document']

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

        # Background color or fill (skip for TEXT)
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

            if not hz_sizing:
                if parent_mode == 'HORIZONTAL' and node.get('layoutGrow') == 1:
                    hz_sizing = 'FILL'
                elif parent_mode == 'VERTICAL' and node.get('layoutAlign') == 'STRETCH':
                    hz_sizing = 'FILL'
                else:
                    hz_sizing = 'FIXED'

            if not vt_sizing:
                if parent_mode == 'VERTICAL' and node.get('layoutGrow') == 1:
                    vt_sizing = 'FILL'
                elif parent_mode == 'HORIZONTAL' and node.get('layoutAlign') == 'STRETCH':
                    vt_sizing = 'FILL'
                else:
                    vt_sizing = 'FIXED'

            if parent_mode == 'HORIZONTAL':
                if hz_sizing == 'FILL':
                    styles.append("flex-grow: 1;")
                if vt_sizing == 'FILL':
                    styles.append("align-self: stretch;")
            elif parent_mode == 'VERTICAL':
                if vt_sizing == 'FILL':
                    styles.append("flex-grow: 1;")
                if hz_sizing == 'FILL':
                    styles.append("align-self: stretch;")

            if hz_sizing == 'FIXED' and width is not None:
                styles.append(f"width: {width}px;")
            elif hz_sizing == 'HUG':
                styles.append("width: fit-content;")

            if vt_sizing == 'FIXED' and height is not None:
                styles.append(f"height: {height}px;")
            elif vt_sizing == 'HUG':
                styles.append("height: fit-content;")
        elif not is_root:
            if width is not None:
                styles.append(f"width: {width}px;")
            if height is not None:
                styles.append(f"height: {height}px;")

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

            tag = "p"
            cls_name = "con-p"
            if font_size >= 28:
                tag = "h4"
                cls_name = "h4-tit01"
            elif font_size >= 22:
                tag = "h5"
                cls_name = "h5-tit01"
            elif font_size >= 18:
                tag = "h6"
                cls_name = "h6-tit01"

            import html
            safe_text = html.escape(char_text).replace('\n', '<br>')
            return f"<{tag} class='{cls_name} {class_name}'>{safe_text}</{tag}>\n"

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

            # If this node is mapped to an image/icon, output an img tag
            if nid in (image_map or {}):
                img_src = image_map[nid]
                css_rules.append(f".{class_name} {{ { ' '.join(styles) } }}")
                return f"<img class='{class_name}' src='{img_src}' alt='{name}'>\n"

            css_rules.append(f".{class_name} {{ { ' '.join(styles) } }}")

            children_html = ""
            for child in node.get('children', []):
                children_html += compile_node(child, parent=node)

            wrapper_cls = class_name
            if is_root:
                wrapper_cls = f"content-box {class_name}"
            elif parent and parent.get('is_root'):
                wrapper_cls = f"con-box {class_name}"

            return f"<div class='{wrapper_cls}'>\n{children_html}</div>\n"

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

    raw_html = compile_node(document, is_root=True)
    if 'content-box' not in raw_html:
        html_result = f'<div class="content-box">\n<div class="con-box">\n{raw_html}\n</div>\n</div>'
    else:
        html_result = raw_html

    default_responsive_css = """
.content-box { box-sizing: border-box; width: 100%; max-width: 1096px; margin: 0 auto; padding: 0 20px; position: relative; }
@media screen and (max-width: 1024px) {
    .content-box { padding: 0 20px; }
}
@media screen and (max-width: 768px) {
    .content-box { padding: 0 16px; }
}
"""
    css_result = "\n".join(css_rules) + "\n" + default_responsive_css
    return html_result, css_result


# ---------------------------------------------------------------------------
# AI refinement helpers
# ---------------------------------------------------------------------------

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
            def simplify_node(node):
                if not isinstance(node, dict):
                    return node
                result = {
                    "n": node.get("name"),
                    "t": node.get("type")
                }
                for key in ['layoutMode', 'layoutSizingHorizontal', 'layoutSizingVertical', 'layoutAlign', 'layoutGrow', 'characters']:
                    if key in node:
                        result[key] = node[key]
                if 'absoluteBoundingBox' in node:
                    result['box'] = node['absoluteBoundingBox']
                if 'children' in node:
                    result['c'] = [simplify_node(c) for c in node['children']]
                return result

            simplified = simplify_node(figma_json.get("document", figma_json))
            json_str = json.dumps(simplified, ensure_ascii=False)
            if len(json_str) > 50000:
                json_str = json_str[:50000] + "...(truncated)"
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
        models_to_try = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-3.1-flash-lite', 'gemini-2.0-flash-lite']
        text = None
        for model in models_to_try:
            try:
                print(f"[Gemini] Trying CSS feedback with model {model}...")
                response = client.models.generate_content(model=model, contents=prompt)
                if response and response.text:
                    text = response.text.strip()
                    break
            except Exception as e:
                print(f"[Gemini] CSS feedback model {model} error: {e}")
                import time
                time.sleep(2)

        if not text:
            print("Gemini API call failed for all models.")
            return css_content

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


def apply_structural_templates(html, css, api_key, menu_name, task_id=None):
    print(f"[{menu_name}] --- Structural Refinement Start ---")
    import os
    import json

    structure_template = ''
    table_template = ''
    try:
        base = os.path.dirname(os.path.dirname(__file__))
        structure_path = os.path.join(base, 'assets', 'ai_prompts', 'structure-template.html')
        table_path = os.path.join(base, 'assets', 'ai_prompts', 'table-template.html')
        
        if os.path.exists(structure_path):
            with open(structure_path, 'r', encoding='utf-8') as f:
                structure_template = f.read()
        if os.path.exists(table_path):
            with open(table_path, 'r', encoding='utf-8') as f:
                table_template = f.read()
    except Exception as e:
        print(f"Error loading templates: {e}")

    css_guide_instruction = (
        "\n\nĐẶC BIỆT LƯU Ý VỀ CẤU TRÚC CSS:\n"
        "1. BẮT BUỘC FORMAT CSS: Mỗi rule CSS (selector + thuộc tính) phải nằm trọn trên 1 dòng riêng biệt và phải có XUỐNG DÒNG (\\n) giữa các rule khác nhau. (VD:\n.class1 { font-size: 20px; color: #333; }\n.class2 { margin-bottom: 15px; }\n)\n"
        "Tuyệt đối không gộp toàn bộ file thành 1 dòng duy nhất, và tuyệt đối KHÔNG xuống dòng bên trong dấu ngoặc nhọn {}.\n"
        f"2. SỬ DỤNG ẢNH PNG CHO ICON: BẮT BUỘC sử dụng thẻ <img> với định dạng PNG (vd: <img src=\"./images/{menu_name}/icon_name.png\" alt=\"icon\">) cho tất cả các icon thay vì sử dụng thẻ span hay font icon.\n"
        "3. Tái cấu trúc layout: Dùng Flexbox/Grid thay cho absolute positioning. Bọc toàn bộ nội dung trong `<div class=\"content-box\">`. Các phần tử cha bọc bằng `<div class=\"con-box\">`."
    )

    prompt = f"""Bạn là một chuyên gia Frontend Developer.
Nhiệm vụ của bạn là tái cấu trúc lại đoạn HTML/CSS thô được sinh ra từ Figma (tọa độ absolute) thành một layout chuẩn semantic, responsive, sử dụng Flexbox/Grid, và phải TUYỆT ĐỐI tuân thủ cấu trúc của dự án.

Nội dung HTML thô hiện tại:
```html
{html[:10000]}
```

Nội dung CSS thô hiện tại:
```css
{css[:10000]}
```
{css_guide_instruction}

TÀI LIỆU THAM KHẢO VỀ CẤU TRÚC VÀ SUB-TEMPLATE:
Mẫu cấu trúc giao diện chung (structure-template.html):
```html
{structure_template}
```
Mẫu bảng (table-template.html):
```html
{table_template}
```

Nhiệm vụ:
1. Sắp xếp lại các phần tử HTML sao cho có hệ thống phân cấp rõ ràng (phần tử cha bọc các con, dùng `.content-box`, `.con-box`).
2. Xóa các class `fg-*` mang tính position absolute và đổi thành layout semantic với margin, padding, flex, grid.
3. Chuyển đổi typography thành các class chuẩn: `.h4-tit01`, `.h5-tit01`, `.h6-tit01`, `.con-p`.
4. Trả về JSON chứa HTML và CSS mới.

Trả lời theo định dạng JSON sau (không thêm gì ngoài JSON, không bọc trong markdown):
{{
  "html": "toàn bộ nội dung HTML mới",
  "css": "toàn bộ nội dung CSS mới"
}}"""

    try:
        from google import genai as _genai
        client = _genai.Client(api_key=api_key)
        
        models_to_try = ['gemini-3.5-flash', 'gemini-2.0-flash', 'gemini-flash-latest']
        text = None
        for model in models_to_try:
            try:
                print(f"[{menu_name}] Trying Structural Model {model}...")
                response = client.models.generate_content(model=model, contents=prompt)
                if response and response.text:
                    text = response.text.strip()
                    break
            except Exception as e:
                print(f"[{menu_name}] Model {model} error: {e}")
                import time
                time.sleep(1)
                
        if text:
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif text.startswith('```'):
                text = text.split('```')[1].split('```')[0].strip()
                
            result = json.loads(text)
            
            new_html = result.get('html', html)
            new_css = result.get('css', css)
            print(f"[{menu_name}] Structural Refinement SUCCESS!")
            return new_html, new_css

    except Exception as e:
        print(f"[{menu_name}] Structural Refinement Error: {e}")
        
    return html, css


def compare_and_fix_visuals(token, figma_link, html, css, css_links, menu_name, gemini_api_key, task_id=None):
    import urllib.parse
    import requests
    import asyncio
    from playwright.async_api import async_playwright
    from google import genai
    import PIL.Image
    import threading

    # Thêm Semaphore để giới hạn chỉ 1 request Gemini được chạy tại 1 thời điểm
    if not hasattr(compare_and_fix_visuals, 'api_lock'):
        compare_and_fix_visuals.api_lock = threading.Semaphore(1)

    # Load templates
    structure_template = ''
    table_template = ''
    quality_checklist = ''
    try:
        base = os.path.dirname(os.path.dirname(__file__))
        structure_path = os.path.join(base, 'assets', 'ai_prompts', 'structure-template.html')
        table_path = os.path.join(base, 'assets', 'ai_prompts', 'table-template.html')
        checklist_path = os.path.join(base, 'assets', 'ai_prompts', 'quality-checklist.md')
        
        if os.path.exists(structure_path):
            with open(structure_path, 'r', encoding='utf-8') as f:
                structure_template = f.read()
        if os.path.exists(table_path):
            with open(table_path, 'r', encoding='utf-8') as f:
                table_template = f.read()
        if os.path.exists(checklist_path):
            with open(checklist_path, 'r', encoding='utf-8') as f:
                quality_checklist = f.read()
    except Exception as e:
        print(f"Error loading templates in compare_and_fix_visuals: {e}")

    print(f"[{menu_name}] --- Visual Reflection Start ---")
    try:
        file_key, node_id = parse_figma_url(figma_link)
        if not file_key or not node_id:
            print(f"[{menu_name}] Error parsing figma link: {figma_link}")
            return html, css
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

    base_dir = os.path.dirname(os.path.dirname(__file__))
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
        if task_id and task_id in GENERATE_TASKS:
            GENERATE_TASKS[task_id]['message'] = f"AI Quality Check ({iteration}/{MAX_ITERATIONS})..."

        temp_html_path = os.path.join(output_dir, f'temp_render_{menu_name}.html')
        css_guide_tags = "".join([f'\n    <link rel="stylesheet" href="{link}">' for link in css_links])
        full_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">{css_guide_tags}
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

        config = get_config()
        show_ui = bool(config.get('show_ui', True))
        headless_mode = not show_ui

        async def capture():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless_mode)
                page = await browser.new_page()
                file_url = 'file:///' + temp_html_path.replace('\\', '/')
                await page.goto(file_url)
                import asyncio as _asyncio
                await _asyncio.sleep(2)
                await page.screenshot(path=render_img_path, full_page=True)
                await browser.close()

        try:
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
        prompt = f"""You are an expert Frontend Developer. Perform a strict quality verification comparing the 2 images:
- Image 1: Figma design.
- Image 2: Current HTML/CSS render.

Goal: Ensure 100% visual match between HTML/CSS render and Figma design!

Checklist to strictly enforce:
{quality_checklist}

Template Rules to follow:
1. Do not use absolute positioning classes like `fg-*`.
2. Follow the structure provided in these templates:
   Structure template: {structure_template}
   Table template: {table_template}
3. Maintain all image/background tags.
4. Keep CSS formatting (one rule per line).
5. CRITICAL STRUCTURE RULE: You MUST wrap the entire page content in `<div class="content-box">`. 
6. Inside `.content-box`, group related content into `<div class="con-box">` sections. Headings (`h4`, `h5`, `h6`) and paragraphs (`p`) MUST be placed inside `.con-box` wrappers.
7. CRITICAL CLASS NAMING: You MUST strictly use the exact class names from the structure template (e.g. `h4-tit01`, `h5-tit01`, `h6-tit01 no-pd`, `con-p`). DO NOT invent new classes.
8. CRITICAL RESPONSIVE RULE: Ensure layout is 100% responsive for Desktop, Tablet, and Mobile. Include media queries in CSS. Never leave fixed pixel widths.

CRITICAL INSTRUCTION: Do NOT return "PERFECT" unless you have thoroughly checked ALL 7 checklist steps pixel-by-pixel. If there is ANY difference in layout, fonts, margins, or responsiveness, you MUST return "NEEDS_FIX" and provide the corrected HTML and CSS.

Current HTML:
{html}

Current CSS:
{css}

Return JSON with "status", "html" and "css" (or only "status" if PERFECT).
"""

        try:
            if gemini_api_key == "DEMO_KEY":
                print(f"[{menu_name}] Using DEMO_KEY. Mocking AI response...")
                import time
                time.sleep(3)
                text = '{"status": "SUCCESS", "html": "<div class=\\"content-box\\"><div class=\\"con-box\\"><h4 class=\\"h4-tit01\\">Demo Title</h4><p class=\\"con-p\\">Mock response.</p></div></div>", "css": ".content-box { padding: 20px; }"}'
            else:
                with compare_and_fix_visuals.api_lock:
                    models_to_try = ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-flash-latest', 'gemini-3.5-flash']
                    text = None
                    last_error = None
                    for model in models_to_try:
                        for attempt in range(2):
                            try:
                                print(f"[{menu_name}] Trying Gemini model {model} (Attempt {attempt+1})...")
                                response = client.models.generate_content(
                                    model=model,
                                    contents=[prompt, target_pil, render_pil]
                                )
                                if response and response.text:
                                    text = response.text.strip()
                                    break
                            except Exception as e:
                                last_error = e
                                print(f"[{menu_name}] Model {model} error: {e}")
                                import time
                                time.sleep(2)
                        if text:
                            break
                    if not text and last_error:
                        print(f"[{menu_name}] Warning: Gemini API call failed ({last_error}).")
                        if task_id and task_id in GENERATE_TASKS:
                            GENERATE_TASKS[task_id]['message'] = f"AI Quality Check ({iteration}/3) Failed. Fallback to semantic rules."
                            import time
                            time.sleep(2)
                        break

            if text:
                if '```json' in text:
                    text = text.split('```json')[1].split('```')[0].strip()
                elif text.startswith('```'):
                    text = text.split('```')[1].split('```')[0].strip()

                result = json.loads(text)

                if result.get('status') == 'PERFECT':
                    if iteration < 2:
                        print(f"[{menu_name}] AI claimed PERFECT on iteration {iteration}. Forcing double-check...")
                        if task_id and task_id in GENERATE_TASKS:
                            GENERATE_TASKS[task_id]['message'] = f"AI Quality Check ({iteration}/3): Double-checking for strict adherence..."
                            import time
                            time.sleep(1)
                    else:
                        print(f"[{menu_name}] Visual match is PERFECT at iteration {iteration}!")
                        break

                html = result.get('html', html)
                css = result.get('css', css)
                print(f"[{menu_name}] Visual correction applied (Iteration {iteration}).")

        except Exception as e:
            print(f"[{menu_name}] Gemini Vision Error: {e}")
            break

    return html, css


# ---------------------------------------------------------------------------
# Async generation runner
# ---------------------------------------------------------------------------

def run_generate_async(task_id, site_id, menu_param, target_dir, figma_token, config, menu, site, feedback):
    import shutil
    try:
        GENERATE_TASKS[task_id] = {"status": "running", "message": "Parsing Figma link..."}
        if GENERATE_TASKS.get(task_id, {}).get('status') == 'cancelled':
            return

        folder, menu_slug = parse_folder_slug(menu_param)
        figma_link = menu.get('figma_link', '').strip()
        image_path = menu.get('image_path', '').strip()
        
        html_result = ""
        css_result = ""
        gemini_api_key = config.get('gemini_api_key', '').strip()

        if figma_link:
            file_key, node_id = parse_figma_url(figma_link)
            if not file_key or not node_id:
                raise Exception("Invalid Figma link format.")

            if not figma_token:
                raise Exception("Figma token is missing in settings.")

            GENERATE_TASKS[task_id] = {"status": "running", "message": "Fetching Figma design..."}
            design_data = fetch_figma_node(file_key, node_id, figma_token)
            if not design_data or 'nodes' not in design_data or node_id not in design_data['nodes']:
                raise Exception("Could not fetch design from Figma API.")

            GENERATE_TASKS[task_id] = {"status": "running", "message": "Downloading assets..."}
            document = design_data['nodes'][node_id]['document']
            used_refs = extract_used_image_refs(document)
            image_map = fetch_figma_images(file_key, figma_token)
            local_image_map = download_and_map_figma_images(image_map, target_dir, menu_slug, used_refs)

            # Export icons
            export_figma_icons(file_key, document, figma_token, target_dir, menu_slug)

            GENERATE_TASKS[task_id] = {"status": "running", "message": "Compiling HTML/CSS..."}
            compile_result = compile_figma_node_to_html_css(design_data, node_id, local_image_map)
            if not compile_result:
                raise Exception("Failed to compile HTML/CSS.")
            html_result, css_result = compile_result

            if gemini_api_key:
                GENERATE_TASKS[task_id] = {"status": "running", "message": "Applying structural templates..."}
                html_result, css_result = apply_structural_templates(
                    html_result, css_result, gemini_api_key, menu_slug, task_id
                )

                GENERATE_TASKS[task_id] = {"status": "running", "message": "Refining visuals with AI..."}
                html_result, css_result = compare_and_fix_visuals(
                    figma_token, figma_link, html_result, css_result,
                    [f"{menu_slug}.css"], menu_slug, gemini_api_key, task_id
                )

                if feedback:
                    GENERATE_TASKS[task_id] = {"status": "running", "message": "Applying feedback..."}
                    css_result = apply_dynamic_css_feedback(css_result, feedback)

        elif image_path:
            
            abs_image_path = image_path
            if not os.path.isabs(abs_image_path):
                root_path = os.path.dirname(os.path.dirname(__file__))
                abs_image_path = os.path.join(root_path, abs_image_path)
                
            if not os.path.exists(abs_image_path):
                raise Exception(f"Image file not found on server at {abs_image_path}.")
            if not gemini_api_key:
                raise Exception("Gemini API Key is required for Image-to-HTML generation.")
                
            GENERATE_TASKS[task_id] = {"status": "running", "message": "Uploading image to AI..."}
            from google import genai
            client = genai.Client(api_key=gemini_api_key)
            
            # Copy image to output/images/menu_slug/ for reference if needed
            images_dir = os.path.join(target_dir, "images", menu_slug)
            os.makedirs(images_dir, exist_ok=True)
            ext = os.path.splitext(abs_image_path)[1]
            dest_image_name = f"source_image{ext}"
            dest_image_path = os.path.join(images_dir, dest_image_name)
            shutil.copy(abs_image_path, dest_image_path)
            
            gemini_file = client.files.upload(file=abs_image_path)
            
            GENERATE_TASKS[task_id] = {"status": "running", "message": "Generating HTML/CSS from Image..."}
            
            structure_template = ''
            try:
                base = os.path.dirname(os.path.dirname(__file__))
                structure_path = os.path.join(base, 'assets', 'ai_prompts', 'structure-template.html')
                if os.path.exists(structure_path):
                    with open(structure_path, 'r', encoding='utf-8') as f:
                        structure_template = f.read()
            except Exception: pass
            
            prompt = f"""You are an expert Frontend Developer. 
Your task is to convert this screenshot into responsive HTML and CSS.

CRITICAL STRUCTURE RULES:
1. Wrap the entire page content in `<div class="content-box">`. 
2. Inside `.content-box`, group related sections into `<div class="con-box">`.
3. Use class names from this structure template:
{structure_template}

Return ONLY a valid JSON object matching this schema without markdown formatting:
{{
  "html": "full HTML content inside body",
  "css": "full CSS content, one rule per line"
}}
"""
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=[gemini_file, prompt]
            )
            
            text = response.text.strip()
            if '```json' in text: text = text.split('```json')[1].split('```')[0].strip()
            elif text.startswith('```'): text = text.split('```')[1].split('```')[0].strip()
            
            import json
            result = json.loads(text)
            html_result = result.get('html', '')
            css_result = result.get('css', '')

            # Create a thumbnail from the image
            thumb_path = os.path.join(target_dir, "thumb.jpg")
            if not os.path.exists(thumb_path):
                shutil.copy(abs_image_path, thumb_path)
        else:
            raise Exception("No Figma link or uploaded image found for this page.")

        # Write files
        html_path = os.path.join(target_dir, f"{menu_slug}.html")
        css_path = os.path.join(target_dir, f"{menu_slug}.css")

        base_style_src = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'layout', 'style.css')
        if os.path.exists(base_style_src):
            shutil.copy(base_style_src, os.path.join(target_dir, "style.css"))
            site_root_dir = os.path.join(OUTPUT_DIR, site_id)
            os.makedirs(site_root_dir, exist_ok=True)
            shutil.copy(base_style_src, os.path.join(site_root_dir, "style.css"))

        final_html = (
            f'<!DOCTYPE html>\n<html lang="vi">\n<head>\n'
            f'    <meta charset="UTF-8">\n'
            f'    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f'    <title>{menu.get("name", menu_slug)}</title>\n'
            f'    <link rel="stylesheet" href="style.css">\n'
            f'    <link rel="stylesheet" href="{menu_slug}.css">\n'
            f'</head>\n<body>\n    {html_result}\n</body>\n</html>'
        )

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(final_html)
        with open(css_path, "w", encoding="utf-8") as f:
            f.write(css_result)

        sites = load_data()
        updated_site = next((s for s in sites if s['id'] == site_id), None)
        if updated_site:
            updated_menu = next(
                (m for m in updated_site['menus']
                 if m.get('folder', '') == folder and m['slug'] == menu_slug),
                None
            )
            if updated_menu:
                updated_menu['generated'] = True
                save_data(sites)

        GENERATE_TASKS[task_id] = {
            "status": "success",
            "message": f'Successfully generated page "{menu["name"]}"!'
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        GENERATE_TASKS[task_id] = {"status": "error", "message": f'Generation error: {str(e)}'}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@generate_bp.route('/site/<site_id>/generate/<menu_param>', methods=['POST'])
def generate_files(site_id, menu_param):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'success': False, 'message': 'Site not found!'}), 404

    folder, menu_slug = parse_folder_slug(menu_param)
    menu = next(
        (m for m in site['menus'] if (m.get('folder') or '') == folder and m.get('slug') == menu_slug),
        None
    )
    if not menu:
        return jsonify({'success': False, 'message': 'Page not found!'}), 404

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
        return jsonify({'success': False, 'message': 'Page is currently generating!'})

    thread = threading.Thread(
        target=run_generate_async,
        args=(task_id, site_id, menu_param, target_dir, figma_token, config, menu, site, feedback)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'task_id': task_id, 'message': 'Started generation process.'})


@generate_bp.route('/api/generate_status', methods=['GET'])
def api_generate_status():
    return jsonify(GENERATE_TASKS)


@generate_bp.route('/api/generate_cancel/<task_id>', methods=['POST'])
def api_generate_cancel(task_id):
    if task_id in GENERATE_TASKS and GENERATE_TASKS[task_id]['status'] == 'running':
        GENERATE_TASKS[task_id] = {"status": "cancelled", "message": "Generation cancelled by user."}
        return jsonify({'success': True, 'message': 'Cancellation requested!'})
    return jsonify({'success': False, 'message': 'Task does not exist or already finished.'})
