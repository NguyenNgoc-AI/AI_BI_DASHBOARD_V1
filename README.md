# AI BI Dashboard & Synthetic Data Generator

Hệ sinh thái phân tích dữ liệu kinh doanh thông minh (AI BI Dashboard) tích hợp động cơ sinh dữ liệu tổng hợp (Synthetic Data Generator) và cổng thẩm định chất lượng 4 trụ cột.

---

## 1. Cấu trúc thư mục dự án

```text
Synthetic/
├── backend/                             # Core Backend Engine (FastAPI, Auth, Ingestion, Dashboard, Chatbot)
├── data/                                # Kho dữ liệu chuẩn (sample_dataset, generated, warehouse)
├── demo_ui/                             # Giao diện Streamlit Demo & Kiểm thử trực quan
├── docs/                                # Tài liệu kỹ thuật, báo cáo nghiệm thu & checklist
├── eval/                                # Bộ công cụ kiểm định 4 trụ cột (Fidelity, Privacy, Utility)
├── semantic/                            # Lớp Ngữ nghĩa, Lược đồ E-commerce & Ràng buộc nghiệp vụ
└── tests/                               # Phân hệ kiểm thử 3 nhóm độc lập
    ├── 1_synthetic_core/                # Nhóm 1: Kiểm thử lõi thuật toán Synthetic (chạy lẻ/gộp)
    ├── 2_synthetic_api/                 # Nhóm 2: Kiểm thử các endpoint FastAPI Synthetic
    └── 3_backend_services/              # Nhóm 3: Kiểm thử nghiệp vụ Backend (Auth, Ingest, KPI)
```

---

## 2. Hướng dẫn cài đặt & Khởi chạy

### Cài đặt môi trường

```powershell
# Dependencies cơ bản cho Backend & API
python -m pip install -r requirements.txt

# Dependencies nâng cao cho Machine Learning, SDV & Quality Gate (nếu cần)
python -m pip install -r requirements-ai.txt
```

### Khởi chạy Server

1. **Khởi chạy Server Backend Tổng hợp (Bao gồm cả Auth, Dashboard, Chatbot và Synthetic API):**
   ```powershell
   uvicorn backend.main:app --reload --port 8000
   ```
   Swagger UI tài liệu API: `http://localhost:8000/docs`

2. **Khởi chạy riêng Server Synthetic API (Sandbox kiểm thử độc lập):**
   ```powershell
   python -m backend.synthetic_generator.api.standalone_server
   ```

3. **Khởi chạy giao diện Demo UI (Streamlit):**
   ```powershell
   streamlit run demo_ui/app.py
   ```

---

## 3. Hướng dẫn Kiểm thử (Test Suites)

### Nhóm 1: Kiểm thử Lõi Data Synthetic (Tasks 1 - 7)

* **Chạy gộp cả 7 bài test trong 1 lệnh duy nhất:**
  ```powershell
  python tests/1_synthetic_core/run_core_tests.py
  # hoặc dùng unittest discover:
  python -m unittest discover -s tests/1_synthetic_core -p "test_*.py"
  ```

* **Chạy từng bài kiểm thử đơn lẻ:**
  ```powershell
  python -m unittest tests/1_synthetic_core/test_01_schema_definition.py
  python -m unittest tests/1_synthetic_core/test_02_business_rules.py
  python -m unittest tests/1_synthetic_core/test_03_profiling_and_quality.py
  python -m unittest tests/1_synthetic_core/test_04_schema_learning.py
  python -m unittest tests/1_synthetic_core/test_05_synthetic_generator.py
  python -m unittest tests/1_synthetic_core/test_06_quality_gate.py
  python -m unittest tests/1_synthetic_core/test_07_benchmark_data.py
  ```

### Nhóm 2: Kiểm thử Tầng API của Synthetic Generator

* **Chạy test endpoint qua FastAPI TestClient:**
  ```powershell
  python -m unittest tests/2_synthetic_api/test_08_synthetic_api.py
  ```

* **Chạy bộ tự động 15 test cases và xuất file kết quả `api_test_results.json`:**
  ```powershell
  python tests/2_synthetic_api/run_api_test_suite.py
  ```

### Nhóm 3: Kiểm thử Nghiệp vụ Backend

* **Chạy test các module Backend (Auth, Ingestion, KPI, Chatbot, Reports):**
  ```powershell
  python -m unittest tests/3_backend_services/test_backend.py
  ```

* **Chạy test tích hợp API Backend:**
  ```powershell
  python -m unittest tests/3_backend_services/test_api_integration.py
  ```

