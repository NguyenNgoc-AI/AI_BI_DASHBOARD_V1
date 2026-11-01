# PROJECT.md — Mục Tiêu Dự Án AI BI Dashboard

Tài liệu này là nguồn sự thật duy nhất (Single Source of Truth) định nghĩa mục tiêu, phạm vi người dùng, tiêu chuẩn hoàn thành và các ranh giới loại trừ của dự án **AI BI Dashboard (v2)**.

---

## 1. Mục Tiêu Dự Án (Project Goal)

Xây dựng hệ thống **AI Business Intelligence (BI) Dashboard** tinh gọn, chạy được cả offline và online, phục vụ doanh nghiệp thương mại điện tử (E-commerce) và bán lẻ:
- **Chuẩn hóa & Phân tích dữ liệu tự động:** Nhập tệp CSV/JSON thô, tự động phát hiện kiểu dữ liệu, đánh giá chất lượng (missing, duplicates, outliers), suy luận schema và quan hệ bảng.
- **Tính toán chỉ số kinh doanh chuẩn xác:** Cung cấp tức thời các chỉ số tài chính cốt lõi (Doanh thu, Giá vốn, Lợi nhuận ròng, AOV, CAC, ROAS, LTV) và biểu đồ trực quan (xu hướng thời gian, top sản phẩm, cơ cấu danh mục).
- **Trợ lý AI phân tích & Text-to-SQL an toàn:** Cho phép hỏi đáp tự nhiên trên dữ liệu kinh doanh hiện tại với cơ chế RAG có rào chắn bảo mật dữ liệu (`<untrusted_data>`) và bộ sinh truy vấn SQL chỉ đọc.
- **Sinh dữ liệu tổng hợp (Synthetic Data):** Tạo dữ liệu giả lập phục vụ kiểm thử, đào tạo hoặc phân tích theo kịch bản thị trường (baseline, tăng trưởng, mùa lễ hội) đi kèm bộ đánh giá chất lượng 3 chiều (Fidelity, Privacy, Utility).
- **Bảo mật & Phân quyền chuẩn doanh nghiệp:** Quy trình cấp phát tài khoản có phê duyệt nội bộ, xác thực hai pha (mật khẩu tạm $\rightarrow$ kích hoạt $\rightarrow$ token chính thức) và phân quyền theo vai trò (RBAC).

---

## 2. Chân Dung Người Dùng (Target Personas)

1. **Nhân viên / Chuyên viên phân tích (Role: `user`)**
   - **Nhu cầu:** Tải lên tệp doanh số bán hàng, xem báo cáo tổng quan, phân tích chất lượng dữ liệu, lọc báo cáo theo ngày/sản phẩm, đặt câu hỏi cho trợ lý AI, xuất báo cáo đa định dạng (PDF, Excel, PPTX, HTML, CSV, JSON).
   - **Giới hạn:** Không được cấu hình hệ thống, không sinh dữ liệu tổng hợp, không quản lý người dùng.
2. **Quản lý kinh doanh (Role: `manager`)**
   - **Nhu cầu:** Xem toàn bộ chỉ số tài chính, sử dụng công cụ sinh dữ liệu mô phỏng thị trường (`/synthetic/*`) để lập kế hoạch kinh doanh hoặc thử nghiệm chiến dịch mà không ảnh hưởng dữ liệu thật.
   - **Giới hạn:** Không duyệt hoặc cấp phát tài khoản nhân sự.
3. **Quản trị viên hệ thống (Role: `admin`)**
   - **Nhu cầu:** Tiếp nhận và duyệt/từ chối yêu cầu cấp tài khoản của nhân viên, phân quyền và cấp mật khẩu tạm thời, điều chỉnh vai trò người dùng, giám sát audit log và cấu hình hệ thống.
   - **Đặc quyền:** Toàn quyền truy cập mọi tính năng kỹ thuật và quản trị.

---

## 3. Định Nghĩa "Thế Nào Là Xong" (Definition of Done - DoD)

Một tính năng hoặc phiên bản được coi là "Xong" khi thỏa mãn đầy đủ các tiêu chuẩn sau:

### 3.1 Về Chức Năng (Functional DoD)
- [ ] Mọi endpoint API có Pydantic schema chặt chẽ (`extra="forbid"`), trả về mã HTTP chuẩn RESTful và xử lý lỗi đồng nhất (`error.code`, `error.message`, `request_id`).
- [ ] Dữ liệu đầu vào CSV/JSON được làm sạch, chuẩn hóa kiểu ngày tháng và giá trị số học, từ chối dữ liệu vô hạn hoặc âm ở các trường doanh thu/chi phí bắt buộc.
- [ ] Công thức tính toán KPI tài chính tuân thủ 100% luật nghiệp vụ xác định trong `semantic/business_rules.py`.
- [ ] Giao diện người dùng (Frontend) phản ánh chính xác kết quả từ API thật; có trạng thái chờ (loading spinner), thông báo lỗi rõ ràng và xử lý escape HTML toàn diện chống XSS.

### 3.2 Về Bảo Mật & Phân Quyền (Security DoD)
- [ ] Không hardcode secret, API key hay mật khẩu thật trong mã nguồn hoặc file mẫu commit vào repo.
- [ ] Bắt buộc xác thực Bearer Token còn hạn và kiểm tra `token_version` trong cơ sở dữ liệu đối với mọi endpoint private.
- [ ] Phân quyền theo vai trò (Role-based: `admin`, `manager`, `user`) được kiểm tra trực tiếp ở tầng Backend (server-side enforcement), không dựa dẫm vào việc Frontend ẩn/hiện nút.
- [ ] Text-to-SQL chỉ cho phép câu lệnh `SELECT`, giới hạn tối đa `LIMIT 500`, chặn mọi lệnh can thiệp cấu trúc hoặc thay đổi dữ liệu.

### 3.3 Về Kiểm Thử & Vận Hành (Quality DoD)
- [ ] Toàn bộ bộ test đơn vị (`tests/test_backend.py`), bộ test API (`tests/test_api.py`), test data engine (`data/tests/`) và frontend test (`core.test.mjs`) chạy qua và có kết quả PASS 100%.
- [ ] Hệ thống có thể khởi động và hoạt động trơn tru ở chế độ ngoại tuyến (`LLM_PROVIDER=deterministic`) mà không cần phụ thuộc Internet.

---

## 4. Những Thứ KHÔNG Làm (Non-Goals & Out of Scope)

Để giữ dự án tập trung vào giá trị cốt lõi của một hệ thống AI BI MVP vận hành mượt mà trên máy cá nhân của các thành viên, các hạng mục sau **tuyệt đối không triển khai**:

1. **Không làm hệ thống Quản lý Nhân sự (HRM) / Chấm công / Tiền lương đầy đủ:**
   - Hệ thống chỉ quản lý tài khoản truy cập dashboard thông qua `employee_id`. Không mở rộng thành phần mềm nhân sự, bảng lương hay sơ đồ tổ chức phòng ban.
2. **Không làm Đăng ký tự do (Self-signup) hoặc Đăng nhập mạng xã hội (OAuth Google/Facebook):**
   - Chỉ áp dụng quy trình cấp phát nội bộ: Gửi yêu cầu $\rightarrow$ Admin duyệt $\rightarrow$ Admin provision $\rightarrow$ Nhân viên kích hoạt.
3. **Không làm Kho lưu trữ đám mây phân tán đa người dùng (Multi-tenant Cloud Storage):**
   - Dữ liệu phân tích hoạt động theo cơ chế in-memory/stateless trên từng phiên làm việc của người dùng, không xây dựng hạ tầng object storage S3/GCS phức tạp cho phiên bản này.
4. **Không thực thi trực tiếp câu lệnh ghi/xóa lên cơ sở dữ liệu từ Chatbot AI:**
   - Chatbot và Text-to-SQL chỉ là công cụ phân tích trợ giúp. Hệ thống không bao giờ tự động chạy các lệnh `INSERT`, `UPDATE`, `DELETE`, `DROP` do AI sinh ra.
5. **Không đưa toàn bộ framework Frontend nặng (React/Next.js/Vue/Angular) vào dự án:**
   - Giao diện duy trì cấu trúc Vanilla HTML/CSS/ES Modules siêu nhẹ, không cần build-step (`npm build`), phục vụ trực tiếp qua máy chủ HTTP tĩnh.
6. **Không tự động suy đoán chi phí ngầm nếu không có sự đồng ý của người dùng:**
   - Sẽ minh bạch hóa mọi ước lượng chi phí khi thiếu cột, không ngầm tạo ra con số lợi nhuận giả định mà không dán nhãn cảnh báo.
7. **Không triển khai cụm hàng đợi bất đồng bộ Celery / Redis:**
   - Giữ môi trường nhẹ máy, không bắt buộc các thành viên cài đặt Redis server hay chạy worker nền trên Windows/macOS.
8. **Không làm phân quyền vi mô (Granular Permissions) & Phân vùng dữ liệu (Data Scope):**
   - Dựa trên 3 vai trò rõ ràng (`admin`, `manager`, `user`). Việc chia nhỏ quyền hạn chi tiết và quản lý multi-tenant data scope được hoãn lại cho đến khi có cơ sở dữ liệu lưu trữ dataset tập trung.
9. **Không làm hệ thống giám sát chi phí/hạn mức gọi API LLM (Rate-limiting & Token metering):**
   - Ở môi trường máy cá nhân, mỗi thành viên tự quản lý khóa API cá nhân trong tệp `.env` hoặc sử dụng chế độ `deterministic` miễn phí.

