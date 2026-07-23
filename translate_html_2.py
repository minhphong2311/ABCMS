import glob
import os

replacements = {
    # settings.html
    "Nhấn nút Save Settings bên dưới để ghi đè vào file cấu hình chung trên server.": "Click Save Settings below to overwrite the global configuration file on the server.",
    "Đang lưu...": "Saving...",
    "Đã lưu cấu hình thành công!": "Configuration saved successfully!",
    "Lỗi": "Error",
    "Không thể lưu cấu hình, vui lòng thử lại.": "Cannot save configuration, please try again.",
    
    # site_detail.html
    "Tài khoản CMS:": "CMS Account:",
    "Không cấu hình": "Not configured",
    "Mật khẩu:": "Password:",
    "Nhấp để xem mật khẩu": "Click to view password",
    "Tìm kiếm Trang...": "Search Page...",
    "Quản lý Thư mục": "Manage Folder",
    "Thêm Trang": "Add Page",
    "Tất cả": "All",
    "Thư mục gốc": "Root Folder",
    "Không tìm thấy Trang nào khớp với từ khóa tìm kiếm.": "No Pages match the search keyword.",
    "Đã cấu hình": "Configured",
    "Chưa cấu hình": "Not configured",
    "Chưa tạo Trang": "Page not generated",
    'Nhấn nút "Tạo Trang" bên dưới để biên dịch Figma.': 'Click the "Generate Page" button below to compile Figma.',
    "Vui lòng nhập Figma Link để tạo": "Please enter Figma Link to generate",
    "Tạo Trang": "Generate Page",
    "Vui lòng tạo trang trước": "Please generate page first",
    "Deploy lên CMS": "Deploy to CMS",
    "Edit thông tin Trang": "Edit Page info",
    "Chưa có trang con nào được thiết lập. Nhấp nút \"Add New Page\" để bắt đầu!": "No child pages have been set up. Click \"Add New Page\" to begin!",
    "Thêm trang": "Add Page",
    "Thư mục gốc (Root)": "Root Folder",
    "Example: Giới thiệu": "Example: About Us",
    "sub-template (Trang con thông thường)": "sub-template (Standard inner page)",
    "sub-template-tab (Trang con dạng Tab)": "sub-template-tab (Tabbed inner page)",
    "Dán Link Figma Dev Mode chứa file-key và node-id...": "Paste Figma Dev Mode Link containing file-key and node-id...",
    "Quản lý thư mục": "Manage Folders",
    "New folder name (ví dụ: news)...": "New folder name (e.g., news)...",
    "Viết liền không dấu, không khoảng trắng.": "Write continuously without accents or spaces.",
    "Tên thư mục": "Folder Name",
    "Hành động": "Action",
    "Di chuyển lên": "Move up",
    "Di chuyển xuống": "Move down",
    "Edit tên thư mục": "Edit folder name",
    "Delete thư mục": "Delete folder",
    "Chưa có thư mục con nào được tạo.": "No child folders have been created.",
    "Đang deploy ngầm...": "Deploying in background...",
    "Deploy CMS thành công!": "Successfully deployed to CMS!",
    "Deploy thành công!": "Deploy successful!",
    "Trang ${slug} đã được cập nhật.": "Page ${slug} has been updated.",
    "Lỗi Deploy:": "Deploy Error:",
    "Lỗi Deploy": "Deploy Error",
    "Đang khởi tạo...": "Initializing...",
    "Đang bắt đầu...": "Starting...",
    "Dừng Tạo": "Stop Generation",
    "Lỗi kết nối server": "Server connection error",
    "Lỗi kết nối": "Connection Error",
    "Vui lòng thử lại.": "Please try again.",
    "Đang dừng...": "Stopping...",
    "Đang tạo...": "Generating...",
    "Đã hủy": "Cancelled",
    "Đang khởi tạo tiến trình deploy...": "Initializing deploy process...",
    "Lỗi kết nối khi Deploy": "Connection error during Deploy",
    "Không thể gọi API Deploy. Vui lòng thử lại.": "Cannot call Deploy API. Please try again.",
    "Xác nhận xóa Trang?": "Confirm Delete Page?",
    "Bạn có chắc chắn muốn xóa trang con này? Tất cả code đã sinh tương ứng cũng sẽ bị xóa sạch.": "Are you sure you want to delete this child page? All corresponding generated code will also be completely deleted.",
    "Đổi tên thư mục": "Rename Folder",
    "Save thay đổi": "Save changes",
    "Tên thư mục không được để trống!": "Folder name cannot be empty!",
    "Tên thư mục viết liền không dấu, không chứa ký tự đặc biệt!": "Folder name must be continuous without accents or special characters!",
    "Xác nhận xóa thư mục": "Confirm delete folder",
    "Các trang con bên trong thư mục này sẽ tự động được di chuyển về Thư mục gốc (Root) và các file code tương ứng sẽ được chuyển ra ngoài.": "Child pages inside this folder will automatically be moved to the Root Folder and corresponding code files will be moved out."
}

for filepath in glob.glob('d:/Projects/test04/templates/*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for k, v in replacements.items():
        content = content.replace(k, v)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("HTML translations completed.")
