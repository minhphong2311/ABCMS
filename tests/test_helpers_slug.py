# tests/test_helpers_slug.py
import pytest
from routes.helpers import make_unique_slug, parse_folder_slug, generate_slug_for_text

def test_make_unique_slug_no_collision():
    existing = ["home", "about", "contact"]
    result = make_unique_slug("services", existing)
    assert result == "services"

def test_make_unique_slug_with_single_collision():
    existing = ["home", "about", "services"]
    result = make_unique_slug("services", existing)
    assert result == "services-2"

def test_make_unique_slug_with_multiple_collisions():
    existing = ["news", "news-2", "news-3"]
    result = make_unique_slug("news", existing)
    assert result == "news-4"

def test_parse_folder_slug_with_folder():
    folder, slug = parse_folder_slug("about-us--history")
    assert folder == "about-us"
    assert slug == "history"

def test_parse_folder_slug_without_folder():
    folder, slug = parse_folder_slug("contact")
    assert folder == ""
    assert slug == "contact"

def test_generate_slug_for_text_fallback(mock_env):
    # In mock_env, slug_method is 'none', should use slugify
    slug = generate_slug_for_text("Giới Thiệu Doanh Nghiệp")
    assert slug == "gioi-thieu-doanh-nghiep"

def test_generate_slug_for_empty_text():
    assert generate_slug_for_text("") == ""
    assert generate_slug_for_text(None) == ""
