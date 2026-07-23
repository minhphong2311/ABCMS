import os
import glob

replacements = {
    "Danh sách Site": "Site List",
    "Tìm kiếm Site theo tên hoặc ID...": "Search Site by name or ID...",
    "Thêm Site": "Add Site",
    "Tổng số trang": "Total Pages",
    "Hoàn thành": "Complete",
    "Đã tạo files": "Files generated",
    "Chưa tạo files": "Files not generated",
    "Quản lý Site / Thiết lập Menu": "Manage Site / Setup Menu",
    "Truy cập trang chủ Site": "Visit Site Homepage",
    "Sửa thông tin Site": "Edit Site Info",
    "Xóa Site": "Delete Site",
    "Chưa có site nào được tạo. Hãy thêm site mới ở trên!": "No sites created yet. Please add a new site above!",
    "Không tìm thấy Site nào khớp với từ khóa tìm kiếm.": "No sites match the search keyword.",
    "Thêm site": "Add Site",
    "Ví dụ:": "Example:",
    "Tên Site": "Site Name",
    "Nhập tên site": "Enter site name",
    "Tên miền / URL": "Domain / URL",
    "Nhập URL": "Enter URL",
    "Tài khoản Admin": "Admin Username",
    "Mật khẩu Admin": "Admin Password",
    "CSS Guide (Các link CSS chuẩn, mỗi link 1 dòng)": "CSS Guide (Standard CSS links, one per line)",
    "Đóng": "Close",
    "Lưu lại": "Save changes",
    "Cập nhật site": "Update Site",
    "Cập nhật": "Update",
    "Chắc chắn xóa site này?": "Are you sure you want to delete this site?",
    "Mọi dữ liệu của site này sẽ bị xóa vĩnh viễn!": "All data of this site will be permanently deleted!",
    "Đồng ý xóa": "Yes, delete it!",
    "Hủy": "Cancel",
    "Chi tiết Site": "Site Details",
    "Quản lý thư mục và menu cho site": "Manage folders and menus for site",
    "Cấu hình Figma Token": "Configure Figma Token",
    "Lưu Token": "Save Token",
    "Thêm Thư Mục Mới": "Add New Folder",
    "Thêm Thư Mục": "Add Folder",
    "Nhập tên thư mục mới...": "Enter new folder name...",
    "Tạo Thư Mục": "Create Folder",
    "Xóa Thư Mục": "Delete Folder",
    "Đổi tên Thư Mục": "Rename Folder",
    "Tên thư mục mới": "New folder name",
    "Xóa thư mục này?": "Delete this folder?",
    "Xóa thư mục sẽ đẩy các menu con ra ngoài thư mục gốc.": "Deleting the folder will move child menus to the root.",
    "Thêm Trang Mới": "Add New Page",
    "Mã (Slug)": "Code (Slug)",
    "Ví dụ: sub01": "Example: sub01",
    "Tên Menu": "Menu Name",
    "Link Figma (URL của node/frame)": "Figma Link (URL of node/frame)",
    "Chưa có Figma Link": "No Figma Link",
    "Thêm Menu": "Add Menu",
    "Đã lưu files": "Files saved",
    "Chưa có files": "No files",
    "Biên dịch (Figma -> HTML)": "Compile (Figma -> HTML)",
    "Hủy biên dịch": "Cancel compilation",
    "Xem trước": "Preview",
    "Sửa": "Edit",
    "Xóa": "Delete",
    "Biên dịch trang": "Compile page",
    "Deploy trang": "Deploy page",
    "Chưa có menu nào.": "No menus available.",
    "Bắt đầu biên dịch": "Start compiling",
    "Đang biên dịch...": "Compiling...",
    "Thành công": "Success",
    "Cài đặt hệ thống": "System Settings",
    "Gemini API Key": "Gemini API Key",
    "Lưu Cài Đặt": "Save Settings",
    "Trang chủ": "Home"
}

for filepath in glob.glob('d:/Projects/test04/templates/*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for k, v in replacements.items():
        content = content.replace(k, v)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Done translating templates.")
