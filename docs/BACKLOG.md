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

### [P1-4] Chuẩn Hóa & Tự Động Hóa Dựng Dashboard Theo 3 Cơ Chế Đa Chiều & DESIGN.md [HOÀN THÀNH]
- **Mô tả:** Triển khai tự động hóa dựng Dashboard và phân bổ 3 cơ chế hiển thị trên 2 tab Tổng quan và Báo cáo theo đúng bộ quy chuẩn thiết kế [`docs/DESIGN.md`](./DESIGN.md) (ADR-10).
- **Tiêu chí hoàn thành (Acceptance Criteria):**
  1. [x] **Backend (`chart_generator.py`):** Bổ sung bộ lọc quyết định chọn biểu đồ tự động (Line nếu $\ge 7$ mốc, Column nếu $\le 6$ mốc; giới hạn Donut $\le 5$ lát, tự động chuyển đổi sang Horizontal Sorted Bar có baseline = 0 nếu $> 5$ danh mục; tự động gộp nhóm "Khác" nếu $> 15$ danh mục). Đính kèm metadata chỉ định `palette_slot` và `measure_family`.
  2. [x] **Tab Tổng quan (Cơ chế 1 & 2):**
     - *Cơ chế 1 (Metric Switcher):* Thanh chọn nhanh các chỉ số số thực có trong file (`revenue, cost, quantity, profit, discount...`). Bấm chọn chỉ số nào thì toàn bộ 4 thẻ KPI và biểu đồ trục $Y$ chuyển sang chỉ số đó; màu sắc đồng bộ theo bảng màu Okabe-Ito.
     - *Cơ chế 2 (Breakdown đa chiều):* Hiển thị biểu đồ thanh ngang cho các chiều danh mục chính (Sản phẩm, Vùng miền, Kênh), tự động nhảy số theo chỉ số chọn ở Cơ chế 1.
  3. [x] **Tab Báo cáo (Cơ chế 3):**
     - Thay thế các khối JSON thô bằng lưới thẻ trực quan *Data Distribution Explorer* cho 100% các cột (Mini Histogram cho cột số, Data Bars cho cột danh mục).
  4. [x] **Kiểm thử:** Đảm bảo toàn bộ test suite frontend và backend đạt 100% PASS, nhãn chữ đạt chuẩn tương phản WCAG 2.1 AA.

### [P1-5] Nâng Cấp Chatbot Cô Lập Thành Local Semantic Intent Engine (4 Nhóm Hỏi Đáp & Zero Mutation) [HOÀN THÀNH]
- **Mô tả:** Tái cấu trúc lớp chatbot thành chuyên gia đọc vị biểu đồ nội bộ (ADR-11), đảm bảo cô lập 100% không thể can thiệp hay sửa đổi Dashboard chính, khắc phục triệt để lỗi hỏi gì cũng trả về 1 câu doanh thu.
- **Tiêu chí hoàn thành (Acceptance Criteria):**
  1. [x] **Ranh giới cô lập (Zero Mutation):** Endpoint `/chat/query` và giao diện chat hoạt động hoàn toàn ở chế độ Read-only; cấm tuyệt đối mọi logic ghi đè hay thay đổi `state.rows` / `state.filter`.
  2. [x] **Local Semantic Intent Engine (`llm_router.py`):** Nâng cấp `DeterministicAdapter` thành bộ máy phân loại ý định nội bộ chạy local 100% miễn phí, phản hồi tức thì (< 2ms), bao quát chuẩn xác 4 nhóm:
     - *Chào hỏi & Hướng dẫn:* Chào mừng thân thiện, giới thiệu chức năng.
     - *Công thức tính toán:* Giải thích cặn kẽ công thức AOV, Net Profit, Gross/Net Sales, Margin, COGS.
     - *Truy vấn Dashboard:* Bóc tách chính xác từng chỉ số KPI hoặc sản phẩm theo đúng câu hỏi.
     - *Từ chối ngoài phạm vi:* Câu hỏi ngoài lề được trả về nguyên văn: *"Yêu cầu này không nằm trong phạm vi hỏi đáp của trợ lý dữ liệu Dashboard."*
  3. [x] **Kiểm thử tích hợp:** Viết unit test và API test kiểm tra cả 4 kịch bản hỏi đáp, đạt 100% PASS.

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

### [P2-3] Mở Rộng Quy Tắc E-commerce Rules & Benchmark Metrics Cho Dashboard [CHỜ LÀM]
- **Mô tả:** Bổ sung thêm các chỉ số và ngưỡng cảnh báo ngành (ví dụ: Tỷ lệ hoàn đơn, Chi phí vận chuyển / Doanh thu) vào bộ luật nghiệp vụ `semantic/business_rules.py`.
- **Tiêu chí hoàn thành (Acceptance Criteria):**
  1. [ ] Mở rộng tính toán các chỉ số bổ trợ khi file đầu vào có các cột tương ứng.
  2. [ ] Hiển thị cảnh báo trực quan khi chỉ số vượt ngưỡng an toàn theo chuẩn ngành E-commerce.

---

## Danh Mục Đã Lược Bỏ (Out of Scope Cho Môi Trường Local)

Các hạng mục sau được chính thức lược bỏ khỏi backlog để giữ hệ thống đơn giản, nhẹ máy và dễ vận hành trên thiết bị cá nhân:
1. **Phân quyền chi tiết `permissions` & phân vùng `data_scope`:** Hệ thống hiện tại đã có phân quyền theo 3 vai trò (`admin`, `manager`, `user`) hoạt động chuẩn xác ở cả backend lẫn frontend, hoàn toàn đủ cho nhu cầu nội bộ.
2. **Hệ thống hàng đợi bất đồng bộ Celery / Redis:** Không yêu cầu các thành viên cài đặt thêm Redis server hay worker nền trên máy Windows/macOS. Các tác vụ synthetic data local chỉ chạy với mô hình `bootstrap` hoặc sample kích thước vừa phải ($100 - 500$ dòng).
3. **Giám sát chi phí & Giới hạn Token LLM:** Mỗi thành viên tự quản lý khóa API cá nhân trong tệp `.env` hoặc dùng chế độ `deterministic` miễn phí; không xây dựng logic đo lường phức tạp trong mã nguồn.
4. **Cơ chế khóa tài khoản `DISABLED` và kiểm toán phức tạp:** Không cần thiết cho nhóm phát triển local với số lượng tài khoản đếm trên đầu ngón tay.
