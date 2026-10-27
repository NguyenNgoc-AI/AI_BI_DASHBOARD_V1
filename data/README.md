# 📦 DATA PACKAGE & ISOLATED DATA ENGINE (`AI_BI_DASHBOARD_V1`)

Thư mục này đóng vai trò là **Kho dữ liệu & Bộ động cơ Dữ liệu độc lập (Self-contained Data & AI Engine)** cho toàn bộ hệ thống AI BI Dashboard. 

Toàn bộ các chức năng chuyên sâu về dữ liệu từ Nhánh 1 (lược đồ ngữ nghĩa, quy tắc nghiệp vụ, mô hình sinh dữ liệu theo kịch bản, và kiểm định chất lượng 3 chiều) được **cô lập hoàn toàn** tại đây nhằm:
1. Cho phép phát triển, tinh chỉnh thuật toán và mô hình độc lập mà **tuyệt đối không can thiệp hay làm gián đoạn độ hoàn thiện sẵn có của Nhánh 2** (Auth RBAC, API Router, Frontend Code Candy).
2. Tách biệt bộ kiểm thử chuyên sâu về dữ liệu (`data/tests/`) khỏi bộ kiểm thử ứng dụng chính (`tests/`).
3. Cung cấp sẵn các nguồn dữ liệu đã chuẩn hóa, đặc biệt là tệp dữ liệu tương thích 100% để Frontend và Dashboard vận hành ngay lập tức.

---

## 1. Cấu trúc Thư mục Cô lập

```text
nhánh 2/data/
├── README.md                           # Tài liệu kỹ thuật, kiến trúc cô lập & hướng dẫn tích hợp
├── app_database.db                     # Database SQLite runtime của Nhánh 2 (tự sinh lúc chạy, gitignored)
│
├── datasets/                           # [KHO DỮ LIỆU ĐÃ CHUẨN HÓA]
│   ├── synthetic_ecommerce.csv         # 50,000 dòng Gold Mock Data (đầy đủ 38 thuộc tính E-commerce)
│   ├── sample_dashboard_feed.csv       # [Adapter View] 50,000 dòng rút gọn chuẩn cho Frontend & Dashboard
│   ├── ecommerce_seed.csv              # 35,000 dòng Benchmark Seed Data (mồi huấn luyện mô hình)
│   ├── real_holdout.csv                # 15,000 dòng Real Holdout Set (tập đối chuẩn độc lập đánh giá Utility)
│   ├── learned_seed_profile.json       # Hồ sơ phân phối thống kê đã học từ tập mồi
│   ├── seed_quality_audit.json         # Báo cáo kiểm định chất lượng dữ liệu mồi
│   ├── synthetic_validation_report.json# Báo cáo kiểm định chất lượng dữ liệu tổng hợp
│   └── create_dashboard_feed.py        # Helper script chuyển đổi 38 cột -> 6 cột cho Frontend
│
├── engine/                             # [CORE ENGINE CÔ LẬP CỦA NHÁNH 1]
│   ├── semantic/                       # Lớp ngữ nghĩa (Semantic Layer) & Business Rules
│   │   ├── schema_definition.py        # Định nghĩa GenericSchema, bảng, cột, khóa ngoại, metrics
│   │   ├── business_rules.py           # Engine thực thi ràng buộc cứng/mềm và tự động sửa lỗi (Auto-repair)
│   │   ├── ecommerce_schema.json       # Lược đồ JSON chuẩn của 5 thực thể E-commerce
│   │   └── rules.json                  # Tập luật kinh doanh E-commerce chuẩn hóa
│   ├── eval/                           # Bộ đánh giá chất lượng dữ liệu 3 chiều khoa học
│   │   ├── fidelity_eval.py            # Đo độ trung thực phân phối (Wasserstein distance, Jensen-Shannon)
│   │   ├── privacy_eval.py             # Đo rủi ro bảo mật & rò rỉ (Distance to Closest Record - DCR, NNDR)
│   │   └── utility_eval.py             # Đo giá trị phân tích qua huấn luyện mô hình TSTR
│   ├── generator/                      # Bộ sinh dữ liệu tổng hợp theo kịch bản kinh doanh
│   │   ├── generator_model.py          # Thuật toán sinh phân phối có điều kiện theo thứ bậc
│   │   ├── pipeline.py                 # Điều phối pipeline sinh dữ liệu và ép luật kinh doanh
│   │   ├── validator.py                # Quality Gate kiểm định 8 tiêu chuẩn dữ liệu
│   │   └── api/                        # Router và schemas hỗ trợ sinh dữ liệu theo kịch bản
│   ├── schema_learning/                # Tự động học cấu trúc và suy luận quan hệ
│   │   ├── schema_extractor.py         # Trích xuất phân phối, tương quan, PK/FK từ CSV/Dataframe
│   │   └── rule_parser.py              # Phân tích cú pháp biểu thức nghiệp vụ sang mã thực thi
│   └── eda/                            # Phân tích khám phá & kiểm định chất lượng
│       ├── profiling.py                # Thống kê phân phối, trung vị, phân vị, độ lệch chuẩn
│       └── quality_checker.py          # Bắt lỗi null, duplicate, out-of-range
│
└── tests/                              # [TEST SUITE CÔ LẬP CỦA DATA ENGINE]
    ├── test_01_schema_definition.py    # Kiểm tra tính toàn vẹn của Semantic Schema
    ├── test_02_business_rules.py       # Kiểm tra bộ luật nghiệp vụ & cơ chế tự sửa lỗi
    ├── test_03_profiling_and_quality.py# Kiểm tra bộ phân tích dữ liệu & bắt lỗi chất lượng
    ├── test_04_schema_learning.py      # Kiểm tra trích xuất phân phối & tương quan
    ├── test_05_synthetic_generator.py  # Kiểm tra các kịch bản sinh dữ liệu (Baseline, Growth, Holiday)
    ├── test_06_quality_gate.py         # Kiểm tra cổng kiểm định chất lượng 8 tiêu chí
    ├── test_07_benchmark_data.py       # Kiểm tra số lượng, 38 cột và tính cách ly của 3 tập dữ liệu
    └── test_08_synthetic_api.py        # Kiểm tra API endpoint sinh dữ liệu kịch bản
```

---

## 2. Các Tập Dữ Liệu & Cấu Trúc 38 Thuộc Tính

Dữ liệu được phân chia theo tiêu chuẩn khoa học để huấn luyện và kiểm thử cách ly:

| Tập dữ liệu | Đường dẫn | Số dòng | Số cột | Vai trò trong hệ thống |
|---|---|:---:|:---:|---|
| **Gold Mock Data** | `data/datasets/synthetic_ecommerce.csv` | **50,000** | **38** | Dữ liệu tổng hợp chất lượng cao, tuân thủ 100% luật kinh doanh, cung cấp cho toàn bộ hệ sinh thái Dashboard & Chatbot. |
| **Dashboard Feed** | `data/datasets/sample_dashboard_feed.csv` | **50,000** | **6** | File trích xuất tương thích chuẩn cho Frontend upload và tính toán tức thì. |
| **Benchmark Seed** | `data/datasets/ecommerce_seed.csv` | **35,000** | **38** | Dữ liệu mồi thực tế (Olist, Online Retail II, BookSQL) dùng để huấn luyện mô hình. |
| **Real Holdout** | `data/datasets/real_holdout.csv` | **15,000** | **38** | Tập kiểm thử độc lập bị cô lập, không dùng để học, dùng để chấm điểm Utility (TSTR). |

### 5 Thực thể & 38 Thuộc tính Chuẩn:
1. **Khách hàng (`customers`):** `customer_id`, `customer_segment`, `city`, `state`, `country`, `zip_code`.
2. **Sản phẩm (`products`):** `product_id`, `category`, `sub_category`, `unit_price`, `unit_cost`, `margin_rate`.
3. **Bán hàng (`sales`):** `sales_id`, `quantity`, `gross_sales`, `discount_amount`, `net_sales`, `cogs`, `gross_profit`, `gross_margin_pct`, `freight_value`, `platform_fee`.
4. **Đơn hàng (`orders`):** `order_id`, `order_status`, `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date`, `payment_type`, `payment_installments`, `payment_value`.
5. **Tài chính & Tiếp thị (`financials`):** `marketing_channel`, `marketing_spend`, `tax_amount`, `operating_expenses`, `net_profit`, `net_margin_pct`.

---

## 3. Chú Thích Tệp & Chức Năng Kết Nối Frontend và Dashboard

Để vận hành hoàn chỉnh giao diện Frontend (`http://localhost:5173`) và Backend API, hệ thống kết nối với các tệp trong thư mục `data/` như sau:

### 3.1. Cấp nguồn Dữ liệu cho Màn hình Tổng quan (Overview) & Báo cáo (Reports)
- **Tệp sử dụng:** `data/datasets/sample_dashboard_feed.csv` (dung lượng ~2.87 MiB, 50,000 dòng).
- **Cách thức vận hành:**
  1. Người dùng mở Frontend tại tab **"Dữ liệu"**.
  2. Kéo thả hoặc chọn tệp `sample_dashboard_feed.csv` để gửi tới `POST /datasets/analyze`.
  3. API nhận diện 6 cột chuẩn:
     - `date`: Ngày phát sinh đơn hàng ($YYYY-MM-DD$).
     - `order_id`: Mã định danh đơn hàng.
     - `product`: Phân nhóm sản phẩm (`sub_category`).
     - `quantity`: Số lượng mặt hàng.
     - `revenue`: Doanh thu thuần (`net_sales`).
     - `cost`: Giá vốn hàng bán (`cogs`).
  4. **Kết quả trên UI:**
     - Tự động hiển thị 7 thẻ KPI Pastel: Tổng doanh thu, Tổng chi phí, Lợi nhuận ròng, Tỷ suất lợi nhuận, AOV, CAC, ROAS.
     - Tự động vẽ 3 biểu đồ: Xu hướng doanh thu theo thời gian, Top sản phẩm đóng góp doanh số, và Cơ cấu tỷ trọng danh mục.
     - Cho phép lọc báo cáo theo khoảng ngày và tải báo cáo đa định dạng (PDF, Excel XLSX, CSV, JSON, HTML, PowerPoint PPTX).

### 3.2. Cấp bối cảnh cho Trợ lý Chatbot AI & Text-to-SQL
- Dữ liệu từ `sample_dashboard_feed.csv` khi được tải lên sẽ nạp vào bộ nhớ ngữ cảnh RAG (`backend/chatbot/rag_engine.py`) và tạo bảng SQLite tạm thời.
- Khi người dùng hỏi tại tab **"Chat AI"** (ví dụ: *"Tổng lợi nhuận của Fitness & Recreation trong tháng 2 là bao nhiêu?"*):
  - Chatbot trích xuất KPI tương ứng hoặc dịch câu hỏi sang câu lệnh `SELECT` an toàn (`backend/chatbot/text_to_sql.py`) để truy vấn trực tiếp trên dữ liệu mẫu này.

### 3.3. Sinh Dữ liệu Giả lập theo Kịch bản Doanh nghiệp (Manager & Admin)
- **Module sử dụng:** `data/engine/generator/generator_model.py` và `pipeline.py`.
- **Hỗ trợ kịch bản:**
  - `baseline`: Phân phối thông thường dựa theo tập mồi `learned_seed_profile.json`.
  - `growth_rate`: Tăng trưởng doanh số theo tỷ lệ định trước.
  - `holiday_season`: Kịch bản mùa lễ hội / Flash Sale (tăng đột biến đơn hàng, tỷ lệ chiết khấu cao, chi phí quảng cáo tăng).
  - Tùy biến khoảng ngày mô phỏng (`start_date`, `end_date`).
- **Cổng kiểm soát chất lượng (Quality Gate):** Dữ liệu sinh ra trước khi trả về phải vượt qua `validator.py` kiểm tra 100% các đẳng thức tài chính:
  $$\text{gross\_sales} = \text{quantity} \times \text{unit\_price}$$
  $$\text{net\_sales} = \text{gross\_sales} - \text{discount\_amount}$$
  $$\text{net\_profit} = \text{net\_sales} - \text{cogs} - \text{marketing\_spend} - \text{platform\_fee} - \text{freight\_value} - \text{tax\_amount} - \text{operating\_expenses}$$

### 3.4. Đánh giá Chất lượng Dữ liệu 3 Chiều Khoa học
- **Module sử dụng:** `data/engine/eval/`.
- Khi cần nghiệm thu hoặc xuất báo cáo độ tin cậy của dữ liệu tổng hợp:
  - `fidelity_eval.py`: Chứng minh phân phối dữ liệu giả lập tương đồng với dữ liệu thực tế ($p\text{-value}$, Wasserstein distance).
  - `privacy_eval.py`: Chứng minh không có hiện tượng sao chép nguyên mẫu dữ liệu nhạy cảm ($DCR > 0$).
  - `utility_eval.py`: Chứng minh mô hình học máy huấn luyện trên dữ liệu tổng hợp đạt hiệu quả tương đương khi kiểm thử trên tập thực tế độc lập `real_holdout.csv` (TSTR).

---

## 4. Helper Script: Tái tạo Dashboard Feed

Nếu có cập nhật dữ liệu mới trong `synthetic_ecommerce.csv` và muốn tạo lại tệp `sample_dashboard_feed.csv`:

```powershell
python data/datasets/create_dashboard_feed.py
```
Script sẽ tự động đọc tệp 38 cột, trích xuất và chuẩn hóa ngày tháng thành 50,000 dòng 6 cột sẵn sàng cho Frontend.

---

## 5. Hướng dẫn Kiểm thử Dành riêng cho Data Engine

Toàn bộ 8 file test của Data Engine được cô lập tại `data/tests/`:

```powershell
# Chạy toàn bộ các bài kiểm thử của Data Engine (34 unit tests kiểm tra toán học & dữ liệu):
python -u -m unittest data/tests/test_01_schema_definition.py data/tests/test_02_business_rules.py data/tests/test_03_profiling_and_quality.py data/tests/test_04_schema_learning.py data/tests/test_05_synthetic_generator.py data/tests/test_06_quality_gate.py data/tests/test_07_benchmark_data.py
```

> [!NOTE]
> Để chạy kiểm thử tích hợp ứng dụng chính của Nhánh 2 (Backend, Auth, Token versioning, RBAC, API):
> ```powershell
> python -u -m unittest tests/test_backend.py
> ```
> Hai bộ test hoàn toàn độc lập, đảm bảo quá trình chỉnh sửa dữ liệu không gây xung đột với logic bảo mật và nghiệp vụ của Backend.
