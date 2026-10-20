# Đánh giá UI và kế hoạch triển khai — 19/10/2026

## Đánh giá thiết kế

PDF là một board gồm login/register, login thành công/thất bại; Tổng quan, Báo cáo, Chat AI, Dữ liệu ở trạng thái trước/sau upload; quản trị nhân sự và cài đặt. Điểm tốt: điều hướng nhất quán, phân biệt empty/loaded, màu pastel giúp phân nhóm KPI và CTA upload rõ ràng.

Điểm cần chỉnh theo code: login dùng username/mã nhân viên thay email; đăng ký không cấp password ngay; thêm activation. Không hiển thị conversion rate hoặc so sánh tăng trưởng nếu backend không có chỉ số đó. KPI thứ tư dùng AOV thật. Các con số nhân sự, integration badges và subscription trong board không phải dữ liệu backend.

## Thảo luận với ChatGPT

Đã gửi mô tả board và contract backend vào cuộc trò chuyện Kế hoạch MVP backend ngày 19/10/2026. ChatGPT chấp thuận HTML/CSS/ES modules cho MVP và yêu cầu: không giả kết quả API, token activation không vào dashboard, dataset in-memory có thông báo, upload raw bytes, report dùng Blob, lỗi 401/403 khác nhau, escape nội dung không tin cậy, test browser thật.

## Các phase

| Phase | Công việc | Điều kiện hoàn thành |
|---|---|---|
| 1. Nền tảng | Design tokens, auth split card, sidebar/topbar, cards, robot, responsive | Login và shell render desktop/mobile, không tràn toàn trang |
| 2. Xác thực | Register-request, login, activation, logout local, token guard | Luồng request → approve → provision → activate → access chạy qua API |
| 3. Dữ liệu | CSV/JSON, EDA/quality/schema, dashboard KPI/charts, filter | Kết quả từ API; empty/loading/error; không âm thầm dùng dữ liệu giả |
| 4. Báo cáo & AI | 6 exports, lịch sử phiên, chatbot, SELECT display | Download Blob thật; nguồn câu trả lời rõ ràng |
| 5. Synthetic & admin | Generate+validation, request list/review/provision, role update | Manager/admin UI; user không có admin/synthetic; backend reject trái quyền |
| 6. QA & tài liệu | Core tests, live adapter integration, browser checks, hướng dẫn | Evidence và phần chưa kiểm thử ghi trong TEST_REPORT.md |

Không thêm dependency/framework chỉ để dựng giao diện. API client và pure helpers tách module; app.js chứa render/event cho các màn hình, styles.css chứa layout. Khi có router/deep-link và state đa phiên phức tạp mới cân nhắc framework.

Các phase này là phạm vi phiên bản đầu, không đồng nghĩa backend đã production-ready. Dataset ownership, granular permissions, async jobs và persistent reporting cần phase backend riêng.
