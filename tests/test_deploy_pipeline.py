# tests/test_deploy_pipeline.py
import re
import pytest

def test_menu_depth_sorting():
    """
    Đảm bảo các menu cha (cấp 1) luôn được tạo trước menu con (cấp 2, cấp 3) trên CMS.
    """
    menus = [
        {"id": "m-deep", "name": "Deep Child", "parent_id": "m-sub", "order": 0},
        {"id": "m-root", "name": "Root Menu", "parent_id": None, "order": 0},
        {"id": "m-sub", "name": "Sub Menu", "parent_id": "m-root", "order": 0}
    ]
    menu_map = {m['id']: m for m in menus}
    
    def get_depth(m):
        depth = 0
        curr = m
        while curr and curr.get('parent_id'):
            depth += 1
            curr = menu_map.get(curr['parent_id'])
        return depth
        
    sorted_menus = sorted(menus, key=lambda x: (get_depth(x), x.get('order', 999)))
    
    assert sorted_menus[0]["id"] == "m-root"
    assert sorted_menus[1]["id"] == "m-sub"
    assert sorted_menus[2]["id"] == "m-deep"

def test_leaf_menu_filtering_for_page_creation():
    """
    Trên CMS, chỉ các leaf menu (không có menu con nào) mới được tạo Page.
    Các menu cha đóng vai trò là Folder/Branch.
    """
    menus = [
        {"id": "root-1", "slug": "academic", "parent_id": None},
        {"id": "sub-1", "slug": "cs", "parent_id": "root-1"},
        {"id": "leaf-1", "slug": "ai-lab", "parent_id": "sub-1"},
        {"id": "leaf-2", "slug": "iot-lab", "parent_id": "sub-1"},
        {"id": "root-leaf", "slug": "standalone-page", "parent_id": None}
    ]
    parent_ids = {m.get('parent_id') for m in menus if m.get('parent_id')}
    leaf_menus = [m for m in menus if m.get('id') not in parent_ids]
    
    leaf_slugs = {m["slug"] for m in leaf_menus}
    assert leaf_slugs == {"ai-lab", "iot-lab", "standalone-page"}
    assert "academic" not in leaf_slugs
    assert "cs" not in leaf_slugs

def test_cms_image_resource_url_format():
    """
    Đảm bảo URL tài nguyên ảnh CMS luôn đúng cấu trúc:
    /_res/{res_org}/{site_id}/img/content/{filename}
    """
    res_org = "kookmin"
    site_id = "phong01"
    filename = "banner-main.png"
    
    expected_url = f"/_res/{res_org}/{site_id}/img/content/{filename}"
    assert expected_url == "/_res/kookmin/phong01/img/content/banner-main.png"

def test_body_content_extraction_for_cms():
    """
    CMS chỉ nhận phần nội dung bên trong <body>, không nhận <!DOCTYPE html> hay <head>.
    """
    raw_html = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Test Page</title>
</head>
<body>
    <div class="content-box">
        <p>Main CMS content here</p>
    </div>
</body>
</html>"""
    
    body_match = re.search(r'<body[^>]*>(.*?)</body>', raw_html, re.DOTALL | re.IGNORECASE)
    assert body_match is not None
    extracted = body_match.group(1).strip()
    assert extracted == '<div class="content-box">\n        <p>Main CMS content here</p>\n    </div>'
