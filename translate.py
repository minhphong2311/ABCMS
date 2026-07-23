import os

file_path = 'd:/Projects/test04/app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    "Đã xóa site thành công!": "Successfully deleted site!",
    "Không tìm thấy site!": "Site not found!",
    "Không tìm thấy trang!": "Page not found!",
    "Trang này đang được Deploy!": "This page is currently being deployed!",
    "Đã bắt đầu deploy ngầm": "Background deploy started",
    "Vui lòng nhập yêu cầu.": "Please enter a request.",
    "⚠️ Chưa cấu hình Gemini API Key. Vui lòng vào trang Chi tiết Site và nhập API Key.": "⚠️ Gemini API Key not configured. Please go to Site Details and enter the API Key.",
    "Đã xóa trang thành công!": "Successfully deleted page!",
    "Đã cập nhật trang": "Successfully updated page",
    "Đường dẫn thư mục": "Folder path",
    "và file": "and file",
    "đã tồn tại!": "already exists!"
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done translation app.py")
