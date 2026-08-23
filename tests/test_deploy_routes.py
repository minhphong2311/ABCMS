# tests/test_deploy_routes.py
import json
import pytest
from routes.deploy import DEPLOY_TASKS

def test_deploy_page_site_not_found(client):
    payload = {
        "site_id": "nonexistent_site",
        "menu_slug": "history"
    }
    response = client.post(
        "/api/deploy",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is False
    assert "Site not found" in data["message"]

def test_deploy_page_menu_not_found(client):
    payload = {
        "site_id": "testsite01",
        "menu_slug": "nonexistent_menu_slug"
    }
    response = client.post(
        "/api/deploy",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is False
    assert "Page not found" in data["message"]

def test_deploy_page_already_running(client):
    task_id = "testsite01--about-us--history"
    DEPLOY_TASKS[task_id] = {"status": "running"}

    payload = {
        "site_id": "testsite01",
        "folder": "about-us",
        "menu_slug": "history"
    }
    response = client.post(
        "/api/deploy",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is False
    assert "currently being deployed" in data["message"]

    # Clean up
    DEPLOY_TASKS.pop(task_id, None)

def test_deploy_menus_selection_ancestor_inclusion(client, monkeypatch):
    """
    Khi chọn 1 menu con ở tầng sâu để deploy (selected_menus),
    hệ thống phải tự động truy hồi và đưa các menu cha, ông vào danh sách deploy.
    """
    captured_menus = []

    def mock_run_deploy_menus_async(task_id, site_url, site_id, site_name, username, password, menus):
        nonlocal captured_menus
        captured_menus = menus

    import routes.deploy as deploy_mod
    monkeypatch.setattr(deploy_mod, "run_deploy_menus_async", mock_run_deploy_menus_async)

    payload = {
        "site_id": "testsite01",
        "selected_menus": ["menu-sub-deep-1"] # Leaf node (Milestones)
    }
    response = client.post(
        "/api/deploy_menus",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

    # Assert that all 3 nodes (menu-root-1, menu-sub-1, menu-sub-deep-1) were included
    included_ids = {m["id"] for m in captured_menus}
    assert "menu-root-1" in included_ids
    assert "menu-sub-1" in included_ids
    assert "menu-sub-deep-1" in included_ids

def test_deploy_status_api(client):
    DEPLOY_TASKS["test_task_01"] = {"status": "running", "progress": 50, "message": "Deploying..."}
    
    response = client.get("/api/deploy_status")
    assert response.status_code == 200
    data = response.get_json()
    assert "test_task_01" in data
    assert data["test_task_01"]["progress"] == 50

    DEPLOY_TASKS.pop("test_task_01", None)

def test_deploy_cancel_api(client):
    task_id = "test_cancel_task"
    DEPLOY_TASKS[task_id] = {"status": "running"}

    response = client.post(
        "/api/deploy_cancel",
        data=json.dumps({"task_id": task_id}),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert DEPLOY_TASKS[task_id]["status"] == "cancelling"

    DEPLOY_TASKS.pop(task_id, None)
