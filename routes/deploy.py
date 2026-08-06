# Author: sawyer88
# Email: phongnguyen@andvina.com

"""
routes/deploy.py
Blueprint xử lý chức năng Deploy page lên CMS.
"""
import os
import re
import threading

from flask import Blueprint, request, jsonify
from .helpers import load_data, parse_folder_slug, OUTPUT_DIR
from automation import run_deploy
from deployer.deploy import run_full_deploy

deploy_bp = Blueprint('deploy', __name__)

# Task state dictionary (task_id -> status dict)
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
        DEPLOY_TASKS[task_id] = {
            "status": "success" if result.get('success') else "error",
            "message": result.get('message', '')
        }
    except Exception as e:
        DEPLOY_TASKS[task_id] = {"status": "error", "message": str(e)}


@deploy_bp.route('/api/deploy', methods=['POST'])
def api_deploy():
    data = request.json or {}
    site_id = data.get('site_id')
    menu_slug = data.get('menu_slug')
    original_folder = data.get('folder', '').strip()
    folder = original_folder
    if not folder:
        folder = menu_slug

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'success': False, 'message': 'Site not found!'})

    menu = next(
        (m for m in site['menus'] if m.get('slug') == menu_slug),
        None
    )
    if not menu:
        return jsonify({'success': False, 'message': 'Page not found!'})

    task_id = f"{site_id}--{original_folder}--{menu_slug}"
    if DEPLOY_TASKS.get(task_id, {}).get('status') == 'running':
        return jsonify({'success': False, 'message': 'This page is currently being deployed!'})

    # Read generated files
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
        with open(html_file, 'r', encoding='utf-8') as f:
            raw_html = f.read()
        # CMS expects only the BODY content, not the full HTML document
        body_match = re.search(r'<body[^>]*>(.*?)</body>', raw_html, re.DOTALL | re.IGNORECASE)
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
        args=(
            task_id,
            site['url'],
            site_id,
            site.get('username', ''),
            site.get('password', ''),
            folder,
            menu_slug,
            menu.get('layout', 'sub-template'),
            html_content,
            css_content,
            js_content
        )
    )
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'message': 'Background deploy started'})


@deploy_bp.route('/api/deploy_status', methods=['GET'])
def api_deploy_status():
    return jsonify(DEPLOY_TASKS)

def run_deploy_menus_async(task_id, site_url, site_id, site_name, username, password, menus):
    DEPLOY_TASKS[task_id] = {"status": "running", "progress": 0, "message": "Starting deployment..."}
    
    def progress_callback(percent, msg):
        if task_id in DEPLOY_TASKS:
            DEPLOY_TASKS[task_id]["progress"] = percent
            DEPLOY_TASKS[task_id]["message"] = msg

    def is_cancelled():
        return DEPLOY_TASKS.get(task_id, {}).get("status") == "cancelling"

    try:
        result = run_full_deploy(
            site_url=site_url,
            site_id=site_id,
            site_name=site_name,
            username=username,
            password=password,
            menus=menus,
            progress_cb=progress_callback,
            is_cancelled=is_cancelled
        )
        
        if is_cancelled():
            last_msg = DEPLOY_TASKS.get(task_id, {}).get("message", "Unknown stage")
            DEPLOY_TASKS[task_id] = {"status": "cancelled", "message": f"Deployment stopped at [{last_msg}]"}
        else:
            DEPLOY_TASKS[task_id] = {
                "status": "success" if result.get('success') else "error",
                "message": result.get('message', '')
            }
    except Exception as e:
        DEPLOY_TASKS[task_id] = {"status": "error", "message": str(e)}

@deploy_bp.route('/api/deploy_menus', methods=['POST'])
def api_deploy_menus():
    data = request.json or {}
    site_id = data.get('site_id')

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'success': False, 'message': 'Site not found!'})

    menus = site.get('menus', [])
    if not menus:
        return jsonify({'success': False, 'message': 'No menus to deploy!'})

    selected_menus = data.get('selected_menus')
    if selected_menus and isinstance(selected_menus, list):
        required_ids = set(selected_menus)
        menu_dict = {m['id']: m for m in menus}
        
        # Recursively include all ancestors
        added = True
        while added:
            added = False
            for m_id in list(required_ids):
                menu = menu_dict.get(m_id)
                if menu and menu.get('parent_id') and menu['parent_id'] not in required_ids:
                    required_ids.add(menu['parent_id'])
                    added = True
                    
        menus = [m for m in menus if m['id'] in required_ids]
        
        if not menus:
            return jsonify({'success': False, 'message': 'No valid menus selected!'})

    task_id = f"{site_id}--deploy-menus"
    if DEPLOY_TASKS.get(task_id, {}).get('status') == 'running':
        return jsonify({'success': False, 'message': 'Menu deployment is already running!'})

    thread = threading.Thread(
        target=run_deploy_menus_async,
        args=(
            task_id,
            site['url'],
            site_id,
            site.get('name', site_id),
            site.get('username', ''),
            site.get('password', ''),
            menus
        )
    )
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'message': 'Background menu deploy started'})

@deploy_bp.route('/api/deploy_cancel', methods=['POST'])
def api_deploy_cancel():
    data = request.json or {}
    task_id = data.get('task_id')
    if not task_id:
        return jsonify({'success': False, 'message': 'task_id required'})
    
    if task_id in DEPLOY_TASKS and DEPLOY_TASKS[task_id]['status'] == 'running':
        DEPLOY_TASKS[task_id]['status'] = 'cancelling'
        return jsonify({'success': True, 'message': 'Cancellation requested'})
    
    return jsonify({'success': False, 'message': 'Task not running'})
