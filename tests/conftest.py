# tests/conftest.py
import os
import json
import pytest
import tempfile
import shutil
from app import app
import routes.helpers as helpers

@pytest.fixture
def mock_env(tmp_path, monkeypatch):
    """
    Tạo môi trường dữ liệu giả lập (mock) an toàn trong thư mục tmp_path.
    Đảm bảo test không bao giờ chạm vào file data/ hay output/ thật.
    """
    mock_data_dir = tmp_path / "data"
    mock_data_dir.mkdir()
    
    mock_output_dir = tmp_path / "output"
    mock_output_dir.mkdir()
    
    mock_data_file = str(mock_data_dir / "sites.json")
    mock_config_file = str(mock_data_dir / "config.json")
    mock_output_dir_str = str(mock_output_dir)
    
    # Sample initial sites data
    sample_sites = [
        {
            "id": "testsite01",
            "name": "Test Site 01",
            "cms_url": "https://cms.test.com",
            "admin": "admin",
            "password": "pass",
            "css": "",
            "js": "",
            "menus": [
                {
                    "id": "menu-root-1",
                    "name": "Giới thiệu",
                    "slug": "about-us",
                    "parent_id": None,
                    "order": 0,
                    "folder": "about-us"
                },
                {
                    "id": "menu-sub-1",
                    "name": "Lịch sử phát triển",
                    "slug": "history",
                    "parent_id": "menu-root-1",
                    "order": 0,
                    "folder": "about-us"
                },
                {
                    "id": "menu-sub-deep-1",
                    "name": "Các mốc lịch sử",
                    "slug": "milestones",
                    "parent_id": "menu-sub-1",
                    "order": 0,
                    "folder": "about-us"
                }
            ]
        }
    ]
    
    with open(mock_data_file, "w", encoding="utf-8") as f:
        json.dump(sample_sites, f, ensure_ascii=False, indent=2)
        
    sample_config = {
        "slug_method": "none",
        "gemini_api_key": ""
    }
    with open(mock_config_file, "w", encoding="utf-8") as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)
        
    # Monkeypatch helpers and modules
    monkeypatch.setattr(helpers, "DATA_FILE", mock_data_file)
    monkeypatch.setattr(helpers, "CONFIG_FILE", mock_config_file)
    monkeypatch.setattr(helpers, "OUTPUT_DIR", mock_output_dir_str)
    
    import routes.preview as preview_mod
    monkeypatch.setattr(preview_mod, "OUTPUT_DIR", mock_output_dir_str)
    
    import routes.menu as menu_mod
    
    import app as app_mod
    monkeypatch.setattr(app_mod, "OUTPUT_DIR", mock_output_dir_str)

    return {
        "data_file": mock_data_file,
        "config_file": mock_config_file,
        "output_dir": mock_output_dir_str,
        "sites": sample_sites
    }

@pytest.fixture
def client(mock_env):
    """Flask test client fixture with isolated test environment."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
