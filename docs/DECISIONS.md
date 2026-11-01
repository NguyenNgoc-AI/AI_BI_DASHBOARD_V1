# DECISIONS.md — Nhật Ký Quyết Định Kiến Trúc (Architecture Decision Records)

Tài liệu này ghi lại các quyết định thiết kế quan trọng trong quá trình phát triển dự án theo định dạng chuẩn: **"Ngày X chọn Y vì Z, đã loại bỏ W"**.

---

### ADR-01: Quy Trình Đăng Ký Tài Khoản Có Phê Duyệt & Mật Khẩu Hai Pha
- **Ngày quyết định:** 01/10/2026
- **Quyết định:** Chọn quy trình phê duyệt 4 bước (`Đăng ký yêu cầu` $\rightarrow$ `Admin phê duyệt` $\rightarrow$ `Admin cấp phát tài khoản` $\rightarrow$ `Nhân viên đăng nhập mật khẩu tạm và kích hoạt`).
- **Lý do (Vì):** Bảo vệ an toàn dữ liệu tài chính nội bộ của doanh nghiệp, ngăn chặn việc người ngoài hoặc nhân sự chưa xác minh tự ý tạo tài khoản truy cập dashboard kinh doanh.
- **Phương án đã loại bỏ (Đã loại bỏ):** Loại bỏ tính năng tự đăng ký công khai (Public self-registration) cho phép người dùng tự điền mật khẩu và tự cấp quyền truy cập ngay lập tức.

---

### ADR-02: Pipeline Xử Lý Dữ Liệu In-Memory (Stateless Data Processing)
- **Ngày quyết định:** 04/10/2026
- **Quyết định:** Chọn cơ chế phân tích dữ liệu trực tiếp trong bộ nhớ (In-memory Processing) từ tệp CSV/JSON người dùng gửi lên trong mỗi phiên làm việc.
- **Lý do (Vì):** Tối ưu hóa tốc độ phản hồi tức thì của dashboard, đơn giản hóa hạ tầng máy chủ cho giai đoạn MVP, và giảm thiểu rủi ro rò rỉ dữ liệu khách hàng (dữ liệu phân tích không bị lưu trữ vĩnh viễn trên ổ cứng máy chủ).
- **Phương án đã loại bỏ (Đã loại bỏ):** Loại bỏ việc xây dựng hệ thống cơ sở dữ liệu kho bãi phân tán (Data Warehouse) hoặc tự động chèn hàng triệu dòng dữ liệu thô vào SQLite/PostgreSQL cho từng người dùng.

---

### ADR-03: Quản Lý Thu Hồi Token Bằng `token_version` Kết Hợp SQLite
- **Ngày quyết định:** 07/10/2026
- **Quyết định:** Tự xây dựng bộ mã hóa JWT HMAC-SHA256 kết hợp trường số phiên bản token `token_version` được lưu và đối chiếu trực tiếp từ bảng `users` trong SQLite ở mỗi request.
- **Lý do (Vì):** Cung cấp khả năng vô hiệu hóa tức thời (Instant Revocation) toàn bộ token cũ khi người dùng đổi vai trò (`role`) hoặc kích hoạt mật khẩu mới, mà vẫn giữ kiến trúc máy chủ đơn giản không cần cụm bộ nhớ đệm phân tán Redis.
- **Phương án đã loại bỏ (Đã loại bỏ):** Loại bỏ JWT hoàn toàn không trạng thái (Stateless unrevokable JWT) và loại bỏ việc tích hợp máy chủ Redis chỉ để quản lý danh sách đen (token blacklist).

---

### ADR-04: Bộ Điều Hướng LLM Đa Nhà Cung Cấp Có Fallback Ngoại Tuyến
- **Ngày quyết định:** 12/10/2026
- **Quyết định:** Thiết kế lớp `LLMRouter` hỗ trợ 4 nhà cung cấp (`deterministic`, `openai`, `gemini`, `llama`), trong đó mọi lỗi kết nối mạng hoặc lỗi định dạng của API bên ngoài sẽ tự động kích hoạt chế độ Fallback về `DeterministicAdapter`.
- **Lý do (Vì):** Đảm bảo hệ thống luôn sẵn sàng vận hành 100% trong mọi điều kiện (demo nội bộ, môi trường cô lập không có internet, hết quota API key) mà không bị sập hay gián đoạn trải nghiệm người dùng.
- **Phương án đã loại bỏ (Đã loại bỏ):** Loại bỏ việc phụ thuộc cứng vào duy nhất một nhà cung cấp đám mây độc quyền (như chỉ dùng OpenAI API hoặc chỉ dùng Google Gemini).

---

### ADR-05: Rào Chắn Truy Vấn Text-to-SQL Chỉ Đọc (Read-Only Guardrails)
- **Ngày quyết định:** 15/10/2026
- **Quyết định:** Áp dụng bộ lọc cú pháp nghiêm ngặt (chỉ cho phép 1 câu lệnh `SELECT`, đối chiếu danh sách trắng bảng/cột, ép `LIMIT 500`, cấm tuyệt đối các từ khóa `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `PRAGMA`).
- **Lý do (Vì):** Ngăn chặn triệt để các cuộc tấn công SQL Injection và loại bỏ hoàn toàn khả năng mô hình ngôn ngữ lớn (LLM) ảo giác sinh ra câu lệnh phá hoại cấu trúc dữ liệu.
- **Phương án đã loại bỏ (Đã loại bỏ):** Loại bỏ việc cho phép LLM tự do thực thi câu lệnh SQL trực tiếp xuống cơ sở dữ liệu mà không qua lớp kiểm duyệt danh sách trắng.

---

### ADR-06: Giao Diện Frontend Thuần "Code Candy" Không Cần Bước Build
- **Ngày quyết định:** 19/10/2026
- **Quyết định:** Xây dựng toàn bộ giao diện bằng Vanilla HTML5, Modern CSS, ES6+ Modules thuần túy và vẽ biểu đồ trực tiếp bằng phần tử SVG gốc.
- **Lý do (Vì):** Giữ dự án siêu nhẹ, mở lên là chạy ngay qua máy chủ static Python (`Frontend/serve.py`), không tốn tài nguyên cài đặt hàng trăm megabyte `node_modules`, và tương thích hoàn toàn với các môi trường hạn chế quyền tải gói.
- **Phương án đã loại bỏ (Đã loại bỏ):** Loại bỏ việc dùng các framework nặng như Next.js, React, TailwindCSS, Chart.js hay các công cụ đóng gói Vite/Webpack cho phiên bản MVP.

---

### ADR-07: Hợp Đồng Dữ Liệu Canonical View 5 Cột & Bộ Từ Điển Ánh Xạ Tự Động
- **Ngày quyết định:** 22/10/2026
- **Quyết định:** Chuẩn hóa toàn bộ dữ liệu kinh doanh về 5 cột cốt lõi (`date, order_id, product, revenue, cost`) thông qua lớp ánh xạ từ điển tiếng Việt/tiếng Anh thông minh (`inspect_and_map_columns`).
- **Lý do (Vì):** Cho phép người dùng tải lên trực tiếp tệp báo cáo xuất từ các sàn thương mại điện tử phổ biến (Shopee, Lazada, TikTok Shop, Shopify) mà không cần chỉnh sửa hoặc đổi tên cột thủ công.
- **Phương án đã loại bỏ (Đã loại bỏ):** Loại bỏ yêu cầu bắt buộc người dùng phải định dạng lại tiêu đề cột theo đúng quy chuẩn kỹ thuật cứng nhắc trước khi tải lên.

---

### ADR-08: Định Hướng Tinh Gọn Cho Môi Trường Phát Triển & Demo Local (Lean Local Strategy)
- **Ngày quyết định:** 27/10/2026
- **Quyết định:** Tối ưu hóa toàn bộ hệ thống cho mục tiêu chạy cục bộ trên máy cá nhân của các thành viên trong nhóm:
  1. Tự động sinh `JWT_SECRET` ngẫu nhiên và lưu vào `.env` local (Phương án B) để duy trì phiên đăng nhập khi Uvicorn reload.
  2. Áp dụng phân quyền theo 3 vai trò (`admin`, `manager`, `user`) đã có sẵn; không phân quyền vi mô `permissions` hay phân vùng `data_scope`.
  3. Loại bỏ yêu cầu cài đặt cụm hàng đợi bất đồng bộ (Celery / Redis / RabbitMQ), giữ toàn bộ tiến trình chạy trực tiếp qua Python chuẩn.
  4. Giữ mô hình Text-to-SQL sinh câu lệnh mẫu an toàn để hiển thị phân tích, chưa cần dựng DB thực thi phức tạp.
- **Lý do (Vì):** Giúp mọi thành viên trong nhóm tải code về là chạy được ngay trên Windows/macOS/Linux với tài nguyên tối thiểu, không bị lỗi phụ thuộc môi trường ngoài, phiên làm việc không bị gián đoạn, và tập trung vào trải nghiệm phân tích dashboard cốt lõi.
- **Phương án đã loại bỏ (Đã loại bỏ):** Loại bỏ việc triển khai kiến trúc microservices, cụm cache/queue phân tán, hệ thống đo lường token/rate-limiting tốn kém và phân quyền vi mô quá mức cần thiết cho môi trường phát triển cục bộ.

---

### ADR-09: Chuyển Đổi Tab "Dữ Liệu Tổng Hợp" Sang "Kiểm Nghiệm Dữ Liệu Độc Lập" (Pre-flight Data Audit Sandbox)
- **Ngày quyết định:** 01/11/2026
- **Quyết định:**
  1. Thay thế hoàn toàn tab "Dữ liệu tổng hợp" bằng tab **"Kiểm nghiệm dữ liệu" (Data Audit)** hoạt động như một **Sandbox kiểm thử độc lập (Pre-flight Check)**:
     - Có khung tải tệp riêng biệt (`POST /datasets/audit`) cho phép người dùng tải lên và kiểm tra chất lượng tệp CSV/JSON tùy ý mà **hoàn toàn không ghi đè hay làm thay đổi Dashboard đang hiển thị**.
     - Cung cấp nút *"Dùng tệp mẫu test"* và nút *"Lấy dữ liệu từ Dashboard"* để linh hoạt nguồn kiểm tra.
     - Sau khi kiểm định đạt chuẩn, cung cấp nút **"🚀 Đưa vào Dashboard"** để nạp dữ liệu đã duyệt sang workspace chính và tự động vẽ biểu đồ.
  2. Nâng cấp bộ máy `backend/eda/quality_checker.py` và endpoint `/datasets/quality`, `/datasets/audit` trả về điểm số tổng hợp, đo lường chi tiết 4 trụ cột (Completeness, Uniqueness, Invariants/Validity, Outliers), phân loại cấp bậc (Tier A - D), danh sách các dòng vi phạm luật kinh doanh cụ thể và khuyến nghị khắc phục.
  3. Xây dựng giao diện hiển thị bảng đồng hồ thẻ điểm (Scorecard), bảng kiểm toán các dòng vi phạm kèm nhãn mức độ (`CRITICAL`, `WARNING`, `INFO`), và nút tải biên bản kiểm toán định dạng JSON.
- **Lý do (Vì):**
  - Người dùng cần một môi trường "tiền kiểm toán" an toàn để rà soát lỗi dữ liệu (doanh thu âm, chiết khấu vượt giá bán, trùng mã đơn) trước khi chính thức đưa vào vẽ biểu đồ và tổng hợp báo cáo kinh doanh.
  - Tách biệt hoàn toàn trạng thái giữa phiên làm việc Dashboard (`state.rows`, `state.analysis`) và phiên kiểm thử độc lập (`state.audit.rows`, `state.audit.quality`).
- **Phương án đã loại bỏ (Đã loại bỏ):** Loại bỏ việc buộc người dùng phải tải dữ liệu trực tiếp vào Dashboard rồi mới xem được chất lượng.

