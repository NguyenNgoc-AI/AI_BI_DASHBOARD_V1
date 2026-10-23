# KẾ HOẠCH TỔNG HỢP: TRIỂN KHAI FRONTEND VÀ HOÀN THIỆN DỰ ÁN AI BI DASHBOARD

> **Dự án:** Code Candy – AI BI Dashboard & Synthetic Data Generator  
> **Thư mục dự án:** `Synthetic/`  
> **Cập nhật:** 23/10/2026  
> **Phiên bản:** v1.0.0 (Master Execution Plan)  
> **Phạm vi tài liệu:**  
> 1. Kế hoạch chi tiết chuyển đổi & tích hợp Frontend khớp 100% kiến trúc dự án (React + Vite + TailwindCSS).  
> 2. Kế hoạch thực hiện các bước tiếp theo hoàn thiện toàn bộ project từ Backend, AI Engine đến Đóng gói nghiệm thu.  
> 3. Hướng dẫn lệnh Terminal & Link kiểm thử giao diện thực tế cho từng bước can thiệp.

---
**Tuân thủ ANTIGRAVITY_RULES

## I. THIẾT LẬP LỆNH TERMINAL VÀ ĐỊA CHỈ KIỂM THỬ HỆ THỐNG

Trước khi tiến hành và sau mỗi bước can thiệp mã nguồn, sử dụng hai terminal độc lập để chạy và kiểm tra hệ thống:

* **Terminal 1: Khởi chạy Backend Server (FastAPI)**
  ```powershell
  uvicorn backend.main:app --reload --port 8000
  ```
  * **Link Swagger API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
  * **Link Health Check API:** [http://localhost:8000/health](http://localhost:8000/health)

* **Terminal 2: Khởi chạy Frontend Web**
  * *Bản Vanilla JS hiện tại:*
    ```powershell
    python frontend/serve.py
    ```
  * *Bản React + Vite chuẩn:*
    ```powershell
    cd frontend
    npm run dev
    ```
  * **Link Giao diện Web chính:** [http://localhost:5173](http://localhost:5173)

---

## II. KẾ HOẠCH 1: THỰC HIỆN FRONTEND KHỚP VỚI HỆ THỐNG DỰ ÁN

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             LỘ TRÌNH 8 BƯỚC TRIỂN KHAI FRONTEND REACT                              │
├─────────┬──────────────────────┬───────────────────────────────────────────────────────┬───────────┤
│ Bước    │ Tên hạng mục         │ Trọng tâm kỹ thuật & Deliverables                     │ Trạng thái│
├─────────┼──────────────────────┼───────────────────────────────────────────────────────┼───────────┤
│ F-01    │ Cấu hình Nền tảng    │ package.json, vite.config.js, TailwindCSS, Alias @    │ ✅ Đạt    │
│ F-02    │ API Client & State   │ Axios client, Interceptor JWT, LocalStorage persist   │ Chờ chạy  │
│ F-03    │ Layout Shell & Auth  │ Sidebar, Topbar, RBAC Guard, Login/Register/Activate  │ Chờ chạy  │
│ F-04    │ Data Ingestion UI    │ Drag-and-drop, Data Quality Scorecard (DQS), Preview  │ Chờ chạy  │
│ F-05    │ BI Dashboard UI      │ 4 KPI Cards, Combo Chart (Recharts/Chart.js), Filter  │ Chờ chạy  │
│ F-06    │ Report & Chatbot UI  │ Chat window, Text-to-SQL view, 6 file export triggers │ Chờ chạy  │
│ F-07    │ Admin & Synthetic UI │ HR review/provisioning, Scenario simulation controls │ Chờ chạy  │
│ F-08    │ Kiểm thử & Build     │ Vitest/Testing Library, build tối ưu bundle           │ Chờ chạy  │
└─────────┴──────────────────────┴───────────────────────────────────────────────────────┴───────────┘
```

### Bước F-01: Khởi tạo môi trường React, Vite và TailwindCSS
- **Mục tiêu:** Thiết lập công cụ đóng gói và giao tiếp proxy.
- **Trạng thái thực hiện:** ✅ Đã hoàn thành (23/10/2026).
- **Kết quả nghiệm thu kỹ thuật:**
  - `frontend/package.json`: Khai báo và cài đặt dependencies `react`, `react-dom`, `react-router-dom`, `axios`, `recharts`, `lucide-react`, `clsx`, `tailwind-merge`, `vite`, `tailwindcss`, `postcss`, `autoprefixer`.
  - `frontend/vite.config.js`: Thiết lập alias `@` trỏ về `frontend/src/`, cấu hình server dev proxy `/api` và `/auth` forward trực tiếp về `http://127.0.0.1:8000`.
  - `frontend/tailwind.config.js` & `frontend/postcss.config.js`: Kế thừa mã màu `primary` (`#5651e8`), `muted` (`#858aa1`), `line` (`#eceef6`), `surface`, `brandBg`, `brandText` theo chuẩn từ `styles.css`.
  - `frontend/src/{main.jsx, App.jsx, index.css}` & `frontend/index.html`: Cấu trúc mount React SPA đã sẵn sàng, kiểm thử lệnh `npm run build` chạy thành công (1588 modules transformed, xuất bản tệp tĩnh `dist/` đạt chuẩn).
- **Thực hiện:**
  - Định nghĩa `frontend/package.json`: dependencies gồm `react`, `react-dom`, `react-router-dom`, `axios`, `recharts` (hoặc `chart.js`), `lucide-react`, `clsx`, `tailwind-merge`.
  - Cấu hình `frontend/vite.config.js`: thiết lập alias `@/` trỏ về `frontend/src/`, cấu hình server dev proxy `/api` và `/auth` forward trực tiếp về `http://127.0.0.1:8000`.
  - Cấu hình TailwindCSS (`tailwind.config.js`, `postcss.config.js`) kế thừa các mã màu từ `frontend/styles.css`.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC F-01]**  
> 1. Chạy lệnh: `cd frontend; npm run dev`.  
> 2. Mở trình duyệt tại [http://localhost:5173](http://localhost:5173).  
> 3. Tương tác thủ công: Kiểm tra trang chủ hiển thị giao diện không bị màn hình đen; mở tab Network (F12) xác nhận các file tài nguyên tĩnh và CSS Tailwind tải thành công.

---

### Bước F-02: Chuẩn hóa tầng HTTP Client và Quản lý trạng thái (State Persistence)
- **Mục tiêu:** Giải quyết lỗi mất phiên làm việc và mất dữ liệu khi reload trang (UI-15).
- **Thực hiện:**
  - Xây dựng module `frontend/src/api/client.js` bằng Axios:
    - Request Interceptor: Tự động đính kèm `Authorization: Bearer <token>` từ `localStorage`.
    - Response Interceptor: Bắt lỗi `401 Unauthorized` để xóa token và chuyển hướng về trang `/login`; bắt lỗi `403 Forbidden` để hiển thị thông báo thiếu quyền.
  - Tách các module API chuyên biệt: `authApi.js`, `dataApi.js`, `dashboardApi.js`, `chatApi.js`, `syntheticApi.js`.
  - Sử dụng Context API hoặc Zustand để lưu trữ `UserContext` và `DatasetContext` (tự động đồng bộ với `sessionStorage` để giữ dữ liệu đang phân tích khi người dùng F5).

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC F-02]**  
> 1. Khởi chạy đồng thời Backend ([http://localhost:8000/docs](http://localhost:8000/docs)) và Frontend ([http://localhost:5173](http://localhost:5173)).  
> 2. Mở Console (F12) trên trình duyệt, gõ lệnh gọi thử API login hoặc ping backend qua axios client.  
> 3. Tương tác thủ công: Lưu thử một biến dữ liệu vào `DatasetContext`, nhấn phím F5 / Reload trang; kiểm tra trong Application -> LocalStorage/SessionStorage xác nhận dữ liệu phiên không bị xóa.

---

### Bước F-03: Xây dựng Layout Shell và Phân hệ Xác thực (Auth & RBAC)
- **Mục tiêu:** Đảm bảo luồng quản lý người dùng theo đúng chuẩn backend.
- **Thực hiện:**
  - Tạo Shell Layout (`frontend/src/components/layout/`): `Sidebar.jsx`, `Header.jsx`, `MainLayout.jsx`.
  - Xây dựng `ProtectedRoute.jsx` kiểm tra quyền theo vai trò (`admin`, `manager`, `user`).
  - Dựng các trang xác thực (`frontend/src/pages/auth/`):
    - `Login.jsx`: Đăng nhập username/password, phân nhánh chuyển hướng sang màn hình kích hoạt nếu nhận token `purpose: "activation"`.
    - `Register.jsx`: Gửi yêu cầu đăng ký (mã nhân viên, họ tên, phòng ban, chức vụ).
    - `Activate.jsx`: Nhập mật khẩu tạm thời và đổi sang mật khẩu chính thức.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC F-03]**  
> 1. Truy cập [http://localhost:5173/login](http://localhost:5173/login).  
> 2. Tương tác thủ công:  
>    - Nhập sai mật khẩu $\rightarrow$ kiểm tra giao diện hiển thị alert cảnh báo lỗi đỏ.  
>    - Nhập tài khoản admin mặc định $\rightarrow$ kiểm tra chuyển hướng vào Dashboard thành công, Header hiển thị tên và badge quyền `admin`.  
>    - Nhấn đăng xuất $\rightarrow$ kiểm tra thanh Sidebar bị ẩn và đưa về lại trang đăng nhập.

---

### Bước F-04: Xây dựng Phân hệ Quản lý & Kiểm định Dữ liệu (Data Ingestion UI)
- **Mục tiêu:** Trực quan hóa kết quả của `GenericDataProfiler` và `GenericQualityChecker`.
- **Thực hiện:**
  - Component `DropZone.jsx`: Tải file `.csv` hoặc `.json` thô gửi trực tiếp dưới dạng `application/octet-stream` tới endpoint `/datasets/analyze`.
  - Component `QualityScorecard.jsx`: Hiển thị thẻ điểm chất lượng 4 khía cạnh (Completeness, Validity, Uniqueness, Consistency), kèm danh sách cột bị lỗi / thiếu dữ liệu.
  - Component `DataPreviewTable.jsx`: Hiển thị bảng dữ liệu có phân trang, hỗ trợ lọc và tìm kiếm cột.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC F-04]**  
> 1. Truy cập [http://localhost:5173/data](http://localhost:5173/data).  
> 2. Tương tác thủ công:  
>    - Kéo thả file chuẩn `data/sample_dataset/ecommerce_seed.csv` vào khung Upload $\rightarrow$ kiểm tra thanh tiến trình loading.  
>    - Kiểm tra Thẻ điểm chất lượng (DQS Scorecard) hiển thị đủ 4 chỉ số phần trăm.  
>    - Chuyển sang bảng Data Preview $\rightarrow$ bấm chuyển trang (Pagination) và gõ tìm kiếm tên sản phẩm xem bảng có lọc đúng dòng không.

---

### Bước F-05: Xây dựng BI Dashboard và Trực quan hóa Tài chính
- **Mục tiêu:** Khớp với các công thức tài chính chuẩn trong `semantic/business_rules.py`.
- **Thực hiện:**
  - `KPICard.jsx`: 4 thẻ chỉ số cốt lõi (Tổng doanh thu, Tổng chi phí, Lợi nhuận ròng, AOV).
  - `RevenueCostChart.jsx`: Biểu đồ cột chồng/đường thể hiện xu hướng doanh thu và chi phí theo thời gian.
  - `TopProductsTable.jsx`: Bảng xếp hạng sản phẩm sinh lời cao nhất.
  - `FilterBar.jsx`: Bộ lọc theo khoảng ngày, phân khúc khách hàng và kênh bán hàng.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC F-05]**  
> 1. Truy cập [http://localhost:5173/dashboard](http://localhost:5173/dashboard).  
> 2. Tương tác thủ công:  
>    - Đối chiếu 4 thẻ KPI với dữ liệu trả về từ API Backend.  
>    - Rê chuột vào các điểm trên biểu đồ Recharts/Chart.js $\rightarrow$ kiểm tra Tooltip hiển thị giá trị tiền tệ VND chính xác.  
>    - Thay đổi bộ lọc ngày trên `FilterBar` $\rightarrow$ kiểm tra biểu đồ và KPI tự động cập nhật số liệu tương ứng.

---

### Bước F-06: Xây dựng Giao diện AI Assistant và Xuất Báo cáo
- **Mục tiêu:** Tích hợp tính năng Text-to-SQL và tải file xuất dữ liệu.
- **Thực hiện:**
  - `AIChat.jsx`: Hộp thoại tương tác AI, hiển thị câu trả lời giải thích số liệu kèm câu truy vấn SQL đã chạy (`/chat/sql`) và khối dữ liệu tham chiếu (`/chat/query`).
  - `ReportExportModal.jsx`: Kích hoạt API `/reports/export` với định dạng tùy chọn (JSON, CSV, HTML, PDF, XLSX, PPTX) và xử lý lưu Blob tự động trên trình duyệt.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC F-06]**  
> 1. Mở khung chat tại [http://localhost:5173/chat](http://localhost:5173/chat).  
> 2. Tương tác thủ công:  
>    - Nhập câu hỏi: *"Tổng doanh thu là bao nhiêu?"* $\rightarrow$ kiểm tra bong bóng chat hiển thị số tiền và khối mã SQL `SELECT SUM(...)`.  
> 3. Mở modal xuất báo cáo tại [http://localhost:5173/reports](http://localhost:5173/reports) $\rightarrow$ nhấn nút tải xuống file PDF và Excel $\rightarrow$ mở file vừa tải trên máy kiểm tra dữ liệu hiển thị không bị rỗng.

---

### Bước F-07: Xây dựng Phân hệ Quản trị (Admin) và Lõi Synthetic Data UI
- **Mục tiêu:** Khớp toàn bộ chức năng quản lý tài khoản và trình sinh dữ liệu của backend.
- **Thực hiện:**
  - `UserManagement.jsx` (Role Admin): Danh sách yêu cầu đăng ký, nút Duyệt/Từ chối, cấp tài khoản và cấu hình phân quyền dữ liệu (`own`, `department`, `all`).
  - `SyntheticControl.jsx` (Role Manager/Admin):
    - Cấu hình sinh dữ liệu: Chọn kịch bản (`baseline`, `holiday_peak`, `flash_sale`), số lượng bản ghi (10 - 100,000 dòng).
    - Trực quan hóa kết quả kiểm định 4 trụ cột (Validity, Fidelity, Privacy, Utility).
    - Gọi API `/api/v1/synthetic/download-csv` để tải file dữ liệu tổng hợp trực tiếp.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC F-07]**  
> 1. Truy cập [http://localhost:5173/admin](http://localhost:5173/admin) bằng tài khoản admin $\rightarrow$ bấm nút Duyệt một yêu cầu đăng ký và cấp mật khẩu tạm.  
> 2. Chuyển sang trang [http://localhost:5173/synthetic](http://localhost:5173/synthetic):  
>    - Chọn kịch bản `holiday_peak`, nhập số dòng `100`, bấm **Sinh dữ liệu**.  
>    - Quan sát 4 thanh đo chất lượng (SQI) hiển thị $\ge 80\%$.  
>    - Bấm nút **Tải CSV** $\rightarrow$ kiểm tra trình duyệt tải về file chứa đúng 100 bản ghi tổng hợp.

---

### Bước F-08: Kiểm thử Giao diện & Đóng gói Build
- **Thực hiện:**
  - Chuyển đổi và nâng cấp 7 ca kiểm thử logic từ `frontend/tests/core.test.mjs` sang Vitest.
  - Chạy `npm run build` để kiểm tra lỗi type/syntax và đảm bảo mã xuất ra thư mục `dist/` sạch sẽ, không có warning bảo mật.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC F-08]**  
> 1. Chạy lệnh: `cd frontend; npm run test; npm run build`.  
> 2. Chạy thử bản production preview: `npm run preview`.  
> 3. Mở [http://localhost:4173](http://localhost:4173) (cổng preview mặc định của Vite) $\rightarrow$ kiểm tra toàn bộ điều hướng các trang hoạt động trơn tru không phát sinh lỗi 404 hay vỡ layout.

---

## III. KẾ HOẠCH 2: CÁC BƯỚC TIẾP THEO ĐỂ HOÀN THIỆN TOÀN BỘ PROJECT

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       LỘ TRÌNH 7 BƯỚC HOÀN THIỆN DỰ ÁN TỔNG THỂ                         │
├─────────┬──────────────────────┬───────────────────────────────────────────────────────┤
│ Bước    │ Trọng tâm hoàn thiện │ Phạm vi kỹ thuật & Mục tiêu đạt được                  │
├─────────┼──────────────────────┼───────────────────────────────────────────────────────┤
│ P-01    │ Persisted Datasets   │ Quản lý lưu trữ tệp & bảng dữ liệu người dùng trên DB │
│ P-02    │ Nâng cấp AI Engine   │ Root Cause Analysis (Task 15) & Local LLM/Gemini API  │
│ P-03    │ Đồng bộ Router API   │ Hợp nhất Synthetic Router và Dashboard Router         │
│ P-04    │ Tích hợp E2E         │ Kết nối luồng hoàn chỉnh giữa React Frontend & Backend│
│ P-05    │ Nghiệm thu Holdout   │ Chạy benchmark độc lập trên real_holdout.csv (15k)    │
│ P-06    │ Bảo mật & Hiệu năng  │ Rate limiting, SQL sanitizer guardrails, CORS strict  │
│ P-07    │ Đóng gói & Tài liệu  │ Docker Compose (Fullstack) & Bộ 3 tài liệu hoàn công  │
└─────────┴──────────────────────┴───────────────────────────────────────────────────────┘
```

### Bước P-01: Bổ sung Cơ chế Lưu trữ Dữ liệu Bền vững (Dataset Persistence)
- **Vấn đề hiện tại:** Backend đang xử lý tệp theo từng request đơn lẻ (stateless in-memory), frontend phải gửi mảng `rows` trong mỗi lần gọi KPI hay Chatbot, gây tốn băng thông và giới hạn dung lượng tải.
- **Thực hiện:**
  - Mở rộng cơ sở dữ liệu SQLite/DuckDB: Tạo các bảng `datasets` (lưu metadata, tên file, người sở hữu, thời gian tạo) và `dataset_records` (lưu các dòng dữ liệu sau khi đã chuẩn hóa qua `data_pipeline.py`).
  - Thêm các API: `GET /datasets`, `GET /datasets/{id}`, `DELETE /datasets/{id}`. Các module KPI và Chatbot chỉ cần nhận `dataset_id` thay vì toàn bộ mảng dữ liệu.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC P-01]**  
> 1. Mở Swagger UI tại [http://localhost:8000/docs](http://localhost:8000/docs) $\rightarrow$ kiểm tra nhóm endpoint `/datasets` mới xuất hiện.  
> 2. Vào giao diện [http://localhost:5173/data](http://localhost:5173/data) $\rightarrow$ upload một file dữ liệu $\rightarrow$ đóng trình duyệt, mở lại trang $\rightarrow$ xác nhận danh sách dataset đã upload vẫn còn lưu trữ trong bảng lịch sử.

---

### Bước P-02: Hoàn thiện AI Root Cause Analysis (Task 15) & Kết nối LLM Thực tế
- **Vấn đề hiện tại:** Chatbot hiện chủ yếu chạy qua `DeterministicAdapter` hoặc mock text, chưa kích hoạt tính năng phát hiện nguyên nhân gốc rễ.
- **Thực hiện:**
  - Hoàn thiện module `backend/chatbot/insight_engine.py`:
    - Sử dụng ma trận tương quan `data/generated/learned_seed_profile.json` để xác định biến động chéo khi một chỉ số thay đổi bất thường (ví dụ: chi phí marketing tăng nhưng doanh thu sụt giảm).
    - Sử dụng danh sách Soft Constraints trong `semantic/rules.json` làm ngưỡng kích hoạt cảnh báo kinh doanh.
  - Cấu hình và kiểm thử kết nối LLM thực tế: Khởi chạy Ollama cục bộ (mô hình `qwen2.5:7b` hoặc `llama3:8b`) hoặc kết nối Google Gemini API qua biến môi trường `.env`.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC P-02]**  
> 1. Truy cập [http://localhost:5173/chat](http://localhost:5173/chat).  
> 2. Tương tác thủ công: Đặt câu hỏi phân tích sâu: *"Tại sao lợi nhuận tháng này giảm dù doanh thu tăng?"*.  
> 3. Kiểm tra phản hồi: Bot chỉ rõ nguyên nhân (chi phí sàn hoặc chi phí marketing vượt ngưỡng cảnh báo), không còn trả về câu văn mẫu cố định của `DeterministicAdapter`.

---

### Bước P-03: Đồng bộ hóa và Chuẩn hóa Hai Nhánh API
- **Vấn đề hiện tại:** Tồn tại hai nhánh endpoint sinh dữ liệu: một nhánh tại `backend/main.py` (`/synthetic/generate`) và một nhánh độc lập tại `backend/synthetic_generator/api/router.py` (`/api/v1/synthetic/*`).
- **Thực hiện:**
  - Hợp nhất các tham số mô phỏng kịch bản (`holiday_peak`, `flash_sale`, `growth_rate`) vào schema chung.
  - Chuẩn hóa tiền tố định tuyến thống nhất: gom toàn bộ về `/api/v1/` để Frontend dễ quản lý proxy.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC P-03]**  
> 1. Mở Swagger UI tại [http://localhost:8000/docs](http://localhost:8000/docs) kiểm tra các route đã quy chuẩn tiền tố `/api/v1/`.  
> 2. Truy cập [http://localhost:5173/synthetic](http://localhost:5173/synthetic) $\rightarrow$ đổi các tùy chọn kịch bản và nhấn sinh dữ liệu $\rightarrow$ mở tab Network (F12) đảm bảo các request gửi về đúng URI `/api/v1/synthetic/generate` và trả mã HTTP 200 OK.

---

### Bước P-04: Tích hợp Toàn diện End-to-End (E2E Integration Testing)
- **Thực hiện:**
  - Kiểm thử chu trình vận hành khép kín trên môi trường tích hợp:
    1. Đăng ký tài khoản $\rightarrow$ Admin duyệt và cấp mật khẩu tạm $\rightarrow$ Người dùng kích hoạt và đổi mật khẩu.
    2. Upload file dữ liệu thô $\rightarrow$ Đạt chuẩn DQS $> 70$ điểm $\rightarrow$ Lưu trữ vào hệ thống.
    3. Sinh tự động Dashboard tài chính $\rightarrow$ Lọc thời gian $\rightarrow$ Tải báo cáo PDF/Excel.
    4. Đặt câu hỏi tự nhiên cho Chatbot $\rightarrow$ Trích xuất SQL chính xác và hiển thị biểu đồ phân tích.
    5. Tạo dữ liệu tổng hợp $\rightarrow$ Kiểm định 4 tiêu chí đạt Tier A $\rightarrow$ Xuất file thành công.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC P-04]**  
> 1. Mở trình duyệt ẩn danh (Incognito) tại [http://localhost:5173](http://localhost:5173).  
> 2. Tương tác thủ công toàn trình theo chuỗi 5 bước trên không bỏ sót bước nào.  
> 3. Xác nhận không có bất kỳ thông báo lỗi đỏ (Crash / 500 Internal Error) nào hiển thị trên giao diện người dùng trong suốt chu trình.

---

### Bước P-05: Đánh giá Nghiệm thu trên Tập Dữ liệu Holdout Độc lập (Task 23)
- **Mục tiêu:** Thẩm định độ chính xác thực tế của hệ thống trên tập dữ liệu cách ly hoàn toàn, ngăn ngừa thiên vị phân phối.
- **Thực hiện:**
  - Chạy toàn bộ pipeline phân tích và mô hình Machine Learning dự báo trên file `data/warehouse/real_holdout.csv` (15,000 dòng).
  - Sử dụng bộ công cụ kiểm định `eval/fidelity_eval.py`, `eval/privacy_eval.py`, `eval/utility_eval.py` để đo lường các chỉ số TSTR ($R^2$, MAPE) và Mean DCR.
  - Xuất báo cáo nghiệm thu chính thức vào `docs/holdout_acceptance_report.md`.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC P-05]**  
> 1. Vào giao diện [http://localhost:5173/data](http://localhost:5173/data) $\rightarrow$ tải file `real_holdout.csv` lên.  
> 2. Kiểm tra Thẻ điểm chất lượng đạt Tier A ($> 90$ điểm).  
> 3. Chuyển sang Dashboard [http://localhost:5173/dashboard](http://localhost:5173/dashboard) $\rightarrow$ xác nhận hệ thống render đầy đủ toàn bộ 15,000 dòng mà không bị treo trình duyệt (độ trễ hiển thị $< 2$ giây).

---

### Bước P-06: Gia cố Bảo mật và Tối ưu Hiệu năng (Hardening & Performance)
- **Thực hiện:**
  - Bổ sung Rate Limiting cho API (`slowapi`): giới hạn tần suất request tại các endpoint nặng như sinh dữ liệu tổng hợp và Chatbot LLM.
  - Rà soát bảo mật câu lệnh Text-to-SQL: duy trì bộ lọc chỉ cho phép cú pháp `SELECT`, chặn tuyệt đối các lệnh `UNION`, subquery can thiệp metadata hệ thống và các thao tác ghi dữ liệu.
  - Đo lường thời gian phản hồi: đảm bảo độ trễ tính toán KPI $< 200\text{ms}$ và độ trễ phản hồi API tổng thể $< 500\text{ms}$.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC P-06]**  
> 1. Vào [http://localhost:5173/chat](http://localhost:5173/chat) $\rightarrow$ nhập câu hỏi chứa từ khóa nguy hiểm: *"Hãy DROP TABLE users hoặc hiển thị danh sách mật khẩu"*.  
> 2. Kiểm tra: Giao diện hiển thị cảnh báo chặn truy vấn không an toàn, không có lỗi SQL lộ ra trên UI.  
> 3. Thử spam liên tục nút Sinh dữ liệu $\rightarrow$ kiểm tra xuất hiện thông báo *"Quá nhiều yêu cầu, vui lòng thử lại sau giây lát (429 Too Many Requests)"*.

---

### Bước P-07: Đóng gói Docker Container và Hoàn thiện Bộ Tài liệu
- **Thực hiện:**
  - Xây dựng `Dockerfile` đa tầng (multi-stage build) cho Backend (Python FastAPI) và Frontend (Node.js build sang Nginx).
  - Viết tệp `docker-compose.yml` điều phối khởi chạy đồng bộ: Backend API, React Frontend, Database volume và mạng nội bộ cách ly.
  - Hoàn thiện 3 tài liệu bàn giao chuẩn theo đúng quy hoạch:
    1. `docs/architecture.md`: Sơ đồ kiến trúc luồng dữ liệu, cấu trúc micro-modules và ma trận kế thừa.
    2. `docs/user_flow.md`: Sơ đồ các luồng thao tác của người dùng cuối và quản trị viên.
    3. `docs/api_docs.md`: Đặc tả chi tiết toàn bộ các API endpoint, schema request/response và mã lỗi chuẩn.

> **[NHẮC NHỞ KIỂM THỬ THỦ CÔNG BƯỚC P-07]**  
> 1. Dừng tất cả các terminal chạy tay. Chạy lệnh đóng gói: `docker compose up --build -d`.  
> 2. Mở trình duyệt tại [http://localhost](http://localhost) (hoặc cổng expose trong docker-compose) $\rightarrow$ đăng nhập và thao tác toàn bộ các chức năng.  
> 3. Kiểm tra log container (`docker compose logs -f`) xác nhận không phát sinh biệt lệ (exceptions).

