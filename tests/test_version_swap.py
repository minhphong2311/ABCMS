# tests/test_version_swap.py
import os
import json
import pytest

def test_undo_changes_no_backup(client):
    payload = {
        "site_id": "testsite01",
        "menu_param": "about-us--history"
    }
    response = client.post(
        "/api/rollback",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is False
    assert "No backup found" in data["message"]

def test_undo_and_redo_toggle_flow(client, mock_env):
    """
    Quy tắc 10: Test kiến trúc hoán đổi phiên bản (.temp swap).
    Khi save 2 lần, file .bak sẽ được tạo.
    Gọi /api/rollback sẽ tráo đổi qua lại giữa Version Cũ (v1) và Version Mới (v2).
    """
    site_id = "testsite01"
    folder = "about-us"
    slug = "history"
    menu_param = f"{folder}--{slug}"
    output_dir = mock_env["output_dir"]
    target_dir = os.path.join(output_dir, site_id, folder)
    os.makedirs(target_dir, exist_ok=True)

    # 1. Save initial Version 1
    v1_payload = {
        "site_id": site_id,
        "folder": folder,
        "slug": slug,
        "html": "<p>Version 1 Initial Content</p>",
        "css": "/* V1 CSS */",
        "js": "// V1 JS"
    }
    client.post("/api/save-code", data=json.dumps(v1_payload), content_type="application/json")

    # 2. Save new Version 2 (this creates .bak with Version 1 content)
    v2_payload = {
        "site_id": site_id,
        "folder": folder,
        "slug": slug,
        "html": "<p>Version 2 AI Updated Content</p>",
        "css": "/* V2 CSS */",
        "js": "// V2 JS"
    }
    client.post("/api/save-code", data=json.dumps(v2_payload), content_type="application/json")

    # Verify current code is Version 2
    code_res = client.get(f"/api/get-code?site_id={site_id}&folder={folder}&slug={slug}")
    assert "Version 2 AI Updated Content" in code_res.get_json()["html"]

    # 3. Trigger Undo (Should swap to Version 1)
    undo_res = client.post(
        "/api/rollback",
        data=json.dumps({"site_id": site_id, "menu_param": menu_param}),
        content_type="application/json"
    )
    assert undo_res.status_code == 200
    assert undo_res.get_json()["success"] is True

    # Verify active code is now Version 1
    code_res_after_undo = client.get(f"/api/get-code?site_id={site_id}&folder={folder}&slug={slug}")
    assert "Version 1 Initial Content" in code_res_after_undo.get_json()["html"]

    # 4. Trigger Redo (Calling rollback again swaps back to Version 2)
    redo_res = client.post(
        "/api/rollback",
        data=json.dumps({"site_id": site_id, "menu_param": menu_param}),
        content_type="application/json"
    )
    assert redo_res.status_code == 200
    assert redo_res.get_json()["success"] is True

    # Verify active code is back to Version 2
    code_res_after_redo = client.get(f"/api/get-code?site_id={site_id}&folder={folder}&slug={slug}")
    assert "Version 2 AI Updated Content" in code_res_after_redo.get_json()["html"]
