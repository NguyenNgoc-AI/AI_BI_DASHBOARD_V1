# BACKLOG.md — Kế Hoạch & Việc Cần Làm (Lean Local Backlog)

> **Định hướng:** Tối ưu hóa cho môi trường phát triển cục bộ trên máy cá nhân của các thành viên trong nhóm (nhẹ máy, khởi động nhanh, duy trì phiên làm việc ổn định, đủ tính năng để chạy thử nghiệm và demo nội bộ).

---

### [P0-1] Tự Động Sinh Persistent Secret Cho Local (Phương Án B) [HOÀN THÀNH]
- **Mô tả:** Loại bỏ chuỗi tĩnh `"development-only-change-me-32-chars"` trong `backend/config.py`. Hỗ trợ môi trường local tự động nạp hoặc sinh secret ngẫu nhiên lưu vào tệp `.env` để không bị văng đăng nhập mỗi khi Uvicorn reload code.
- **Tiêu chí hoàn thành (Acceptance Criteria):**
  1. [x] Ở môi trường sản xuất (`APP_ENV=production`): Bắt buộc cấu hình `JWT_SECRET` dài $\ge 32$ ký tự, nếu thiếu phải từ chối khởi động (`raise RuntimeError`).
  2. [x] Ở môi trường phát triển (`development`): Backend đọc biến từ tệp `.env` local. Nếu chưa có `JWT_SECRET`, tự động sinh chuỗi ngẫu nhiên an toàn (`secrets.token_urlsafe(32)`), tự động ghi lưu vào tệp `.env` và in thông báo ra console.
  3. [x] Duy trì phiên đăng nhập: Các lần khởi động hoặc Uvicorn reload tiếp theo ở local đọc lại secret từ `.env`, đảm bảo token không bị vô hiệu hóa bất ngờ. Tuyệt đối không còn chuỗi secret tĩnh hardcode trong mã nguồn.

### [P0-2] Khắc Phục Lỗi Treo Bộ Test Tích Hợp `tests/test_api.py` [HOÀN THÀNH]
- **Mô tả:** Khi chạy `python -m unittest tests/test_api.py` trên môi trường Python 3.13 và FastAPI phiên bản mới, `TestClient` bị treo vô hạn trong `setUpClass` (do xung đột cơ chế event loop giữa `httpx` và `starlette.testclient`).
- **Tiêu chí hoàn thành (Acceptance Criteria):**
  1. [x] Tinh chỉnh cách khởi tạo TestClient hoặc đồng bộ phiên bản tương thích giữa FastAPI, Starlette và httpx; cô lập `JWT_SECRET` trong `conftest.py`.
  2. [x] Chạy lệnh `python -m unittest tests/test_api.py` hoàn tất trong vòng dưới 15 giây và đạt kết quả **PASS 100% (6/6 suites, 2.58s)**.

---
## Mức Độ Ưu Tiên P1: Cốt Lõi & Dọn Dẹp Mã Nguồn

### [P1-1] Dọn Dẹp Mã Nguồn Nhân Bản & Sửa Lỗi Import [HOÀN THÀNH]
- **Mô tả:** Hiện tại có sự trùng lặp giữa các thư mục `semantic/`, `eval/` tại thư mục gốc và `data/engine/semantic/`, `data/engine/eval/`. Ngoài ra thư mục `demo_ui/` đang bị bỏ trống và tệp `data/engine/generator/api/standalone_server.py` bị lỗi import đường dẫn.
- **Tiêu chí hoàn thành (Acceptance Criteria):**
  1. [x] Chuẩn hóa kiến trúc import: Xác định duy nhất 1 thư mục làm nguồn sự thật cho lớp ngữ nghĩa (Semantic Layer) và bộ đánh giá (Evaluation) tại thư mục gốc; dọn dẹp các thư mục bản sao `data/engine/semantic/` và `data/engine/eval/`.
  2. [x] Sửa lỗi đường dẫn import module và dữ liệu trong `data/engine/generator/api/standalone_server.py` và `router.py`. Toàn bộ 40/40 tests trong `data/tests/` chạy thành công (8.7s).
  3. [x] Dọn dẹp thư mục rỗng `demo_ui/`.

### [P1-2] Cảnh Báo Nhẹ Khi Thiếu Cột Chi Phí Trên Giao Diện [HOÀN THÀNH]
- **Mô tả:** Tệp dữ liệu mẫu chuẩn của dự án (`sample_dashboard_feed.csv`) đã có sẵn cột `cost`. Tuy nhiên, nếu người dùng tải lên tệp tùy ý thiếu cột `cost`, hệ thống sẽ tự động suy đoán chi phí từ doanh thu.
- **Tiêu chí hoàn thành (Acceptance Criteria):**
  1. [x] Backend `/datasets/analyze` tự động phát hiện tệp thiếu cột chi phí/giá vốn thực tế và trả về trường `cost_estimated: true`.
  2. [x] Trên giao diện Frontend, nếu phát hiện dữ liệu thiếu cột giá vốn, hiển thị nhãn chú thích nhẹ bên cạnh thẻ KPI: *"⚠️ Chi phí được ước tính tự động từ doanh thu do tệp thiếu cột giá vốn"* và nhãn *"⚠️ Chi phí ước tính"* trên thẻ lợi nhuận.

### [P1-3] Xây Dựng Chức Năng Kiểm Nghiệm Dữ Liệu Độc Lập (Pre-flight Data Audit Sandbox) [HOÀN THÀNH]
- **Mô tả:** Thay thế hoàn toàn tab "Dữ liệu tổng hợp" bằng tab "Kiểm nghiệm dữ liệu" (Data Audit) hoạt động như một **Sandbox kiểm thử độc lập**, cho phép người dùng tải lên và kiểm tra chất lượng tệp dữ liệu trước khi quyết định nạp vào Dashboard để vẽ biểu đồ.
- **Tiêu chí hoàn thành (Acceptance Criteria):**
  1. [x] **Backend:** Mở rộng `quality_checker.py`, `QualityResponse` và bổ sung endpoint `POST /datasets/audit` (nhận tệp raw bytes kiểm nghiệm độc lập, không ghi đè session). Cung cấp chi tiết 4 trụ cột chất lượng (Completeness, Uniqueness, Invariants/Validity, Outliers), cấp bậc (Tier A - D), danh sách dòng vi phạm chi tiết (`violations`) và khuyến nghị khắc phục (`recommendations`).
  2. [x] **Frontend Sandbox:** Xây dựng khung tải tệp riêng biệt trong tab Kiểm nghiệm; cách ly dữ liệu kiểm thử (`state.audit`) hoàn toàn với dữ liệu Dashboard (`state.rows`).
  3. [x] **Cầu nối nạp Dashboard:** Cung cấp nút **"🚀 Đưa vào Dashboard"** để chuyển dữ liệu đã kiểm định đạt chuẩn sang Dashboard chỉ bằng một cú nhấp chuột.
  4. [x] **Kiểm thử:** Bổ sung test kiểm tra `POST /datasets/audit` và các trường audit; toàn bộ test suite chạy đạt 100% PASS.

---

## Mức Độ Ưu Tiên P2: Kế Hoạch Tiếp Theo (Upcoming Tasks)

### [P2-1] Nhúng Biểu Đồ Trực Quan Vào File Báo Cáo Xuất (PDF / HTML) [CHỜ LÀM]
- **Mô tả:** Hiện tại chức năng xuất báo cáo mới chỉ hiển thị bảng tóm tắt KPI; cần hỗ trợ xuất kèm hình ảnh biểu đồ SVG/PNG trong báo cáo PDF và HTML.
- **Tiêu chí hoàn thành (Acceptance Criteria):**
  1. [ ] Frontend gửi SVG snapshot hoặc Backend tự kết xuất đồ thị sang định dạng ảnh tương thích ReportLab.
  2. [ ] File PDF và HTML tải về hiển thị đầy đủ thẻ KPI kèm biểu đồ trực quan xu hướng.

### [P2-2] Quản Trị Danh Sách Người Dùng Toàn Diện Trên Giao Diện Admin [CHỜ LÀM]
- **Mô tả:** Hiện tại màn hình Admin phải gõ mã nhân viên thủ công để đổi quyền; cần giao diện bảng danh sách trực quan.
- **Tiêu chí hoàn thành (Acceptance Criteria):**
  1. [ ] API `GET /admin/users` trả về danh sách tài khoản hiện có cùng trạng thái kích hoạt và role.
  2. [ ] Giao diện Admin hiển thị bảng tài khoản, cho phép đổi vai trò (`admin`, `manager`, `user`) trực tiếp qua dropdown.

### [P2-3] Tối Ưu Ngữ Cảnh Cho Trợ Lý AI (Chatbot RAG Trực Quan) [CHỜ LÀM]
- **Mô tả:** Tinh chỉnh prompt và lược trích ngữ cảnh từ dữ liệu Dashboard hiện hành khi người dùng đặt câu hỏi phân tích kinh doanh.
- **Tiêu chí hoàn thành (Acceptance Criteria):**
  1. [ ] Khi dataset có nhiều dòng, tự động tóm tắt các chiều phân tích quan trọng (Top 5 sản phẩm, ngày biến động mạnh nhất) gửi cho LLM.
  2. [ ] Đảm bảo câu trả lời phản ánh đúng số liệu đang hiển thị trên biểu đồ của người dùng.

---

## Danh Mục Đã Lược Bỏ (Out of Scope Cho Môi Trường Local)

Các hạng mục sau được chính thức lược bỏ khỏi backlog để giữ hệ thống đơn giản, nhẹ máy và dễ vận hành trên thiết bị cá nhân:
1. **Phân quyền chi tiết `permissions` & phân vùng `data_scope`:** Hệ thống hiện tại đã có phân quyền theo 3 vai trò (`admin`, `manager`, `user`) hoạt động chuẩn xác ở cả backend lẫn frontend, hoàn toàn đủ cho nhu cầu nội bộ.
2. **Hệ thống hàng đợi bất đồng bộ Celery / Redis:** Không yêu cầu các thành viên cài đặt thêm Redis server hay worker nền trên máy Windows/macOS. Các tác vụ synthetic data local chỉ chạy với mô hình `bootstrap` hoặc sample kích thước vừa phải ($100 - 500$ dòng).
3. **Giám sát chi phí & Giới hạn Token LLM:** Mỗi thành viên tự quản lý khóa API cá nhân trong tệp `.env` hoặc dùng chế độ `deterministic` miễn phí; không xây dựng logic đo lường phức tạp trong mã nguồn.
4. **Cơ chế khóa tài khoản `DISABLED` và kiểm toán phức tạp:** Không cần thiết cho nhóm phát triển local với số lượng tài khoản đếm trên đầu ngón tay.
