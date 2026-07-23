# Project Rules

# Chạy bằng Flask trong thư mục này

1. Giao diện quản trị được tạo bằng AdminLTE.
2. Phát triển bằng Python Flask.
3. Không sử dụng Database, lưu dữ liệu bằng file JSON.
4. Điều hướng và Thương hiệu (Navbar):
   - Logo thương hiệu ở góc trái là chữ **ABCMS** (Auto Build CMS) kích thước lớn (~1.65rem), được hiển thị dưới dạng chữ có màu sắc đặc trưng gradient (`linear-gradient(135deg, #00aeef, #8cc63f)`). Không có biểu tượng icon đi kèm.
   - Liên kết quay lại trang danh sách ở thanh Navbar là biểu tượng **Ngôi nhà** (Home Icon).
5. Giao diện danh sách Site (index.html):
   - Không sử dụng thanh Sidebar bên trái. Bố cục hiển thị toàn màn hình (full-width/full-screen) sử dụng cấu trúc Top Navigation (`layout-top-nav`) của AdminLTE.
   - Khoảng cách lề trên (Top Padding) của nội dung chính được căn chỉnh đều với hai bên (sử dụng class `pt-3` khoảng ~16px) để tạo sự cân đối.
   - Phải có ô Tìm kiếm Site (Search Site) ở phía trên cùng để lọc nhanh danh sách Site theo ID hoặc Tên bằng JavaScript (tìm kiếm instant thời gian thực).
   - Các Site được hiển thị dưới dạng Box/Card mô phỏng cấu trúc bảng quản trị hosting gồm:
     - Header: Chứa Monitor Icon, Site ID (nền xám), và Tên Site.
     - Body: Hiển thị thống kê thực tế số lượng Trang con bên trong Site (Tổng số Trang, số Trang đã tạo files, số Trang chưa tạo files) kèm theo thanh tiến độ hoàn thành (progress bar).
     - Footer: Chứa cụm biểu tượng hành động ở góc phải (⚙️ Quản lý/Chi tiết Site, 🏠 Truy cập nhanh trang chủ Site, 📝 Sửa thông tin Site, 🗑️ Xóa Site).
6. Khi nhấn "Thêm Site", hiển thị popup nhập:
   - Site ID
   - Tên Site
   - URL
   - Tài khoản
   - Mật khẩu
   - CSS (Mỗi link 1 dòng) - Cho phép cấu hình nhiều đường dẫn thư viện CSS chuẩn của dự án.
7. Sau khi lưu (Tạo Site mới):
   - Lưu thông tin vào file JSON.
   - Hiển thị Site trong danh sách Trang chủ (index.html). Các Site thêm mới nhất sẽ được đảo thứ tự để luôn **hiển thị lên đầu danh sách**.
8. Khi nhấn vào Tên Site hoặc nút xem (icon ⚙️ ở chân thẻ):
   - Chuyển hướng đến trang chi tiết Site (`site_detail.html`).
9. Cấu trúc mỗi Trang con (Page) gồm:
   - Tên Trang
   - Thư mục con (Folder - để trống nếu ở thư mục gốc)
   - Slug đường dẫn (Đóng vai trò là Tên File HTML lúc sinh code, ví dụ: `gioi-thieu` tạo thành `gioi-thieu.html`)
   - Link Figma Dev Mode
   - Layout (Chỉ có 2 loại tùy chọn: `sub-template` và `sub-template-tab`)
10. Sau khi lưu Trang con:
    - Lưu vào file JSON của Site tương ứng.
    - Trang mới được chèn tự động lên vị trí trên cùng của danh sách (không nằm dưới đáy).
11. Có nút Sửa để chỉnh sửa thông tin của từng Trang con:
    - Cho phép thay đổi Tên Trang, Thư mục con, Slug, Link Figma, Layout.
    - Lưu thay đổi vào JSON và tự động di chuyển/đổi tên các file code đã sinh tương ứng trên đĩa cứng nếu đổi Thư mục con hoặc Slug.
12. Có nút Xóa để xóa Trang con:
    - Cho phép xóa hoàn toàn Trang con khỏi cấu trúc JSON.
    - Tự động xóa các file HTML/CSS/JS đã sinh tương ứng của trang con đó và dọn dẹp thư mục con nếu thư mục bị trống hoàn toàn để giữ hệ thống sạch sẽ.
13. Giao diện chi tiết Site (site_detail.html) và Trang chủ (index.html):
    - Khung thông tin Site ở đầu trang phải dàn hàng ngang chiếm trọn màn hình (full-width). (Lưu ý: Cấu hình Gemini API Key và Figma Token đã được tách thành cài đặt toàn cục, lưu chung tại file `data/config.json` và chỉnh sửa ở màn hình **Cài đặt hệ thống** riêng biệt qua nút bánh răng trên top navbar).
    - Phải có ô Tìm kiếm Trang (Search Page) đặt sát ở góc bên trái để lọc nhanh danh sách Trang con. Ở góc phải, có nút **"Quản lý Thư mục"** (màu viền xanh dương) bên cạnh nút **"Thêm Trang"** (màu xanh dương).
    - Nút **"Quản lý Thư mục"** mở ra một Modal hợp nhất cho phép:
      - Tạo Thư mục mới.
      - Xem danh sách các thư mục con hiện có của Site.
      - Thay đổi vị trí (Reorder) của các thư mục con bằng các nút mũi tên Di chuyển lên (`▲`) và Di chuyển xuống (`▼`). Thứ tự mới sẽ tự động cập nhật lại nhãn lọc và hộp chọn dropdown.
      - Đổi tên (Rename) từng thư mục: Thay đổi metadata thư mục, tự động đổi đường dẫn lưu trữ của tất cả Trang con thuộc thư mục đó, và đổi tên thư mục vật lý tương ứng trên đĩa cứng.
      - Xóa (Delete) từng thư mục: Xóa thư mục khỏi danh sách, tự động di chuyển toàn bộ Trang con bên trong về **Thư mục gốc (Root)** để bảo toàn dữ liệu, và dọn dẹp thư mục vật lý.
    - Tất cả các Modal Popup (Thêm/Sửa Site, Thêm/Sửa Trang, Quản lý Thư mục) phải được chuẩn hóa đồng bộ 100%:
      - Tiêu đề modal (Header) sử dụng nền xám đậm (`bg-dark text-white`) với tiêu đề rút gọn tối giản: **"Thêm site"**, **"Sửa site"**, **"Thêm trang"**, **"Sửa trang"**, **"Quản lý thư mục"**.
      - Nút lưu hành động chính (submit) luôn đặt tên là **"Lưu"** và sử dụng màu xanh dương (`btn-primary`).
      - Nút **"Đóng"** (màu xám `btn-secondary`) luôn được bố trí nằm ở phía bên trái của chân trang Modal (Modal Footer), nút **"Lưu"** nằm ở phía bên phải.
      - Toàn bộ các ô nhập dữ liệu (`input type="text"`, `select`, `textarea`) đều phải có cùng một kích thước chiều cao chuẩn (`form-control`), không pha trộn kích thước nhỏ (`form-control-sm`). Riêng ô nhập liệu Link Figma (`textarea`) phải thiết kế với chiều cao rộng rãi là **170px** để dễ hiển thị các liên kết dài.
      - Quy tắc CSS định dạng nút hành động (`.page-action-btn`, `.folder-action-btn`) tuyệt đối không dùng từ khóa `!important` cho thuộc tính `display: inline-flex;` để tránh xung đột làm ghi đè và ngăn cản việc ẩn phần tử bằng `display: none;` của inline style.
    - Trong biểu mẫu Thêm và Sửa Trang, trường **"Thư mục con (Folder)"** phải được hiển thị dưới dạng hộp chọn **Select box (Dropdown)** chứa danh sách các thư mục con đã được khởi tạo của Site đó để người dùng lựa chọn trực tiếp thay vì nhập liệu tự do.
    - Danh sách các Trang con được trình bày dưới dạng lưới ô (Grid Box layout - `col-md-6 col-lg-4`). Mỗi thẻ Trang con chứa:
      - Header: Tên Trang, biểu tượng file code, và nhãn hiển thị loại Layout ở góc bên phải.
      - Body: Thư mục con, Tên file (Slug), trạng thái Figma Link, trạng thái Trang (Đã tạo / Chưa tạo), và thông tin hướng dẫn.
      - Footer: Tích hợp các nút chức năng. Trong đó, các nút hành động icon-only ở góc phải (Deploy, Sửa, Xóa) phải được thiết kế đồng bộ kích thước vuông chuẩn **32x32px** (`page-action-btn`), căn giữa icon tuyệt đối.
14. Cơ chế hoạt động của các nút Preview và Deploy:
    - Nếu Trang con chưa được biên dịch thành công (trạng thái Chưa tạo Trang), cả hai nút **Preview** và **Deploy** phải ở trạng thái **khóa màu xám (disabled)**.
    - Sau khi nhấn **Tạo Trang** và biên dịch thành công, hai nút bị khóa này sẽ lập tức được ẩn đi và kích hoạt hiển thị nút **Preview** (xanh lá) và **Deploy** (xanh dương) tương ứng bằng JavaScript.
    - Đặc biệt, khi mở màn hình Preview, Backend sẽ tự động phát hiện và chèn (inject) động tất cả các link CSS mặc định của Site vào phần `<head>` của trang HTML để đảm bảo luôn hiển thị đúng giao diện mà không phụ thuộc vào mã tĩnh trên đĩa cứng.
15. Khi nhấn "Tạo Trang" (Biên dịch):
    - Sinh mã nguồn HTML/CSS/JS theo cấu trúc `output/<site_id>/<folder>/<slug>.<ext>`.
    - Quá trình tạo phải được thực hiện bất đồng bộ (AJAX) và hiển thị trạng thái chờ build ("Đang phân tích thiết kế...", "Đang tạo files...").
    - Nếu Trang chưa được cấu hình Link Figma, nút "Tạo Trang" phải ở trạng thái disabled.
    - Hệ thống luôn thực hiện biên dịch động (Dynamic Compilation) trực tiếp từ cấu trúc thiết kế Figma:
      - Trích xuất dữ liệu JSON của Node ID từ Figma API và tải xuống bản đồ hình ảnh (Image Fills Mapping) bằng Personal Access Token (lưu bảo mật chung tại file `data/config.json`) để giải quyết toàn bộ các ảnh và màu nền gradient thực tế.
      - Chạy bộ dịch `compile_figma_node_to_html_css` hỗ trợ đầy đủ các thuộc tính Layout Sizing phức tạp của Figma (`HUG`, `FILL`, `FIXED`, `STRETCH`) để biên dịch trực tiếp ra mã nguồn HTML/CSS tĩnh tự động co giãn tương ứng.
      - Hoàn toàn KHÔNG sử dụng các mẫu giao diện ngoại tuyến được viết sẵn (Offline Fallback Templates).
      - Hỗ trợ lưu cache cấu trúc thiết kế trong tệp tin `data/figma_cache.json` để phục vụ biên dịch ngoại tuyến tức thời nếu Token bị trống hoặc lỗi kết nối.
      - Nếu người dùng có cấu hình Gemini API Key, sau khi sinh HTML/CSS thô từ Figma, hệ thống sẽ tự động gọi AI để tái cấu trúc (Refactor) lại toàn bộ mã nguồn sao cho tuân thủ chuẩn cấu trúc và layout bảng được quy định trong thư mục tham chiếu `data/ai_templates/` (gồm `structure-template.html` và `table-template.html`). AI cũng sẽ được cung cấp danh sách các thư viện CSS (nếu có cấu hình ở Site) để ưu tiên tận dụng tối đa class chuẩn, thay vì tự viết mã CSS mới.
16. Quy trình Deploy lên CMS (Tự động cập nhật HTML, CSS, JS lên hệ thống):
    - Quy trình Deploy được thiết kế chạy **bất đồng bộ ngầm (Background Task)** trên server. Người dùng có thể F5 tải lại trang, tắt trình duyệt hoặc click Deploy nhiều trang cùng lúc mà tiến trình không bị ngắt. Trạng thái hiển thị tức thời qua API polling `/api/deploy_status` mỗi 3s.
    - Khi Deploy, hệ thống tự động chạy Playwright thực hiện các bước sau:
      1. Đăng nhập vào CMS bằng tài khoản cấu hình và điều hướng đến trình quản lý trang `#!/page`.
      2. Kiểm tra sự tồn tại của Trang trên CMS.
         - Nếu **Trang chưa tồn tại**: Kiểm tra và tự động tạo Thư mục con (nếu có) -> Tự động điền form Tạo Trang (Tên trang, Slug, HTML Header, Layout) -> click Biên tập để mở màn hình Editor.
         - Nếu **Trang đã tồn tại**: Bỏ qua bước tạo trang, chọn trang và click Biên tập để mở màn hình Editor.
      3. Cập nhật mã nguồn (UI Automation):
         - Upload hình ảnh: Nhấn nút `insertCmsImage` mở popup quản lý file, kiểm tra và tạo thư mục `content` (nếu chưa có), sau đó upload file ảnh vào thư mục này.
         - Cập nhật HTML: Click nút `<>` (`data-cmd="html"`) để mở chế độ Code, dán mã HTML vào CodeMirror hoặc bơm trực tiếp qua biến môi trường Angular.
         - Cập nhật CSS/JS: Chuyển sang tab CSS/JS tương ứng, dán mã vào CodeMirror hoặc bơm qua scope Angular.
         - Click nút "Lưu" trên giao diện CMS để lưu toàn bộ thay đổi.
      4. Lưu dữ liệu, hoàn thành và báo thành công bằng popup (Toast) trên giao diện.
17. Khi xóa Site ở trang chủ:
    - Xóa thông tin khỏi JSON và đồng thời xóa sạch sẽ thư mục code đã sinh của Site đó trên đĩa cứng để tránh rác hệ thống.
18. Giao diện xem Preview kết hợp với Phản hồi Thiết kế (Split-Screen Preview & Feedback):
    - Khi bấm Preview, trang quản trị hiển thị giao diện chia đôi tích hợp thanh top navbar quản trị chung (không có lề margin-left).
    - Nút Preview sẽ chuyển hướng trực tiếp trên tab hiện tại (không mở tab mới) để người dùng có thể điều hướng mượt mà khi quay lại trang quản lý.
    - Bên trái hiển thị Iframe của trang giao diện thực tế (raw HTML) với độ rộng khung hình hiển thị tối đa là 1920px.
    - Bên phải hiển thị một Chatbox giao tiếp với Design Critic Agent để hỗ trợ tiếp nhận ý kiến sửa đổi giao diện trực tiếp từ người dùng.
    - Chatbox hiển thị tin nhắn người dùng dạng **plain text** (tự động escape HTML entities), đảm bảo các thẻ HTML như `<h4 class="...">` được hiển thị đúng như ký tự thay vì bị render bởi trình duyệt.
    - Lịch sử trò chuyện của Chatbox được **tự động lưu vào `localStorage`** (theo từng trang cụ thể) để không bị mất dữ liệu khi tải lại trang (F5).
19. Bộ máy điều chỉnh HTML/CSS động thông qua Chatbox (AI Feedback Engine):
    - Hỗ trợ gửi bất kỳ yêu cầu điều chỉnh giao diện nào bằng ngôn ngữ tự nhiên thông qua tích hợp **Google Gemini AI** (model: `gemini-3.1-flash-lite`, thư viện: `google-genai`).
    - Backend đọc toàn bộ nội dung **HTML và CSS** hiện tại của trang, gửi kèm yêu cầu người dùng lên AI để phân tích. Cùng lúc đó, AI cũng được truyền vào nội dung của các template chuẩn từ thư mục `data/ai_templates/` và danh sách các thư viện CSS chuẩn của Site để sử dụng làm tài liệu tham chiếu (Reference) khi sửa HTML/CSS.
    - AI trả về toàn bộ HTML và CSS đã được cập nhật dưới dạng JSON. Backend ghi đè trực tiếp vào file tương ứng, Iframe Preview tự động reload để hiển thị giao diện mới ngay lập tức.
    - Gemini API Key được dùng chung cho tất cả các Site. Key lưu bảo mật tại `data/config.json` và cấu hình qua trang **Cài đặt hệ thống** (biểu tượng răng cưa ở top navbar).
20. Cập nhật giao diện (Dark Mode & Đồng bộ Card):
    - Thêm nút bật/tắt Dark Mode trên thanh điều hướng (lưu trạng thái qua localStorage), code CSS/JS được tách riêng vào static/css/dark-mode.css và static/js/dark-mode.js.
    - Đồng bộ thiết kế của Site Card (Dashboard) và Page Card (Site Detail) với viền xanh (1.5px solid #00aeef) và bo góc 6px.
    - Bổ sung CSS hỗ trợ Dark Mode cho các thành phần tuỳ chỉnh (menu tree, modal bg-white, page card, viền input search).
    - Mặc định gán layout: 'sub-template' khi tạo Menu mới qua tính năng tạo nhanh (Inline Menu).
