# Reflection - UI & Chat Experience Engineer (minhnq-chc)

## Thành viên
- **Họ và tên:** Ninh Quang Minh
- **MSSV:** 2A202602432
- **Vai trò:** Thành viên 4: UI & Chat Experience Engineer

## Tổng quan công việc đã thực hiện

Trong quá trình phát triển dự án IT Helpdesk AI Agent, tôi đã hoàn thành toàn bộ trách nhiệm của mình cho module User Interface. UI được xây dựng với Streamlit nhưng đã được tùy biến sâu (custom CSS) để mang lại trải nghiệm chuyên nghiệp, vượt ra khỏi các giới hạn mặc định của framework.

### 1. Phân tích & Chuẩn bị
- Đọc và phân tích kiến trúc backend (`chat.py`) để hiểu luồng hoạt động của hàm `run_model_tool_loop()`.
- Lựa chọn Streamlit là framework phù hợp nhất do tính đồng bộ, khả năng quản lý `session_state` hiệu quả, và dễ dàng tích hợp các component render UI.
- Thêm dependencies cần thiết (`streamlit>=1.30.0`) vào `requirements.txt`.

### 2. Phát triển Chat Interface (`app.py`)
- **Tích hợp Backend:** Import và gọi trực tiếp `run_model_tool_loop()`, quản lý dữ liệu lịch sử hội thoại qua `st.session_state`.
- **Hiển thị Tool Trace:** Xây dựng cơ chế parse và render chi tiết từng vòng lặp tool (`st.expander`), bao gồm cả trạng thái thành công/lỗi và tham số (arguments & results).
- **Trạng thái (Status Badges):** Bổ sung các thông báo trực quan (UI Badges) khi AI đang chờ người dùng xác nhận thông tin (⏸️ waiting_for_user) hoặc khi chạm ngưỡng số vòng lặp tối đa (⚠️ max_tool_rounds).
- **Xử lý JSON Output:** Xây dựng hàm `parse_assistant_text()` để bóc tách thông điệp phản hồi từ Model. Do Model thô thường trả về chuỗi JSON thô có chứa intent/action/reply, hàm này tự động parse và chỉ hiển thị phần text tự nhiên (trường `reply` hoặc `message`) tới người dùng.

### 3. Tối ưu hóa UI/UX
- **Liquid Glassmorphism:** Đập bỏ giao diện mặc định của Streamlit, nhúng custom CSS theo xu hướng Liquid Glassmorphism (nền gradient, các block chat và sidebar trong suốt nhẹ, có hiệu ứng kính mờ (blur), bo góc sâu, viền tinh tế).
- **Light/Dark Mode Tự Động:** Tối ưu hóa CSS bằng cách sử dụng các biến Native CSS của Streamlit (`var(--background-color)`, `var(--secondary-background-color)`) kết hợp với lớp kính bán trong suốt (`rgba(128,128,128,x)`). Kết quả là giao diện sẽ tự động chuyển màu mượt mà khi người dùng bật Dark/Light mode trong menu mặc định, không còn bị lỗi chữ trắng nền trắng.
- **Bot Avatar & Tên mới:** Đổi tên bot thành "Vhelpdesk Bot" và tích hợp một Avatar riêng biệt mang phong cách gọn gàng, thân thiện.

### 4. Tính năng Phụ trợ & Chế độ Demo
- **Cấu hình Sidebar Compact:** Bố trí lại sidebar thông minh hơn. Đưa các thiết lập nâng cao (Cửa sổ lịch sử, Số vòng lặp, Phiên bản Artifact) vào trong `st.expander` để tiết kiệm không gian.
- **Song ngữ (i18n):** Tích hợp nút chuyển đổi Anh/Việt áp dụng toàn thời gian thực cho mọi nhãn và placeholder trên UI.
- **Mock/Demo Mode:** Khả năng chuyển đổi sang chế độ Demo không cần API Key, bao gồm 11 kịch bản mock được thiết kế tinh tế (bắt keyword) để biểu diễn mọi tình huống (từ check dịch vụ, hỏi thêm thông tin, đến từ chối yêu cầu ngoài luồng).
- **Xuất Transcript:** Viết tính năng tải xuống file lịch sử (JSON format tương thích hoàn toàn với schema gốc của hệ thống), đồng thời tự động lưu trữ (auto-save) phiên làm việc vào folder `transcripts/`.

## Kinh nghiệm rút ra (Reflection)
1. **Kiểm soát CSS trong Streamlit:** Streamlit là một framework đóng, việc style UI đôi khi rất khó khăn do các class sinh tự động (`st-emotion-cache`). Giải pháp tốt nhất là sử dụng `data-testid` để inject CSS an toàn, kết hợp biến màu nguyên bản của Streamlit để duy trì tính tương thích với Dark/Light mode.
2. **Xử lý Output của Agent:** Khi làm việc với LLM trả về cấu trúc JSON cứng (để phục vụ tool call hoặc internal logic), bộ phận UI cần phải đứng ở giữa làm "bộ lọc" để chỉ hiển thị những thông tin thân thiện (Human-readable) cho người dùng cuối.
3. **Cấu trúc Module độc lập:** Nhờ việc tuân thủ triệt để nguyên tắc không sửa file của thành viên khác, UI layer được cô lập hoàn toàn vào `app.py`. Việc này giúp hạn chế conflict khi merge code trên Git và thể hiện đúng tinh thần teamwork độc lập - hiệu quả.

## Hướng dẫn Merge Code (Git)
Dự án được triển khai trên branch độc lập. Lịch sử commit đảm bảo sạch sẽ và mô tả rõ ràng các thành phần chức năng:
1. `feat(ui): add streamlit>=1.30.0 to requirements.txt`
2. `feat(ui): create Streamlit chat UI with tool trace, i18n, demo mode`
3. `style(ui): apply Liquid Glassmorphism and JSON response parser`
4. `evidence(ui): add demo transcript files and reflection`
