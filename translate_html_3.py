import glob

replacements = {
    # index.html
    "Tài khoản": "Account",
    "Mật khẩu CMS": "CMS Password",
    "Mật khẩu": "Password",
    "CSS (Mỗi link 1 dòng)": "CSS (One link per line)",
    "Không thể thay đổi Site ID.": "Cannot change Site ID.",
    "Xác nhận xóa Site?": "Confirm Delete Site?",
    "Bạn có chắc chắn muốn xóa site này? All dữ liệu và thư mục code đã sinh sẽ bị xóa sạch.": "Are you sure you want to delete this site? All data and generated code will be completely deleted.",
    
    # preview_frame.html
    "Quay lại chi tiết Site": "Back to Site details",
    "Quay lại Site": "Back to Site",
    "Tải lại trang": "Reload page",
    "Tác tử Thiết kế (Design Critic)": "Design Critic Agent",
    "Trực tuyến": "Online",
    "Chào bạn! Tôi là Tác tử Đánh giá Thiết kế (Design Critic Agent). Tôi có thể giúp bạn so sánh và tinh chỉnh giao diện trang": "Hello! I am the Design Critic Agent. I can help you compare and refine the UI of page",
    "để khớp chính xác nhất với thiết kế Figma.": "to precisely match the Figma design.",
    "Hãy viết các yêu cầu điều chỉnh giao diện của bạn (ví dụ: thay đổi cỡ chữ, căn chỉnh lại hình ảnh, hay cập nhật lại khoảng cách lề) vào ô bên dưới!": "Please enter your UI adjustment requests (e.g. change font size, realign images, or update margin) in the box below!",
    "Nhập yêu cầu chỉnh sửa...": "Enter edit request...",
    "Đang tải lại giao diện...": "Reloading interface...",
    "Không thể kết nối đến AI.": "Cannot connect to AI.",
    
    # settings.html
    "Cấu hình AI Feedback (Google Gemini)": "AI Feedback Configuration (Google Gemini)",
    "Gemini API Key được sử dụng chung cho tất cả các Site để AI có thể tự động hiểu ý kiến người dùng và phân tích, thay đổi giao diện HTML/CSS.": "Gemini API Key is shared across all Sites for the AI to understand user feedback and analyze/change HTML/CSS UI.",
    "Nhập Gemini API Key...": "Enter Gemini API Key...",
    "Figma Personal Access Token dùng để đồng bộ thiết kế trực tiếp từ file Figma thành Code giao diện.": "Figma Personal Access Token is used to sync design directly from Figma to UI code.",
    "Nhập Figma Personal Access Token...": "Enter Figma Personal Access Token...",
    
    # site_detail.html
    "Tên Trang <span class=\"text-danger\">*</span>": "Page Name <span class=\"text-danger\">*</span>",
    "Tên file Slug (không nhập .html) <span class=\"text-danger\">*</span>": "Slug (do not enter .html) <span class=\"text-danger\">*</span>",
    "Error kết nối server": "Server connection error",
    "Error kết nối khi Deploy": "Connection error during Deploy",
    "Error kết nối": "Connection Error",
    "Không thể gọi API Deploy. Please try again.": "Cannot call Deploy API. Please try again.",
    "Bạn có chắc chắn muốn xóa trang con này? All code đã sinh tương ứng cũng sẽ bị xóa sạch.": "Are you sure you want to delete this child page? All corresponding generated code will also be completely deleted.",
    "Folder Name không được để trống!": "Folder Name cannot be empty!",
    "Folder Name viết liền không dấu, không chứa ký tự đặc biệt!": "Folder Name must be continuous without accents or special characters!",
    "Các trang con bên trong thư mục này sẽ tự động được di chuyển về Root Folder (Root) và các file code tương ứng sẽ được chuyển ra ngoài.": "Child pages inside this folder will automatically be moved to the Root Folder and corresponding code files will be moved out.",
    "Tài khoản CMS": "CMS Account"
}

for filepath in glob.glob('d:/Projects/test04/templates/*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for k, v in replacements.items():
        content = content.replace(k, v)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Final HTML translations completed.")
