# ABCMS - CMS Page Deployer & Builder

**ABCMS** là một ứng dụng web và công cụ tự động hóa quy trình triển khai (deploy) giao diện (HTML, CSS, JS) lên hệ thống quản trị nội dung (CMS). 

Ứng dụng giúp lập trình viên kiểm thử, thiết kế và tự động đẩy mã nguồn từ môi trường cục bộ lên hệ thống CMS mà không cần phải sao chép - dán (copy-paste) thủ công thông qua giao diện quản trị phức tạp của CMS.

---

## 🌟 Tính năng chính

1. **Quản lý danh sách Site CMS**:
   - Thêm, sửa, xóa thông tin cấu hình các website mục tiêu (Site ID, Name, URL, Tài khoản/Mật khẩu CMS).
   - Hỗ trợ lưu trữ các hướng dẫn tùy biến CSS (`css_guide`) cho từng site.

2. **Xây dựng & Thiết kế giao diện (Builder)**:
   - Giao diện quản lý menu, trang (pages), và cấu trúc thư mục của dự án trực quan.
   - Hỗ trợ cấu hình các thành phần HTML, CSS và JavaScript riêng biệt cho từng trang hoặc layout.

3. **Tự động hóa triển khai (Automation Deploy with Playwright)**:
   - Đăng nhập tự động vào CMS bằng thông tin tài khoản đã cấu hình.
   - Điều hướng trực tiếp đến trang Quản lý trang (Page Manager).
   - Tự động tạo thư mục mới trên cây thư mục CMS nếu chưa tồn tại.
   - Kiểm tra trang (JSP/HTML) đã tồn tại hay chưa:
     - **Nếu chưa tồn tại**: Tự động tạo mới trang, chọn Layout mẫu và cấu hình tiêu đề/tên tệp tin.
     - **Nếu đã tồn tại**: Chọn trang cần chỉnh sửa và mở trình biên tập (Editor).
   - Tự động điền nội dung HTML, CSS và JS vào các trình biên tập mã nguồn trong CMS (ví dụ: Froala Editor, CodeMirror hoặc Editor tích hợp của hệ thống CMS).
   - Lưu và hoàn tất triển khai hoàn toàn tự động.

---

## 📁 Cấu trúc thư mục dự án

```text
├── app.py                # Server Flask chính, quản lý giao diện web builder cục bộ
├── automation.py         # Kịch bản tự động hóa Playwright đăng nhập và cập nhật code lên CMS
├── check_cms.py          # Script kiểm tra kết nối và cấu trúc DOM của CMS mục tiêu
├── check_folders.py      # Script phụ trợ kiểm tra cấu trúc thư mục
├── inspect_*.py          # Các script debug giao diện, trang, Figma phục vụ phát triển
├── test_deploy.py        # File test tiến trình deploy
├── data/                 # Thư mục chứa cấu hình dữ liệu (sites, config, cache)
│   ├── sites.json        # Danh sách các site CMS được quản lý
│   └── config.json       # Cấu hình cài đặt chung của hệ thống
├── templates/            # Giao diện HTML hiển thị của Flask app (Jinja2 templates)
└── .gitignore            # Cấu hình bỏ qua các file logs, ảnh debug và cache khi đẩy lên Git
```

---

## 🚀 Hướng dẫn cài đặt & Chạy ứng dụng

### 1. Yêu cầu hệ thống
- Python 3.8+
- Node.js (nếu có các tool/plugin hỗ trợ đi kèm)

### 2. Cài đặt các thư viện cần thiết
Mở terminal và chạy lệnh:
```bash
pip install flask playwright asyncio
playwright install chromium
```

### 3. Khởi chạy Web Dashboard Builder cục bộ
Chạy server Flask:
```bash
python app.py
```
Sau đó truy cập trình duyệt tại địa chỉ: [http://localhost:5000](http://localhost:5000)

### 4. Triển khai tự động (Command Line)
Bạn có thể chạy kiểm tra deploy bằng cách chạy trực tiếp các script test:
```bash
python test_deploy.py
```

---

## 🛠️ Công nghệ sử dụng
- **Backend**: Python, Flask (phục vụ giao diện điều khiển).
- **Automation**: Playwright (điều khiển trình duyệt Chromium không đầu / có đầu để tương tác trực tiếp với CMS).
- **Database**: Dạng tệp tin JSON đơn giản lưu trong thư mục `data/` giúp dễ dàng đồng bộ và nhẹ nhàng.
