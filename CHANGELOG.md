# Lịch sử Cập nhật Dự án (Changelog)

File này lưu trữ những thay đổi lớn về mặt kiến trúc, tính năng và quy tắc của hệ thống ABCMS, giúp bất kỳ lập trình viên nào tham gia dự án cũng có thể nắm bắt được tiến độ phát triển.

## [2026-08-10] Nâng cấp Kiến trúc Giao diện Chat & Lõi AI

### Tính năng mới (Features)
- **Kiến trúc Undo/Redo Version:** Triển khai tính năng chuyển đổi (Toggle) giữa 2 phiên bản mã nguồn (Cũ/Mới) ngay trên giao diện Preview. Sử dụng kiến trúc tráo đổi file tạm (`.temp` và `.bak`) ở backend (`app.py`), loại bỏ hoàn toàn sự phụ thuộc vào Database giúp hệ thống tối giản.
- **Tối ưu hóa AI Prompt:** Hệ thống AI (Design Critic Agent) được nâng cấp khả năng nhận diện ngôn ngữ và giao tiếp súc tích. Bắt buộc phản hồi bằng ngôn ngữ của người dùng (Tiếng Việt/Tiếng Anh) trong độ dài tối đa 1-2 câu thay vì giải thích rườm rà.

### Cải thiện UI/UX (Refactor & Style)
- **Giao diện nút Undo/Redo:** Chuyển đổi liên kết Undo đơn giản thành cụm nút điều hướng `< Undo | Redo >` chuyên nghiệp. Cập nhật logic vô hiệu hóa (disabled) nút bấm theo trạng thái phiên bản hiện tại.
- **Refactor CSS Clean Code:** Quét và loại bỏ toàn bộ các thuộc tính `style="..."` (Inline style) lộn xộn trong `preview_frame.html`. Toàn bộ giao diện được chuẩn hóa thành các Class CSS riêng biệt (`.brand-text-gradient`, `.ref-design-box`, `.chat-img-preview-container`, v.v...).
- **Cải thiện Dark Mode:** Tinh chỉnh độ tương phản, đổi màu chữ và nền của khối Reference Design trong chế độ ban đêm (Dark Mode) để bảo vệ mắt và tăng tính thẩm mỹ.

### Quy tắc hệ thống (Agents Rules)
- Cập nhật thêm 3 quy tắc mới (Rule 10, 11, 12) vào bộ nhớ nội bộ của AI (`.agents/AGENTS.md`) để rèn luyện AI luôn tuân thủ chuẩn mực Clean Code, kiến trúc Undo/Redo, và phong cách giao tiếp ngắn gọn trong các phiên làm việc tương lai.
