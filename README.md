# AI BI Dashboard · Data Engine & Synthetic Generator (`Unhi0`)

> **Nhánh chuyên trách Dữ liệu:** Chịu trách nhiệm toàn bộ các chức năng liên quan đến Data Pipeline, Semantic Schema, Schema Learning, Mô hình sinh dữ liệu giả lập (Synthetic Data Engine), Đánh giá chất lượng dữ liệu và Giao diện kiểm thử độc lập.

---

## 🎯 Phạm vi và Mục tiêu của Nhánh `Unhi0`

Nhánh **`Unhi0`** được chuẩn hóa thành một gói dịch vụ dữ liệu độc lập (Self-contained Data Package), bao gồm hai giai đoạn cốt lõi:

1. **Giai đoạn 1: Chuẩn bị dữ liệu & Lược đồ ngữ nghĩa (Semantic Layer)**
   * Thu thập, làm sạch và chuẩn hóa các nguồn dữ liệu thương mại điện tử (Olist, Online Retail II, BookSQL).
   * Phân tích khám phá dữ liệu (EDA), phân phối thống kê và kiểm định chất lượng (Data Quality Audit).
   * Định nghĩa cấu trúc bảng, khóa ngoại, ràng buộc giá trị và quy tắc nghiệp vụ e-commerce (Business Rules).
   * Tự động suy luận schema và trích xuất quy tắc từ file CSV/JSON/Database (Schema Learning).

2. **Giai đoạn 2: Công cụ sinh dữ liệu giả lập (Synthetic Data Engine) & Kiểm thử**
   * Mô hình toán học & phân phối xác suất mô phỏng hành vi mua sắm, doanh thu, lợi nhuận, giỏ hàng.
   * Hỗ trợ các kịch bản thực tế: *Baseline, Flash Sale, Lạm phát / Tăng giá, Khủng hoảng chuỗi cung ứng*.
   * Cổng kiểm soát chất lượng (Quality Gate) tự động xác thực dữ liệu sinh ra theo 8 tiêu chuẩn khắt khe.
   * Đánh giá chất lượng theo 3 chiều chuẩn khoa học: **Độ trung thực (Fidelity)**, **Bảo mật quyền riêng tư (Privacy)** và **Giá trị phân tích (Utility)**.
   * **Standalone API** (FastAPI) phục vụ sinh dữ liệu và tải file CSV độc lập.
   * **Interactive Demo UI** (Streamlit) phục vụ hội đồng nghiệm thu và kiểm thử trực quan.

---

## 📁 Cấu trúc Thư mục

```text
├── backend/
│   ├── eda/                               # Phân tích khám phá & kiểm định chất lượng data
│   │   ├── profiling.py                   # Thống kê phân phối, trung bình, độ lệch chuẩn
│   │   ├── quality_checker.py             # Bắt lỗi null, duplicate, out-of-range
│   │   └── run_eda.py                     # Script thực thi quét toàn bộ dataset
│   ├── schema_learning/                   # Tự động học cấu trúc và quan hệ dữ liệu
│   │   ├── schema_extractor.py            # Suy luận kiểu dữ liệu, PK/FK từ tập tin
│   │   └── rule_parser.py                 # Phân tích cú pháp quy tắc nghiệp vụ
│   └── synthetic_generator/               # Cốt lõi sinh dữ liệu giả lập
│       ├── generator_model.py             # Thuật toán mô phỏng phân phối thống kê
│       ├── pipeline.py                    # Pipeline điều phối sinh dữ liệu theo kịch bản
│       ├── validator.py                   # Cổng kiểm soát chất lượng (Quality Gate)
│       └── api/                           # Dịch vụ API độc lập cho Synthetic Data
│           ├── standalone_server.py       # FastAPI runner (cổng 8000, tài liệu /docs)
│           ├── router.py                  # Các endpoint /generate, /scenarios, /download-csv
│           └── schemas.py                 # Pydantic models cho request / response
├── data/
│   ├── sample_dataset/                    # Dữ liệu nguồn thô & kịch bản hợp nhất
│   ├── generated/                         # Dữ liệu synthetic sinh ra, profile & audit report
│   └── warehouse/                         # Dữ liệu holdout thực tế để đối chuẩn
├── demo_ui/
│   └── app.py                             # Ứng dụng Streamlit kiểm thử trực quan & vẽ biểu đồ
├── eval/                                  # Bộ 3 công cụ đánh giá chất lượng dữ liệu
│   ├── fidelity_eval.py                   # Đánh giá độ tương đồng phân phối (KS-test, Chi-square)
│   ├── privacy_eval.py                    # Đánh giá nguy cơ rò rỉ dữ liệu (Distance to Closest Record)
│   └── utility_eval.py                    # Đánh giá hiệu quả khi huấn luyện mô hình ML
├── semantic/                              # Tầng định nghĩa ngữ nghĩa & quy tắc
│   ├── schema_definition.py               # Lược đồ e-commerce chuẩn hóa (orders, items, products)
│   ├── business_rules.py                  # Ràng buộc nghiệp vụ (giá bán > giá vốn, trạng thái)
│   ├── ecommerce_schema.json              # Schema dạng JSON
│   └── rules.json                         # Quy tắc nghiệp vụ dạng JSON
├── docs/                                  # Báo cáo kỹ thuật, nghiệm thu giai đoạn 1 & 2
├── tests/                                 # 8 bài kiểm thử chuyên sâu cho toàn bộ pipeline data
│   ├── test_01_schema_definition.py
│   ├── test_02_business_rules.py
│   ├── test_03_profiling_and_quality.py
│   ├── test_04_schema_learning.py
│   ├── test_05_synthetic_generator.py
│   ├── test_06_quality_gate.py
│   ├── test_07_benchmark_data.py
│   └── test_08_synthetic_api.py
└── requirements.txt                       # Thư viện phụ thuộc chuyên biệt cho Data & Demo
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy

### 1. Cài đặt môi trường
Khuyến nghị sử dụng Python 3.11+:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Khởi chạy Standalone Synthetic API
Dịch vụ API phục vụ sinh dữ liệu hoạt động độc lập (không cần database auth hay server main):
```powershell
python -m backend.synthetic_generator.api.standalone_server
```
* **Swagger UI / API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Các endpoint chính:**
  * `GET /api/v1/synthetic/scenarios` — Danh sách các kịch bản mô phỏng.
  * `POST /api/v1/synthetic/generate` — Sinh dữ liệu theo số dòng và kịch bản mong muốn.
  * `GET /api/v1/synthetic/download-csv` — Xuất và tải tập tin CSV vừa sinh.
  * `POST /api/v1/synthetic/validate-benchmark` — Chạy Quality Gate kiểm định chất lượng.

### 3. Khởi chạy Giao diện Demo Streamlit
Ứng dụng kiểm thử trực quan với biểu đồ so sánh phân phối và bộ lọc kịch bản:
```powershell
streamlit run demo_ui/app.py
```
* Trình duyệt tự động mở tại: **[http://localhost:8501](http://localhost:8501)**

### 4. Chạy Pipeline sinh dữ liệu bằng dòng lệnh (CLI)
```powershell
python -m backend.synthetic_generator.pipeline
```
Dữ liệu sinh ra sẽ được lưu tại: `data/generated/synthetic_ecommerce.csv`.

### 5. Chạy bộ kiểm thử tự động (Unit & Integration Tests)
Chạy toàn bộ 8 bộ test kiểm định chất lượng:
```powershell
pytest tests/ -v
```

---
