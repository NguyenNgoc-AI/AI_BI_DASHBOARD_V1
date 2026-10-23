# Báo cáo kiểm thử module Synthetic Data Generator

## 1. Kết luận
Hệ thống Synthetic Data Generator đã hoàn thành các hạng mục kiểm thử theo cả hai phương thức: kiểm thử tương tác trực tiếp qua giao diện Swagger UI và kiểm thử tự động theo từng test case.

Kết quả kiểm thử ghi nhận:
- 45/45 unit test cases tự động trong hệ thống đạt trạng thái hợp lệ.
- 15/15 test cases API thực thi độc lập đạt kỳ vọng kỹ thuật, thời gian thực thi trung bình khoảng 1.05 giây cho toàn bộ kịch bản API.
- Dữ liệu tổng hợp sinh ra tuân thủ cấu trúc 38 thuộc tính chuẩn, đạt tỷ lệ hợp lệ logic nghiệp vụ 100% nhờ cơ chế Constraint Enforcement và Auto-Repair.
- Các cơ chế phòng vệ bao gồm xác thực dữ liệu đầu vào (Input Validation), kiểm soát phân quyền (RBAC), cách ly dữ liệu xuất (Gold Benchmark Isolation) và xử lý ngoại lệ dữ liệu rác hoạt động đúng thiết kế.

---

## 2. Dữ liệu kiểm thử

### 2.1. Tập dữ liệu sử dụng
- Benchmark Seed Data (`data/sample_dataset/ecommerce_seed.csv`): 35,000 dòng, 38 cột, dùng làm cơ sở học phân phối thống kê và đối chiếu phân phối.
- Real Holdout Set (`data/warehouse/real_holdout.csv`): 15,000 dòng, 38 cột, được cách ly hoàn toàn (0% ID trùng lặp với tập seed), dùng để kiểm định Utility (TSTR).
- Synthetic Gold Benchmark (`data/generated/synthetic_ecommerce.csv`): 50,000 dòng, 38 cột, tỷ lệ tuân thủ quy tắc nghiệp vụ 100%.
- Learned Seed Profile (`data/generated/learned_seed_profile.json`): Hồ sơ tham số phân phối, cây phân cấp danh mục và ma trận tương quan đã học.
- Thư mục xuất file thử nghiệm (`data/generated/exports/`): Chứa các tệp xuất khi có yêu cầu ghi đĩa từ client nhằm bảo vệ tệp benchmark gốc.

### 2.2. Ma trận tham số truyền đầu vào
- Tham số `n_records` (kiểu Integer): Số lượng bản ghi cần sinh. Phạm vi kiểm thử gồm 3 (vi phạm ngưỡng tối thiểu), 30, 50, 100, 150, 500 bản ghi.
- Tham số `scenario` (kiểu String): Kịch bản mô phỏng nghiệp vụ. Các giá trị kiểm thử gồm `baseline`, `holiday_peak`, `flash_sale`.
- Tham số `start_date` (kiểu String YYYY-MM-DD): Ngày bắt đầu dải dữ liệu. Các giá trị kiểm thử gồm `2024-01-01`, `2024-05-01`, `2024-11-01`, và giá trị lỗi nghịch lý `2025-12-31`.
- Tham số `end_date` (kiểu String YYYY-MM-DD): Ngày kết thúc dải dữ liệu. Các giá trị kiểm thử gồm `2024-01-01`, `2024-05-05`, `2024-06-30`, `2024-12-31`.
- Tham số `growth_rate` (kiểu Float): Hệ số tăng trưởng doanh số. Các giá trị kiểm thử gồm `0.0`, `0.25`, `0.40`, và giá trị lỗi vượt biên `50.0`.
- Tham số `export_csv` (kiểu Boolean): `false` (mặc định) sinh dữ liệu in-memory và trả về preview; `true` xuất file ra đĩa máy chủ tại thư mục `exports/`.
- Header `X-User-Role` (kiểu String): Vai trò người dùng gửi yêu cầu. Các giá trị kiểm thử gồm `admin`, `data_analyst`, và giá trị vi phạm phân quyền `guest`.
- Tham số `column` (kiểu Query String): Tên cột số học cần so sánh phân phối qua endpoint `/compare-distribution`. Các giá trị kiểm thử gồm `net_sales` và giá trị lỗi `hacker_unknown_col_xyz`.

---

## 3. Test trực tiếp trên Swagger UI

### SW-01: Sinh dữ liệu xem trước In-Memory trên giao diện Swagger
- Endpoint: `POST /api/v1/synthetic/generate`
- Thao tác/Body: Mở Swagger UI tại `http://localhost:8000/docs`, chọn endpoint `POST /api/v1/synthetic/generate`, bấm "Try it out", nhập body:
```json
{
  "n_records": 100,
  "scenario": "baseline",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "growth_rate": 0.0,
  "export_csv": false
}
```
Sau đó bấm "Execute".
- Kỳ vọng: HTTP status `200 OK`. Phản hồi trả về cấu trúc JSON gồm: `status: "SUCCESS"`, `total_records: 100`, `total_columns: 38`, `pass_rate_pct: 100.0`, `preview_data` chứa đủ 20 dòng mẫu, `export_filepath: null`.
- Thực tế: Hệ thống phản hồi mã `200 OK` trong 0.063 giây. Toàn bộ các trường dữ liệu hiển thị đúng định dạng trên Swagger UI, không ghi file xuống ổ đĩa máy chủ.
- Kết luận: **PASS**

### SW-02: Stream và tải trực tiếp tệp CSV 38 thuộc tính
- Endpoint: `POST /api/v1/synthetic/download-csv`
- Thao tác/Body: Chọn endpoint `POST /api/v1/synthetic/download-csv`, bấm "Try it out", nhập body:
```json
{
  "n_records": 50,
  "scenario": "baseline",
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "growth_rate": 0.0
}
```
Bấm "Execute", sau đó bấm liên kết "Download file" trong phần Response.
- Kỳ vọng: HTTP status `200 OK`, response header `content-type: text/csv; charset=utf-8`, trình duyệt tải về tệp tin CSV có 38 cột tiêu đề và đúng 50 dòng dữ liệu.
- Thực tế: Trình duyệt tải về tệp `synthetic_ecommerce_baseline_50.csv`, kiểm tra cấu trúc có đúng 51 dòng (1 header + 50 bản ghi) và 38 trường.
- Kết luận: **PASS**

### SW-03: Kiểm tra giao diện Health Check đứng đầu danh mục
- Endpoint: `GET /`
- Thao tác/Body: Mở nhóm `System Health & Service Discovery` ở vị trí trên cùng của Swagger UI, bấm "Try it out" và bấm "Execute".
- Kỳ vọng: HTTP status `200 OK`, body trả về trạng thái `status: "ONLINE"` và danh sách 5 endpoint con khả dụng.
- Thực tế: Phản hồi mã `200 OK` trong 0.018 giây, hiển thị đúng nhóm chức năng đầu tiên trên Swagger UI.
- Kết luận: **PASS**

---

## 4. Test API tự động theo từng case

### API-01 (TC-API-01): Health Check và phát hiện dịch vụ
- Endpoint: `GET /`
- Thao tác/Body: Gửi request GET tới endpoint gốc để kiểm tra trạng thái hoạt động của dịch vụ và danh sách endpoint. Không truyền body.
- Kỳ vọng: HTTP status `200 OK`. Phản hồi trả về `status: "ONLINE"` và danh sách 5 endpoint dịch vụ khả dụng.
- Thực tế: HTTP status `200 OK`, thời gian thực thi 0.0187 giây. Service trả về đúng trạng thái `ONLINE` cùng 5 endpoint con định tuyến đầy đủ.
- Kết luận: **PASS**

### API-02 (TC-API-02): Truy vấn danh mục kịch bản mô phỏng nghiệp vụ
- Endpoint: `GET /api/v1/synthetic/scenarios`
- Thao tác/Body: Gửi request GET để truy vấn các kịch bản mô phỏng được định nghĩa trong hệ thống. Không truyền body.
- Kỳ vọng: HTTP status `200 OK`. Danh sách kịch bản chứa tối thiểu `baseline` và `holiday_peak`.
- Thực tế: HTTP status `200 OK`, thời gian thực thi 0.0047 giây. Hệ thống trả về 4 kịch bản hợp lệ gồm `baseline`, `holiday_peak`, `flash_sale` và `high_churn_risk`.
- Kết luận: **PASS**

### API-03 (TC-API-03): Sinh dữ liệu chuẩn In-Memory với cấu hình hợp lệ (Baseline)
- Endpoint: `POST /api/v1/synthetic/generate`
- Thao tác/Body: Gửi request POST với payload:
```json
{
  "n_records": 100,
  "scenario": "baseline",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "growth_rate": 0.0,
  "export_csv": false
}
```
- Kỳ vọng: HTTP status `200 OK`. `total_records == 100`, `total_columns == 38`, `pass_rate_pct == 100.0`, `export_filepath == null`.
- Thực tế: HTTP status `200 OK`, thời gian thực thi 0.0585 giây. Sinh đủ 100 bản ghi trên bộ nhớ với đúng 38 cột thuộc tính, tỷ lệ tuân thủ quy tắc nghiệp vụ đạt 100.0%.
- Kết luận: **PASS**

### API-04 (TC-API-04): Sinh dữ liệu kịch bản mùa vụ và tăng trưởng doanh số (Holiday Peak)
- Endpoint: `POST /api/v1/synthetic/generate`
- Thao tác/Body: Gửi request POST với payload:
```json
{
  "n_records": 150,
  "scenario": "holiday_peak",
  "start_date": "2024-11-01",
  "end_date": "2024-12-31",
  "growth_rate": 0.25,
  "export_csv": false
}
```
- Kỳ vọng: HTTP status `200 OK`. `total_records == 150`, `pass_rate_pct == 100.0`, `summary_kpis.total_gross_sales > 0`.
- Thực tế: HTTP status `200 OK`, thời gian thực thi 0.0480 giây. Toàn bộ 150 bản ghi thỏa mãn 100.0% ràng buộc, tổng doanh thu gross ghi nhận 47,699.58 USD.
- Kết luận: **PASS**

### API-05 (TC-API-05): Xuất dữ liệu ra tệp máy chủ và bảo vệ tập benchmark gốc (Isolated Export)
- Endpoint: `POST /api/v1/synthetic/generate`
- Thao tác/Body: Gửi request POST với cờ `export_csv = true`:
```json
{
  "n_records": 30,
  "scenario": "flash_sale",
  "start_date": "2024-05-01",
  "end_date": "2024-05-05",
  "growth_rate": 0.4,
  "export_csv": true
}
```
- Kỳ vọng: HTTP status `200 OK`. Tệp CSV được ghi vào thư mục cách ly `data/generated/exports/`, đường dẫn `export_filepath` hợp lệ và không ghi đè vào tệp `data/generated/synthetic_ecommerce.csv`.
- Thực tế: HTTP status `200 OK`, thời gian thực thi 0.0508 giây. Tệp dữ liệu được tạo tại đường dẫn cách ly `synthetic_flash_sale_20261019_184337_30.csv`, tệp benchmark gốc giữ nguyên trạng.
- Kết luận: **PASS**

### API-06 (TC-API-06): Tải trực tiếp dữ liệu dạng luồng CSV (Direct Streaming Download)
- Endpoint: `POST /api/v1/synthetic/download-csv`
- Thao tác/Body: Gửi request POST với payload:
```json
{
  "n_records": 50,
  "scenario": "baseline",
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "growth_rate": 0.0
}
```
- Kỳ vọng: HTTP status `200 OK`, response header `content-type: text/csv; charset=utf-8`. Dữ liệu luồng trả về gồm đúng 38 cột tiêu đề và 50 dòng bản ghi (tổng 51 dòng văn bản).
- Thực tế: HTTP status `200 OK`, thời gian thực thi 0.0377 giây. Định dạng nội dung chuẩn `text/csv`, kiểm tra chính xác 38 cột và 51 dòng văn bản.
- Kết luận: **PASS**

### API-07 (TC-API-07): So sánh phân phối thống kê giữa dữ liệu thực và dữ liệu tổng hợp
- Endpoint: `GET /api/v1/synthetic/compare-distribution?column=net_sales`
- Thao tác/Body: Gửi request GET so sánh phân phối trên trường số học `net_sales` qua query parameter `column=net_sales`.
- Kỳ vọng: HTTP status `200 OK`. Phản hồi trả về đầy đủ các chỉ số thống kê (mean, std, min, p25, median, p75, max) của cả 2 tập `real_distribution` và `synthetic_distribution`.
- Thực tế: HTTP status `200 OK`, thời gian thực thi 0.0531 giây. Trích xuất đầy đủ 7 phân vị thống kê cho cả hai tập dữ liệu (real median: 69.90, synthetic median: 72.28).
- Kết luận: **PASS**

### API-08 (TC-API-08): Thẩm định toàn diện chất lượng dữ liệu qua Quality Gate 4 trụ cột
- Endpoint: `GET /api/v1/synthetic/validate-benchmark`
- Thao tác/Body: Gửi request GET thực thi Quality Gate đối chiếu mẫu 3,000 dòng giữa Seed Data, Holdout Set và Synthetic Benchmark. Không truyền body.
- Kỳ vọng: HTTP status `200 OK`. Báo cáo trả về `validity_pass_rate_pct == 100.0`, `sqi_score >= 80.0`, `status == "PASSED"`, đầy đủ 4 trụ cột Validity, Fidelity, Privacy, Utility.
- Thực tế: HTTP status `200 OK`, thời gian thực thi 0.3810 giây. Chỉ số SQI đạt 95.7/100 điểm, Validity đạt 100.0%, Fidelity đạt 90.5 điểm, Privacy Leakage ở mức an toàn 7.22%, Utility (TSTR) đạt 99.98 điểm.
- Kết luận: **PASS**

### API-09 (TC-API-09): Xử lý ngoại lệ số lượng bản ghi dưới ngưỡng tối thiểu (n_records < 10)
- Endpoint: `POST /api/v1/synthetic/generate`
- Thao tác/Body: Gửi request POST với giá trị vi phạm ràng buộc số lượng tối thiểu `n_records = 3` (yêu cầu tối thiểu là 10):
```json
{
  "n_records": 3,
  "scenario": "baseline"
}
```
- Kỳ vọng: HTTP status `422 Unprocessable Entity`. Trường detail phản hồi thông báo giá trị phải lớn hơn hoặc bằng 10.
- Thực tế: HTTP status `422 Unprocessable Entity`, thời gian thực thi 0.0019 giây. Lỗi được chặn chính xác tại tầng schema Pydantic với thông điệp `Input should be greater than or equal to 10`.
- Kết luận: **PASS**

### API-10 (TC-API-10): Kiểm tra tính bất biến của tập dữ liệu vàng 50,000 dòng
- Endpoint: `SYSTEM (data/generated/synthetic_ecommerce.csv)`
- Thao tác/Body: Đọc và kiểm định trực tiếp số dòng và số cột của tập dữ liệu benchmark sau khi hệ thống hoàn tất các lượt kiểm thử API sinh dữ liệu.
- Kỳ vọng: Tệp dữ liệu tồn tại nguyên vẹn, kích thước đạt chính xác 50,000 dòng và 38 cột, không bị suy giảm hay ghi đè.
- Thực tế: Trạng thái 200 OK, thời gian thực thi 0.2773 giây. Tập dữ liệu giữ nguyên vẹn 50,000 dòng và 38 thuộc tính.
- Kết luận: **PASS**

### API-11 (TC-API-11): Gài lỗi nghịch lý thời gian ngày bắt đầu lớn hơn ngày kết thúc
- Endpoint: `POST /api/v1/synthetic/generate`
- Thao tác/Body: Gửi request POST gài dữ liệu lỗi với ngày bắt đầu trễ hơn ngày kết thúc:
```json
{
  "n_records": 100,
  "scenario": "baseline",
  "start_date": "2025-12-31",
  "end_date": "2024-01-01"
}
```
- Kỳ vọng: HTTP status `422 Unprocessable Entity`. Validator tầng Schema chặn trước khi gọi vào engine sinh dữ liệu.
- Thực tế: HTTP status `422 Unprocessable Entity`, thời gian thực thi 0.0031 giây. Phản hồi thông báo lỗi `start_date cannot be after end_date`.
- Kết luận: **PASS**

### API-12 (TC-API-12): Gài lỗi truy vấn so sánh cột không tồn tại trong lược đồ
- Endpoint: `GET /api/v1/synthetic/compare-distribution?column=hacker_unknown_col_xyz`
- Thao tác/Body: Gửi request GET kiểm tra phân phối với tên cột không nằm trong 38 thuộc tính chuẩn.
- Kỳ vọng: HTTP status `400 Bad Request`. Báo cáo lỗi rõ ràng thay vì phát sinh ngoại lệ nội bộ 500 từ Pandas.
- Thực tế: HTTP status `400 Bad Request`, thời gian thực thi 0.0069 giây. Response body: `{"detail": "Cột 'hacker_unknown_col_xyz' không tồn tại trong danh mục 38 thuộc tính của tập dữ liệu."}`.
- Kết luận: **PASS**

### API-13 (TC-API-13): Gài lỗi hệ số tăng trưởng vượt ngưỡng biên cho phép
- Endpoint: `POST /api/v1/synthetic/generate`
- Thao tác/Body: Gửi request POST gài giá trị `growth_rate = 50.0` (vượt ngưỡng biên tối đa là 10.0):
```json
{
  "n_records": 50,
  "scenario": "baseline",
  "growth_rate": 50.0
}
```
- Kỳ vọng: HTTP status `422 Unprocessable Entity`. Validator chặn do vượt giới hạn `le=10.0`.
- Thực tế: HTTP status `422 Unprocessable Entity`, thời gian thực thi 0.0026 giây. Thông điệp chi tiết: `Input should be less than or equal to 10`.
- Kết luận: **PASS**

### API-14 (TC-API-14): Gài dữ liệu lỗi cấu trúc và kiểm thử cơ chế tự sửa lỗi
- Endpoint: `CORE_ENGINE (backend.schema_learning.rule_parser.ConstraintEngine)`
- Thao tác/Body: Gài DataFrame chứa 2 mẫu vi phạm quy tắc kế toán (`unit_price = -20.0`, `net_sales = 100.0` trong khi `gross_sales = 10.0`) vào bộ kiểm tra `validate_dataframe`, sau đó đưa qua bộ phục hồi `enforce_constraints`.
- Kỳ vọng: Hệ thống phát hiện vi phạm (`invalid_records >= 1`), sau khi chạy `enforce_constraints` dữ liệu được tự động tính toán lại và đưa tỷ lệ hợp lệ về 100.0%.
- Thực tế: Trạng thái 200 OK, thời gian thực thi 0.0096 giây. Giai đoạn 1 phát hiện đúng 1 dòng vi phạm (tỷ lệ hợp lệ ban đầu 50.0%). Giai đoạn 2 tự động sửa chữa đưa tỷ lệ tuân thủ về 100.0% và loại bỏ hoàn toàn lỗi chặn.
- Kết luận: **PASS**

### API-15 (TC-API-15): Kiểm soát phân quyền RBAC chặn truy cập trái phép vai trò guest
- Endpoint: `POST /api/v1/synthetic/generate`
- Thao tác/Body: Gửi request POST sinh dữ liệu kèm header phân quyền không hợp lệ:
  Header: `{"X-User-Role": "guest"}`
  Body:
```json
{
  "n_records": 50,
  "scenario": "baseline"
}
```
- Kỳ vọng: HTTP status `403 Forbidden`. Cổng kiểm soát RBAC từ chối thực thi do vai trò không được cấp phép.
- Thực tế: HTTP status `403 Forbidden`, thời gian thực thi 0.0052 giây. Response body: `{"detail": "Truy cập bị từ chối: Vai trò người dùng không có quyền thực thi thao tác sinh dữ liệu."}`.
- Kết luận: **PASS**

---

## 5. Cảnh báo về giới hạn hệ thống

Dựa trên quá trình kiểm thử thực tế, hệ thống có các giới hạn kỹ thuật cần lưu ý:
- Giới hạn dung lượng sinh In-Memory: Tham số `n_records` qua API bị chặn ở mức tối đa 100,000 dòng để tránh cạn kiệt bộ nhớ RAM máy chủ. Đối với nhu cầu sinh tập dữ liệu lớn hơn (từ 500,000 dòng trở lên), cần sử dụng chế độ chạy hàng loạt theo lô (Batch Processing CLI).
- Thời gian chạy Quality Gate đầy đủ: Endpoint `/validate-benchmark` thực hiện tính toán ma trận tương quan và kiểm định thống kê KS-Test trên mẫu 3,000 dòng mất khoảng 0.4 giây. Nếu nâng mẫu lên toàn bộ 50,000 dòng, thời gian xử lý sẽ tăng lên khoảng 8 - 12 giây, khuyến nghị không gọi endpoint này lặp lại liên tục ở tần suất cao.
- Ràng buộc trường số học: Endpoint `/compare-distribution` chỉ hỗ trợ các cột số học (Float/Integer). Việc truyền các cột định danh phân loại dạng chuỗi (`city`, `payment_type`) sẽ bị từ chối xử lý với mã `400 Bad Request`.
- Cơ chế RBAC hiện tại: Tầng phân quyền API hiện đang hoạt động dựa trên kiểm tra header `X-User-Role` ở mức Gateway cục bộ. Khi tích hợp với hệ thống xác thực chung (`backend/auth.py`), cần bổ sung kiểm tra chữ ký số JWT Bearer Token.

---

## 6. Danh mục tệp bằng chứng kiểm thử

Các tệp mã nguồn kiểm thử và kết quả thực thi được lưu trữ trực tiếp trong repository:
- Báo cáo kết quả kiểm thử API chi tiết dạng JSON: `data/generated/api_test_results.json`
- Script thực thi kiểm thử API tự động theo từng case: `tests/run_api_test_suite.py`
- Bộ unit test tích hợp API (11 tests): `tests/test_08_synthetic_api.py`
- Router định tuyến và xử lý lỗi: `backend/synthetic_generator/api/router.py`
- Schema ràng buộc dữ liệu đầu vào: `backend/synthetic_generator/api/schemas.py`
- Giao diện Swagger UI phục vụ kiểm thử thủ công: `backend/synthetic_generator/api/standalone_server.py`
- Tệp dữ liệu tổng hợp chuẩn bàn giao (50,000 dòng): `data/generated/synthetic_ecommerce.csv`
- Báo cáo thẩm định chất lượng dữ liệu tổng hợp: `data/generated/synthetic_validation_report.json`
