# STATUS.md — Hiện Trạng Từng Tính Năng & Rủi Ro Kỹ Thuật

> **Ngày cập nhật:** 01/11/2026  
> **Tình trạng kiểm toán:** Toàn diện mã nguồn, kiểm tra cơ sở dữ liệu SQLite và chạy các bộ test thực tế.

---

## 1. Bảng Trạng Thái Tính Năng Chi Tiết

| # | Phân Hệ / Tính Năng | Trạng Thái | Mô Tả Hiện Trạng & Ghi Chú Kỹ Thuật |
|---|---|:---:|---|
| **I** | **Xác thực & Phân quyền (Auth & RBAC)** | | |
| 1.1 | Gửi yêu cầu đăng ký (`/auth/register-request`) | **Xong** | Lưu vào `registration_requests` với trạng thái `PENDING`. Có kiểm tra trùng lặp `employee_id`. |
| 1.2 | Duyệt / Từ chối yêu cầu đăng ký | **Xong** | Chỉ admin có quyền. Từ chối bắt buộc có `rejection_reason`. Phê duyệt tự động upsert thông tin vào bảng `employees`. |
| 1.3 | Cấp phát tài khoản (`/admin/users/provision`) | **Xong** | Tạo tài khoản trạng thái `PENDING_ACTIVATION` với mật khẩu tạm thời mã hóa PBKDF2. |
| 1.4 | Đăng nhập & Đổi mật khẩu kích hoạt | **Xong** | Cấp `activation_token` (hạn 10 phút), endpoint `/auth/activate` cập nhật trạng thái `ACTIVE` và tăng `token_version`. |
| 1.5 | Cấp & xác thực Access Token JWT | **Xong** | Tự triển khai thuật toán HS256 chuẩn. Mọi request đối chiếu trạng thái user trong DB và kiểm tra `token_version`. |
| 1.6 | Phân quyền theo vai trò (Role-based: admin/manager/user) | **Xong** | Thực thi đúng tại các router chính (`admin_only`, `manager_or_admin`, `current_user`). |
| 1.7 | Phân quyền theo quyền hạn chi tiết (`permissions`) | **Hoãn lại (Deferred)** | Các quyền (`report:export`, `chat:use`,...) được lưu nhưng hoãn kiểm tra riêng lẻ. Hệ thống kiểm soát hoàn toàn theo 3 vai trò (Role-based), đủ cho môi trường local. |
| 1.8 | Phân vùng phạm vi dữ liệu (`data_scope`) | **Hoãn lại (Deferred)** | Dữ liệu dashboard xử lý in-memory theo từng phiên; hoãn lại tính năng lọc theo phòng ban cho đến khi có cơ sở dữ liệu lưu trữ dataset tập trung. |
| 1.9 | Đổi vai trò người dùng (`/auth/users/{id}/role`) | **Chạy một phần** | Cập nhật được role và tăng `token_version`; chưa ghi audit log, chưa chặn việc tự hạ quyền admin cuối cùng. |
| 1.10 | Khóa tài khoản / Đặt lại mật khẩu / Refresh Token | **Chưa có** | Đã có trường `status = 'DISABLED'` trong DB nhưng chưa có API endpoint quản trị hoặc cơ chế refresh token. |
| **II** | **Xử Lý Dữ Liệu & Dashboard (Data Pipeline & BI)** | | |
| 2.1 | Đọc tệp CSV/JSON thô (`/datasets/analyze`) | **Xong** | Parser CSV tùy chỉnh chống lỗi dấu nháy và ký tự đặc biệt, ánh xạ bí danh cột tiếng Việt/Anh sang chuẩn canonical. |
| 2.2 | Đánh giá chất lượng dữ liệu (Quality Check & EDA) | **Xong** | Kiểm tra null, duplicate, outlier, tính toán ma trận tương quan và phân phối cột. |
| 2.3 | Suy luận cấu trúc và quan hệ (`/schema/infer-relations`) | **Xong** | Dự đoán kiểu dữ liệu, ứng viên khóa chính (PK) và khóa ngoại (FK) giữa nhiều bảng. |
| 2.4 | Tính toán chỉ số KPI E-commerce | **Xong** | Tính đúng Doanh thu, Chi phí, Lợi nhuận, AOV; CAC/ROAS khi có `ad_spend`/`new_customers`. Khi thiếu cột giá vốn, hệ thống trả cờ `cost_estimated: true` và Frontend hiển thị cảnh báo trực quan cho người dùng. |
| 2.5 | Cấu hình biểu đồ trực quan (Charts API) | **Xong** | Sinh cấu hình biểu đồ trung lập (Doanh thu theo ngày, Top sản phẩm, Cơ cấu doanh thu) cho Frontend vẽ SVG. |
| 2.6 | Lọc dữ liệu báo cáo & Xuất báo cáo đa định dạng | **Chạy một phần** | Hỗ trợ 6 định dạng (JSON, CSV, HTML, PDF, XLSX, PPTX). Nội dung xuất hiện mới chỉ tóm tắt bảng KPI, chưa nhúng biểu đồ. |
| 2.7 | Kiểm nghiệm dữ liệu độc lập (Data Audit Sandbox) | **Xong** | Cho phép upload kiểm tra chất lượng tệp độc lập (POST /datasets/audit), không ghi đè Dashboard. Phân hạng chất lượng Tier A-D, bắt dòng vi phạm luật kinh doanh và nút "🚀 Đưa vào Dashboard". |
| **III** | **Trí Tuệ Nhân Tạo & Trợ Lý Phân Tích (AI & LLM)** | | |
| 3.1 | LLM Router đa nhà cung cấp | **Xong** | Hỗ trợ `deterministic`, `openai`, `gemini`, `llama`. Tự động fallback về chế độ ngoại tuyến khi gặp lỗi mạng/API. |
| 3.2 | Trợ lý hỏi đáp Dashboard (RAG Engine) | **Chạy một phần** | Ở chế độ `deterministic` chỉ trả về 1 câu mẫu cố định. Khi kết nối LLM thật chưa có cơ chế cắt tỉa ngữ cảnh lớn. |
| 3.3 | Text-to-SQL an toàn | **Chỉ có khung** | Sinh câu lệnh SQL và áp bộ lọc regex an toàn (`SELECT` only, allowlist cột/bảng). **Chưa thực thi câu lệnh** lên DB thật. |
| 3.4 | Giám sát chi phí & Giới hạn Token LLM | **Chưa có** | Chưa có bộ đếm token, chưa có hạn mức theo ngày/người dùng hay lưu vết chi phí phát sinh. |
| **IV** | **Dữ Liệu Tổng Hợp (Synthetic Data Engine)** | | |
| 4.1 | Sinh dữ liệu mô hình `bootstrap` | **Xong** | Hoạt động tốt với thư viện cơ bản, hoán vị dữ liệu có kiểm soát và ẩn danh hóa ID cá nhân. |
| 4.2 | Sinh dữ liệu mô hình nâng cao (`sdv`: CTGAN, CopulaGAN) | **Chạy một phần** | Code đã sẵn sàng nhưng môi trường chưa cài gói `sdv` (trong `requirements-ai.txt`). Chạy đồng bộ dễ quá hạn timeout. |
| 4.3 | Sinh dữ liệu qua `llm_agent` | **Chạy một phần** | Logic xử lý prompt và parse JSON hoàn thiện, đã có unit test qua mock adapter. |
| 4.4 | Kiểm định chất lượng 3 chiều (Fidelity/Privacy/Utility) | **Xong** | Đo khoảng cách Wasserstein, Jensen-Shannon, DCR bảo mật và TSTR kiểm tra giá trị phân tích. |
| 4.5 | Động cơ kịch bản độc lập (`data/engine/generator/api`) | **Xong** | Đã sửa đường dẫn dữ liệu, cập nhật module import chuẩn `uvicorn.run`, toàn bộ 40/40 test trong `data/tests/` PASS (bao gồm cả `test_08_synthetic_api.py`). |
| **V** | **Giao Diện Người Dùng (Frontend SPA)** | | |
| 5.1 | Khung giao diện, layout hai cột, điều hướng, themes | **Xong** | Thiết kế nhẹ nhàng bằng CSS thuần, tải nhanh, không cần npm build. |
| 5.2 | Luồng màn hình Auth, Dashboard, Chat, Reports, Admin | **Xong** | Xử lý đầy đủ các tương tác người dùng, render biểu đồ SVG trực tiếp và tải báo cáo dạng Blob an toàn. |
| 5.3 | Quản trị nhân viên toàn diện | **Chưa có** | Chưa có danh sách toàn bộ nhân viên; UI hiện phải nhập mã thủ công khi đổi role. |
| 5.4 | Thư mục `demo_ui/` | **Đã dọn dẹp** | Đã xóa thư mục rỗng `demo_ui/`, làm sạch cấu trúc dự án. |

---

## 2. Báo Cáo Kiểm Thử Thực Tế (Test Execution Matrix)

| Bộ Kiểm Thử | Tệp Kiểm Thử | Số Lượng | Kết Quả | Ghi Chú & Nhận Xét |
|---|---|:---:|:---:|---|
| **Backend Core** | `tests/test_backend.py` | 12 | **PASS (12/12)** | Chạy xong trong ~0.5s. Kiểm tra logic auth, RBAC, hash, LLM router mock, report exporters, text-to-sql regex. |
| **Data Engine & API** | `data/tests/test_01...08` | 40 | **PASS (40/40)** | Chạy xong trong ~8.7s. Kiểm tra tính toán phân phối, luật kinh doanh, auto-repair, benchmark data, quality gate và API sinh dữ liệu độc lập. |
| **Frontend Core** | `Frontend/tests/core.test.mjs` | 8 | **PASS (8/8)** | Chạy xong trong ~0.1s (Node.js). Kiểm tra bộ lọc ngày, ánh xạ cột alias, xử lý lỗi API và chart bucketing. |
| **Backend Integration** | `tests/test_api.py` | 6 | **PASS (6/6 suites)** | Chạy xong trong ~2.5s. Kiểm tra toàn bộ luồng public guards, CORS, workflow phê duyệt/kích hoạt, role matrix, private analytics (bao gồm cờ cost_estimated) và sanitized errors. |

---

## 3. Các Rủi Ro Bảo Mật & Kỹ Thuật Đã Ghi Nhận

1. **Khóa bí mật mặc định (ĐÃ KHẮC PHỤC - Task P0-1):**
   - Đã loại bỏ hoàn toàn chuỗi tĩnh `"development-only-change-me-32-chars"` khỏi `backend/config.py`.
   - Cơ chế nạp `.env` tự động sinh persistent secret an toàn cho local và bắt buộc `RuntimeError` nếu production thiếu secret $\ge 32$ ký tự.
2. **Lỗi treo bộ test tích hợp (ĐÃ KHẮC PHỤC - Task P0-2):**
   - Đã tinh chỉnh vòng đời `TestClient` và cô lập biến môi trường JWT trong tests, đạt 100% PASS trong 2.5s.
3. **Trùng lặp và phân mảnh mã nguồn (ĐÃ KHẮC PHỤC - Task P1-1):**
   - Đã chuẩn hóa duy nhất thư mục `semantic/` và `eval/` tại thư mục gốc làm Single Source of Truth; loại bỏ bản sao trong `data/engine/`.
   - Đã xóa thư mục rỗng `demo_ui/` và sửa đường dẫn import, dữ liệu trong `standalone_server.py` và `router.py`.
4. **Cảnh báo thiếu cột chi phí (ĐÃ KHẮC PHỤC - Task P1-3):**
   - Hệ thống phát hiện khi tệp thiếu cột giá vốn, trả về trường `cost_estimated: true` và Frontend hiển thị cảnh báo rõ ràng cho người dùng.
5. **Phân quyền chi tiết phía Server (Đã đánh giá & phân loại):**
   - Server hiện kiểm tra theo vai trò (`admin`, `manager`, `user`). Các trường `permissions` và `data_scope` chưa được kiểm tra riêng lẻ ở từng route nghiệp vụ, nhưng mức độ kiểm soát theo vai trò hiện tại đã đáp ứng đầy đủ yêu cầu cho môi trường chạy local / thử nghiệm nội bộ (không coi là blocker).

