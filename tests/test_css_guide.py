# tests/test_css_guide.py
from routes.helpers import get_css_guide_instruction

def test_get_css_guide_instruction_without_links():
    guide = get_css_guide_instruction()
    assert "ĐẶC BIỆT LƯU Ý VỀ CẤU TRÚC VÀ FORMAT CSS" in guide
    assert "BẮT BUỘC FORMAT CSS" in guide
    assert "RESPONSIVE DESIGN LÀ BẮT BUỘC" in guide
    assert "Dự án sử dụng CSS chuẩn tại" not in guide

def test_get_css_guide_instruction_with_links():
    links = ["/css/main.css", "/css/layout.css"]
    guide = get_css_guide_instruction(links)
    assert "Dự án sử dụng CSS chuẩn tại: /css/main.css, /css/layout.css" in guide
    assert "BẮT BUỘC FORMAT CSS" in guide
