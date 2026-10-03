# TÀI LIỆU MÔ TẢ DỰ ÁN: AI BI DASHBOARD

> **Cập nhật lần cuối:** 30/09/2026  
> **Người tạo:** Uyên Nhi  
> **Mục đích tài liệu:** Tổng hợp hướng đi của dự án, cấu trúc thư mục dự kiến và checklist công việc để các thành viên trong nhóm theo dõi, phối hợp và cập nhật tiến độ.  
> **Tài liệu tham chiếu & lịch sử phát triển:**  
> - [Tài liệu ban đầu – Google Docs](https://docs.google.com/document/d/17Y9n_H5RuIwydklXoJbnSR-pAb_67J4Y5uijegYSHzA/edit?usp=sharing)
> - [Theo dõi cập nhật – Google Sheets](https://docs.google.com/spreadsheets/d/1BFRtqecf_S5UWGVSArQSYeKclGXqZSr21TLGr2K82MQ/edit?gid=1386834576#gid=1386834576)
> - [Repository dự án – GitHub](https://github.com/HocJavaToiCung/AI_BI_DASHBOARD)
---

## I. Ý TƯỞNG THỰC HIỆN DỰ ÁN (PROJECT IDEA)

### 1. Dự án AI BI Dashboard là gì?

**AI BI Dashboard** (Business Intelligence Dashboard tích hợp Trí tuệ nhân tạo) là hướng tiếp cận nhằm hỗ trợ tự động hóa các bước chính trong quy trình phân tích dữ liệu kinh doanh và khởi tạo báo cáo trực quan.

Khác với phương pháp truyền thống (người dùng phải thao tác thủ công trên các công cụ như Power BI, Tableau để làm sạch dữ liệu, xây dựng mô hình và dựng biểu đồ), hệ thống dự kiến sử dụng các thuật toán AI để hỗ trợ:

* Phân tích, kiểm tra và làm sạch dữ liệu đầu vào.
* Lựa chọn dạng biểu đồ (visualization) phù hợp với chỉ số kinh doanh.
* Rút ra các nhận xét, đánh giá tổng quan dựa trên dữ liệu.
* Tích hợp Chatbot AI hỗ trợ tương tác bằng ngôn ngữ tự nhiên để truy vấn sâu, nhận phản hồi và tùy chỉnh giao diện báo cáo theo nhu cầu.

### 2. Đối tượng sử dụng

* Các cá nhân có nhu cầu phân tích dữ liệu kinh doanh.
* Các doanh nghiệp vừa và nhỏ (SME) thiếu đội ngũ chuyên gia Data Analyst/BI chuyên trách.

### 3. Thông tin hiển thị trên giao diện (UI Components)

* **Giao diện Dashboard BI:** Hiển thị hệ thống biểu đồ trực quan tự động sinh từ dữ liệu.
* **Giao diện Chatbot AI:** Tương tác ngôn ngữ tự nhiên để hỗ trợ truy vấn và phân tích nâng cao.
* **Giao diện Lịch sử tài khoản:** Quản lý và tóm tắt lịch sử phân tích, lưu trữ báo cáo của người dùng.

---

---

### Luồng thực hiện dự án (WORKFLOW)

Quy trình vận hành của dự án được phân định rõ theo vai trò người dùng trong hệ thống:

```
[Người dùng tải File CSV/JSON] 
            │
            ▼
[Hệ thống xử lý & Tạo BI Dashboard] ──► [Xuất hình ảnh Dashboard]
            │
            ▼
[Tương tác với Chatbot (Prompt)] ──► [Chatbot phản hồi & Phân tích sâu]

```

### 1. Luồng dành cho Người dùng / Thành viên Doanh nghiệp

1. **Đầu vào (Input):** Người dùng tải lên tệp dữ liệu dạng `CSV` hoặc `JSON`.
2. **Xử lý & Khởi tạo (Processing):** Hệ thống tự động phân tích cấu trúc, khởi tạo BI Dashboard tương ứng và xuất ra hình ảnh/giao diện báo cáo.
3. **Tương tác nâng cao (Interaction):** Người dùng nhập câu lệnh (prompt) vào Chatbot để tìm hiểu sâu hơn về dữ liệu. Chatbot phản hồi, đưa ra gợi ý cải thiện hoặc điều chỉnh Dashboard theo yêu cầu.
4. **Hỗ trợ ra quyết định (Decision Support):** Cung cấp các góc nhìn chuyên sâu hoàn toàn dựa trên các chỉ số kinh doanh đã được cấp.

### 2. Luồng dành cho Quản trị viên (Admin)

1. **Đăng nhập:** Truy cập hệ thống với phân quyền Quản trị viên.
2. **Quản lý:** Chuyển hướng đến giao diện quản lý danh sách các tài khoản, phân quyền và giám sát hoạt động người dùng dưới quyền.

---

---

### Ý tưởng về cách thu thập và xây dựng dữ liệu (DATA PIPELINE)

Để giải quyết thách thức về việc thu thập lượng lớn dữ liệu thực đa dạng phục vụ huấn luyện mô hình AI, dự án triển khai quy trình **Synthetic Data Generation Pipeline** (Đường ống tạo dữ liệu tổng hợp). Dữ liệu tổng hợp sinh ra hướng tới việc phản ánh các đặc trưng của dữ liệu thực và được kiểm tra về rủi ro bảo mật.

```
[Dữ liệu thô] ──► [Data Understanding & EDA] ──► [Semantic Schema]
                                                        │
                                                        ▼
[Mô hình AI BI] ◄── [Bộ kiểm định 4 tiêu chí] ◄── [Synthetic Data Generator]

```

### 1. Quy trình tạo Dữ liệu Tổng hợp (Synthetic Data Pipeline)

1. **Thu thập dữ liệu ban đầu:** Tiếp nhận các tập dữ liệu thực mẫu.
2. **Thấu hiểu dữ liệu (Data Understanding & EDA):** Thực hiện phân tích khám phá dữ liệu để nắm bắt đặc trưng phân phối và tương quan.
3. **Trích xuất Semantic Schema (Lược đồ quan hệ):** Xây dựng cấu trúc định nghĩa để hệ thống hiểu được ý nghĩa nghiệp vụ, kiểu dữ liệu, quan hệ giữa các cột và các bảng.
4. **Huấn luyện Trình sinh dữ liệu (Synthetic Data Generator):** Mô hình học cấu trúc phân phối và quan hệ thuộc tính từ dữ liệu thực, từ đó tự động sinh ra các bản ghi mới có đặc tính tương đương.

### 2. Kiểm định Dữ liệu Tổng hợp (Validation Framework)

Dữ liệu được sinh ra từ bộ tạo dữ liệu tổng hợp cần trải qua quá trình kiểm định trước khi đưa vào huấn luyện mô hình AI chính, bao gồm 4 tiêu chí:

* **Validity (Tính hợp lệ):** Kiểm tra mức độ phù hợp với cấu trúc Semantic Schema, kiểu dữ liệu, khoảng giá trị (range) và các quy tắc nghiệp vụ (business rules).
* **Fidelity (Tính trung thực):** Đánh giá mức độ tương đồng về phân phối thống kê, sự tương quan và quan hệ giữa các thuộc tính so với dữ liệu thực.
* **Privacy (Tính bảo mật):** Đánh giá nguy cơ trùng lặp hoặc làm lộ nguyên vẹn các bản ghi (record) cụ thể từ dữ liệu thực gốc.
* **Utility (Tính hữu ích):** Đánh giá mức độ hữu ích của dữ liệu sinh ra đối với mục tiêu huấn luyện các mô hình AI trong hệ thống.

> **Ghi chú về Đánh giá (Evaluation Note):**
> Dữ liệu thực gốc sẽ được tách riêng một phần làm tập kiểm định độc lập (Holdout Set/Evaluation). Việc này nhằm đánh giá khả năng tổng quát hóa của mô hình AI BI Dashboard và hạn chế nguy cơ mô hình chỉ phản ánh dữ liệu do chính bộ sinh tạo ra.
Dưới đây là **Cấu trúc Thư mục Đầy đủ (được chia nhỏ module cụ thể kèm ghi chú `# comment` chức năng)** và **Bảng Master Checklist Công việc theo Timeline tuần tự** dành cho dự án **Code Candy - AI BI Dashboard**.

---

---

## II. CẤU TRÚC THƯ MỤC ĐỀ RA

### Cấu trúc Thư mục Dự án (`ai-bi-dashboard/`)

```text
ai-bi-dashboard/
├── semantic/
│   ├── ecommerce_schema.json           # Định nghĩa cấu trúc Semantic Schema chuẩn cho ngành Bán lẻ/E-commerce
│   └── business_rules.py               # Ràng buộc nghiệp vụ tài chính (Lợi nhuận = Doanh thu - COGS - Chi phí MKT/Sàn)
├── backend/
│   ├── main.py                         # Điểm khởi chạy FastAPI Server, điều hướng Routes, CORS và Middleware
│   ├── config.py                       # Cấu hình môi trường (API Keys, Database Connection, System Settings)
│   ├── auth.py                         # API Đăng ký, Đăng nhập, JWT Authentication và Phân quyền người dùng (RBAC)
│   ├── eda/
│   │   ├── __init__.py                 # Đánh dấu module Python
│   │   ├── profiling.py                # Phân tích phân phối thống kê dữ liệu mồi thực tế (Mean, Std, Min, Max, Nulls)
│   │   └── quality_checker.py          # Đánh giá chất lượng dữ liệu mồi (Tỷ lệ hợp lệ, thiếu, trùng lặp, ngoại lệ)
│   ├── schema_learning/
│   │   ├── __init__.py                 # Đánh dấu module Python
│   │   ├── schema_extractor.py         # Học kiểu dữ liệu, cấu trúc quan hệ giữa các bảng và ma trận tương quan
│   │   └── rule_parser.py              # Chuyển đổi các quy tắc nghiệp vụ thành các hàm kiểm tra ràng buộc (Constraints)
│   ├── synthetic_generator/
│   │   ├── __init__.py                 # Đánh dấu module Python
│   │   ├── generator_model.py          # Huấn luyện mô hình sinh dữ liệu tổng hợp (SDV / CTGAN / CopulaGAN / LLM Agent)
│   │   ├── pipeline.py                 # Điều phối đường ống sinh dữ liệu tổng hợp theo quy mô yêu cầu
│   │   └── validator.py                # Module kiểm định 4 tiêu chí: Validity, Fidelity, Privacy và Utility (TSTR)
│   ├── dashboard_engine/
│   │   ├── __init__.py                 # Đánh dấu module Python
│   │   ├── data_pipeline.py            # Upload, làm sạch, biến đổi và map dữ liệu từ CSV/JSON vào Schema chuẩn
│   │   ├── kpi_calculator.py           # Tính toán các chỉ số tài chính E-commerce (GMV, Net Profit, CAC, ROAS, LTV)
│   │   ├── chart_generator.py          # Tạo cấu hình dữ liệu cho các biểu đồ (Xu hướng, Top sản phẩm, Cơ cấu)
│   │   └── report_exporter.py          # Engine tự động xuất báo cáo tài chính ra file PDF, Excel, PowerPoint
│   └── chatbot/
│       ├── __init__.py                 # Đánh dấu module Python
│       ├── llm_router.py               # Kết nối và điều hướng truy vấn đến các mô hình LLM (GPT-4o, Gemini, Llama)
│       ├── rag_engine.py               # Trích xuất ngữ cảnh dữ liệu hiện tại từ Dashboard để đưa vào LLM Context
│       ├── text_to_sql.py              # Chuyển đổi câu hỏi tiếng Việt tự nhiên thành câu lệnh truy vấn dữ liệu
│       └── prompt_templates.py         # Bộ Prompts định hướng phân tích tài chính và Guardrails chống Hallucination
├── data/
│   ├── sample_dataset/
│   │   └── ecommerce_seed.csv          # Dữ liệu thực mẫu ban đầu dùng để mồi cho Synthetic Generator
│   ├── generated/
│   │   └── synthetic_ecommerce.csv     # Bộ dữ liệu tài chính tổng hợp được sinh ra từ Generator Pipeline
│   └── warehouse/
│       ├── real_holdout.csv            # Tập dữ liệu thực độc lập dùng cho nhân viên kiểm định (Holdout Test Set)
│       └── app_database.db             # Cơ sở dữ liệu lưu Users, Phân quyền, System Config và Lịch sử Chat
├── frontend/
│   ├── package.json                    # Khai báo các thư viện React, Vite, TailwindCSS, Chart.js, Axios
│   ├── vite.config.js                  # Cấu hình Vite bundler và API Proxy kết nối Backend
│   ├── public/                         # Chứa tài nguyên tĩnh (Logo Code Candy, Favicon, Icons)
│   └── src/
│       ├── App.jsx                     # Component gốc quản lý Routing và Auth Provider
│       ├── main.jsx                    # Entry point chính của ứng dụng React Frontend
│       ├── api/
│       │   ├── authApi.js              # Gọi API Đăng ký, Đăng nhập, Quản lý tài khoản
│       │   ├── dataApi.js              # Gọi API Upload file, Kiểm tra Chất lượng data, Biến đổi data
│       │   ├── dashboardApi.js         # Gọi API lấy dữ liệu KPIs, Biểu đồ và Xuất báo cáo
│       │   └── chatApi.js              # Gọi API tương tác AI Assistant Chatbot và Lịch sử trò chuyện
│       ├── components/
│       │   ├── layout/                 # Sidebar điều hướng, Header Navbar, Admin Layout
│       │   ├── common/                 # Reusable UI (Buttons, Modals, Cards, Loading Spinners)
│       │   ├── dashboard/              # Component KPICard, ComboChart, TopProducts, FilterPanel
│       │   └── chat/                   # Component ChatWindow, PromptSuggestions, ContextSelector
│       ├── pages/
│       │   ├── auth/
│       │   │   ├── Login.jsx           # Màn hình Đăng nhập (Thành công / Thất bại)
│       │   │   └── Register.jsx        # Màn hình Đăng ký tài khoản mới
│       │   ├── dashboard/
│       │   │   └── Overview.jsx        # Màn hình Dashboard Tổng quan (Trạng thái Empty & Active Data)
│       │   ├── reports/
│       │   │   ├── ReportList.jsx      # Màn hình Quản lý danh sách Báo cáo
│       │   │   └── ReportExport.jsx    # Màn hình Xuất báo cáo PDF, Excel, PowerPoint
│       │   ├── ai_analysis/
│       │   │   └── AIChat.jsx          # Màn hình Tương tác Phân tích AI Chatbot
│       │   ├── data/
│       │   │   ├── DataManagement.jsx  # Màn hình Quản lý Nguồn dữ liệu & Đánh giá chất lượng Data
│       │   │   └── DataPreview.jsx     # Màn hình Xem trước bảng & Thao tác nhanh dữ liệu
│       │   ├── hr/
│       │   │   └── UserManagement.jsx # Màn hình Quản lý Nhân sự, Tài khoản & Phân quyền (RBAC)
│       │   └── settings/
│       │       └── SystemSettings.jsx  # Màn hình Cài đặt Hệ thống, Múi giờ, Theme & Gói dịch vụ
│       └── styles/
│           └── global.css              # Cấu hình TailwindCSS và Style giao diện hệ thống
├── eval/
│   ├── fidelity_eval.py                # Đánh giá sai lệch thống kê (KS-Test, Correlation Heatmap Similarity)
│   ├── privacy_eval.py                 # Đánh giá nguy cơ rò rỉ dữ liệu (Distance to Closest Record - DCR)
│   └── utility_eval.py                 # Đánh giá TSTR (Train on Synthetic, Test on Real) trên Holdout Set
└── docs/
    ├── architecture.md                 # Tài liệu mô tả Kiến trúc Hệ thống & Luồng xử lý Data
    ├── user_flow.md                     # Tài liệu mô tả Chi tiết Luồng Giao diện Người dùng (User Flow)
    └── api_docs.md                     # Tài liệu thiết kế API Endpoints giữa Frontend và Backend

```

---

---

## III. CHECKLIST CÔNG VIỆC (PHÂN THEO TIMELINE TUẦN TỰ)

| Timeline | STT | Hạng mục công việc (Task) | File/Thư mục thực hiện | Đầu ra dự kiến (Deliverables) |
| --- | --- | --- | --- | --- |
| **Giai đoạn 1: Schema & Data Preparation** | 1 | Thiết lập Semantic Schema E-commerce | `semantic/ecommerce_schema.json` | Cấu hình JSON chuẩn hóa các bảng `customers`, `orders`, `sales`, `products`, `financials`.

 |
|  | 2 | Định nghĩa Ràng buộc Nghiệp vụ Tài chính | `semantic/business_rules.py` | Mã hóa các công thức toán học (`Net_Profit`, `CAC`, `ROAS`, `LTV`). |
|  | 3 | Thu thập & Chuẩn bị Seed Data + Holdout Set | `data/sample_dataset/ecommerce_seed.csv`<br>

<br>`data/warehouse/real_holdout.csv` | File dữ liệu mồi thực tế + File Holdout cách ly phục vụ kiểm thử. |
| **Giai đoạn 2: Backend Core - Synthetic Data Pipeline** | 4 | Viết Module EDA & Kiểm tra chất lượng Data mồi | `backend/eda/profiling.py`<br>

<br>`backend/eda/quality_checker.py` | Báo cáo phân phối thống kê & Tỷ lệ chất lượng data mồi.

 |
|  | 5 | Trích xuất Schema & Parse Business Rules | `backend/schema_learning/schema_extractor.py`<br>

<br>`backend/schema_learning/rule_parser.py` | Ma trận tương quan & Bộ lọc Validate Constraints cho Generator. |
|  | 6 | Xây dựng & Huấn luyện Synthetic Generator | `backend/synthetic_generator/generator_model.py`<br>

<br>`backend/synthetic_generator/pipeline.py` | Mô hình Generator hoàn chỉnh & Tập dữ liệu tổng hợp `synthetic_ecommerce.csv`. |
|  | 7 | Xây dựng Bộ Kiểm định 4 Tiêu chí (Quality Gate) | `backend/synthetic_generator/validator.py`<br>

<br>`eval/fidelity_eval.py`<br>

<br>`eval/privacy_eval.py`<br>

<br>`eval/utility_eval.py` | Báo cáo điểm số Validity, Fidelity (KS-Test), Privacy (DCR) và Utility (TSTR) đạt chuẩn. |
| **Giai đoạn 3: Backend Core - Dashboard Engine & Ingestion** | 8 | Cấu hình FastAPI Server & Database | `backend/main.py`<br>

<br>`backend/config.py`<br>

<br>`data/warehouse/app_database.db` | Server Backend chính được cấu hình để nhận API requests. |
|  | 9 | Xây dựng Authentication & Phân quyền RBAC | `backend/auth.py` | API Đăng ký, Đăng nhập JWT, Phân quyền Admin/Manager/User.

 |
|  | 10 | Xây dựng Data Ingestion & Cleansing Module | `backend/dashboard_engine/data_pipeline.py` | API xử lý file tải lên (CSV/JSON), làm sạch và map vào Semantic Schema.

 |
|  | 11 | Xây dựng Analytics & KPI Calculation Engine | `backend/dashboard_engine/kpi_calculator.py`<br>

<br>`backend/dashboard_engine/chart_generator.py` | API tính KPIs (Doanh thu, Đơn hàng, Lợi nhuận) và render Chart data.

 |
|  | 12 | Xây dựng Export Engine | `backend/dashboard_engine/report_exporter.py` | API tự động xuất báo cáo ra file PDF, Excel, PowerPoint.

 |
| **Giai đoạn 4: Backend Core - AI Chatbot & RAG Layer** | 13 | Tích hợp LLM Router & RAG Engine | `backend/chatbot/llm_router.py`<br>

<br>`backend/chatbot/rag_engine.py` | Xử lý kết nối GPT-4o và trích xuất ngữ cảnh dữ liệu hiện tại.

 |
|  | 14 | Lập trình Text-to-SQL & Prompt Guardrails | `backend/chatbot/text_to_sql.py`<br>

<br>`backend/chatbot/prompt_templates.py` | Chuyển đổi câu hỏi tiếng Việt thành SQL Query & System Prompts chống bịa số liệu.

 |
| **Giai đoạn 5: Frontend - Auth, Data & System Settings** | 15 | Khởi tạo Dự án React Vite & Axios Clients | `frontend/package.json`<br>

<br>`frontend/vite.config.js`<br>

<br>`frontend/src/api/*` | Khung ứng dụng Web UI và bộ gõ API Client chuẩn bị kết nối Backend. |
|  | 16 | Dựng Màn hình Đăng nhập & Đăng ký | `frontend/src/pages/auth/Login.jsx`<br>

<br>`frontend/src/pages/auth/Register.jsx` | UI Xác thực hỗ trợ Đăng nhập/Đăng ký và báo trạng thái.

 |
|  | 17 | Dựng Màn hình Quản lý Dữ liệu & Preview | `frontend/src/pages/data/DataManagement.jsx`<br>

<br>`frontend/src/pages/data/DataPreview.jsx` | UI Quản lý nguồn data, hiển thị biểu đồ Chất lượng dữ liệu & Preview bảng.

 |
|  | 18 | Dựng Màn hình Nhân sự & Cài đặt Hệ thống | `frontend/src/pages/hr/UserManagement.jsx`<br>

<br>`frontend/src/pages/settings/SystemSettings.jsx` | UI Quản lý người dùng/phân quyền RBAC & Cài đặt múi giờ, giao diện.

 |
| **Giai đoạn 6: Frontend - Dashboard & AI Chatbot UI** | 19 | Dựng Màn hình Dashboard Tổng quan | `frontend/src/pages/dashboard/Overview.jsx`<br>

<br>`frontend/src/components/dashboard/*` | UI hiển thị trạng thái Chưa có data (Empty) & Đã có data (KPI Cards, Combo Chart, Top Products).

 |
|  | 20 | Dựng Màn hình Phân hệ Báo cáo & Export | `frontend/src/pages/reports/ReportList.jsx`<br>

<br>`frontend/src/pages/reports/ReportExport.jsx` | UI Bộ lọc báo cáo đa chiều, danh sách báo cáo & chức năng Xuất PDF/Excel/PPT.

 |
|  | 21 | Dựng Màn hình AI Chatbot Assistant | `frontend/src/pages/ai_analysis/AIChat.jsx`<br>

<br>`frontend/src/components/chat/*` | Khung chat AI, gợi ý Prompt nhanh, bộ chọn ngữ cảnh và lịch sử trò chuyện.

 |
| **Giai đoạn 7: Integration, Testing & Docs** | 22 | Tích hợp End-to-End Frontend & Backend | Toàn bộ các file trong `frontend/` và `backend/` | Luồng hệ thống từ Upload ➔ Sinh Dashboard ➔ Chatbot tương tác được tích hợp và kiểm thử.

 |
|  | 23 | Kiểm thử Nghiệm thu trên Real Data Holdout | `data/warehouse/real_holdout.csv` | Kiểm định độc lập để đánh giá hoạt động của AI Dashboard trên data thực mới. |
|  | 24 | Hoàn thiện Tài liệu Dự án | `docs/architecture.md`<br>

<br>`docs/user_flow.md`<br>

<br>`docs/api_docs.md` | Bộ tài liệu phục vụ bàn giao đồ án theo phạm vi hiện tại.
