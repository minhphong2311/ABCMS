# tests/test_helpers_tree.py
import pytest
from routes.helpers import assign_folders_from_roots

def test_assign_folders_flat_menus():
    menus = [
        {"id": "m1", "slug": "home", "parent_id": None},
        {"id": "m2", "slug": "contact", "parent_id": None}
    ]
    assign_folders_from_roots(menus)
    # Root menus should have folder equal to their own slug
    assert menus[0]["folder"] == "home"
    assert menus[1]["folder"] == "contact"

def test_assign_folders_hierarchical_rule_7():
    """
    Quy tắc 7: Khi tính toán folder của một trang con, luôn truy hồi lên nhánh cấp cao nhất
    (root ancestor) để lấy slug của nhánh đó làm folder cho toàn bộ nhánh con,
    dù trang có nằm ở độ sâu bao nhiêu đi chăng nữa.
    """
    menus = [
        # Level 1 (Root)
        {"id": "root-1", "slug": "academic", "parent_id": None},
        # Level 2
        {"id": "sub-1", "slug": "computer-science", "parent_id": "root-1"},
        # Level 3 (Deep nested)
        {"id": "deep-1", "slug": "artificial-intelligence", "parent_id": "sub-1"},
        # Level 4 (Ultra deep nested)
        {"id": "ultra-1", "slug": "lab-robotics", "parent_id": "deep-1"}
    ]
    assign_folders_from_roots(menus)
    
    # Root menu gets its own slug as folder
    assert menus[0]["folder"] == "academic"
    # All children and descendants MUST inherit the ROOT slug 'academic', NOT parent slug
    assert menus[1]["folder"] == "academic"
    assert menus[2]["folder"] == "academic"
    assert menus[3]["folder"] == "academic"

def test_assign_folders_multiple_roots():
    menus = [
        {"id": "r1", "slug": "news", "parent_id": None},
        {"id": "c1", "slug": "events", "parent_id": "r1"},
        {"id": "r2", "slug": "about", "parent_id": None},
        {"id": "c2", "slug": "vision", "parent_id": "r2"},
        {"id": "c3", "slug": "mission", "parent_id": "c2"}
    ]
    assign_folders_from_roots(menus)
    
    assert menus[0]["folder"] == "news"
    assert menus[1]["folder"] == "news"
    assert menus[2]["folder"] == "about"
    assert menus[3]["folder"] == "about"
    assert menus[4]["folder"] == "about"

def test_assign_folders_empty_list():
    menus = []
    assign_folders_from_roots(menus)
    assert menus == []
