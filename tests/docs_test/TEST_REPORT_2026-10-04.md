# BÁO CÁO KIỂM THỬ BACKEND AI BI DASHBOARD

- Ngày kiểm thử: 04/10/2026, múi giờ Asia/Saigon
- Phiên bản API: `0.1.0`
- Python: `3.12.14`
- Framework: FastAPI, SQLite, JWT/RBAC
- Kiểm thử tự động: pytest `9.1.1`
- Kiểm thử giao diện: Swagger UI trên server thật tại `http://127.0.0.1:8001/docs`

## 1. Kết luận

Kết quả cuối: **15/15 test pytest PASS** trong 2,38 giây. Toàn bộ endpoint private đã được gọi thành công với JWT hợp lệ; các nhánh từ chối `401`, `403`, `400`, `413`, `422` và lỗi `500` đã được kiểm tra. Ma trận quyền `user`, `manager`, `admin` hoạt động đúng.

Ba thiếu sót quan trọng của lần kiểm thử trước đã được sửa:

1. Swagger dùng security scheme `HTTPBearer`, có nút **Authorize** chung và tự gắn header `Authorization: Bearer <token>`.
2. `POST /datasets/analyze` có request body `application/octet-stream` bắt buộc và nút **Choose File** để upload CSV/JSON.
3. Các response chính có schema đặt tên rõ ràng; mở `/` trả thông tin dịch vụ và đường dẫn `/health`, `/docs` thay vì 404.

## 2. Dữ liệu test chuẩn

### 2.1. Dataset E-commerce

```json
[
  {"date":"2026-10-01","order_id":"O001","product":"Bag A","revenue":100.0,"cost":60.0},
  {"date":"2026-10-02","order_id":"O002","product":"Bag B","revenue":200.0,"cost":80.0}
]
```

Kết quả chuẩn dùng để đối chiếu:

- Tổng doanh thu: `300`
- Tổng chi phí: `140`
- Lợi nhuận ròng: `160`
- Số đơn: `2`
- Giá trị đơn trung bình: `150`

### 2.2. Ma trận quyền

| Hành động | Không token | user | manager | admin |
|---|---:|---:|---:|---:|
| Analytics, schema, KPI, chart, chat, report | 401 | 200 | 200 | 200 |
| Sinh/kiểm định dữ liệu tổng hợp | 401 | 403 | 200 | 200 |
| Đổi role người dùng | 401 | 403 | 403 | 200 |

Mật khẩu và JWT thật không được ghi vào báo cáo. Test tạo tài khoản cục bộ trong database tạm; không tác động database nghiệp vụ.

## 3. Test trực tiếp trên Swagger UI

### SW-01 - Đăng nhập admin

- Endpoint: `POST /auth/login`.
- Thao tác: mở endpoint → **Try it out** → thay JSON mẫu bằng tài khoản admin test → **Execute**.
- Dữ liệu nhập: username `swagger_admin`, mật khẩu test cục bộ.
- Kỳ vọng: `200`, có `access_token`, `token_type = bearer`, `expires_in = 3600`.
- Thực tế: đúng toàn bộ kỳ vọng. **PASS**.

### SW-02 - Authorize và gọi endpoint private

- Thao tác: bấm **Authorize** → nhập JWT nhận từ SW-01 → **Apply credentials** → mở `GET /auth/me` → **Try it out** → **Execute**.
- Kiểm tra curl do Swagger sinh: có header `Authorization: Bearer ...`.
- Kỳ vọng: `200`, trả đúng username và `role = admin`.
- Thực tế: `200`, response có `sub`, `username = swagger_admin`, `role = admin`. **PASS**.

### SW-03 - Upload và phân tích CSV

- Endpoint: `POST /datasets/analyze`.
- Thao tác: **Try it out** → nhập `filename = sales.csv` → **Choose File** → chọn `tests/fixtures/sales.csv` → **Execute**.
- Nội dung file:

```csv
date,order_id,product,revenue,cost
2026-10-01,O001,Bag A,100,60
2026-10-02,O002,Bag B,200,80
```

- Kiểm tra curl: có Bearer token, `Content-Type: application/octet-stream` và `--data-binary '@sales.csv'`.
- Kỳ vọng: `200`, 2 dòng/5 cột, KPI `net_profit = 160`.
- Thực tế: đúng; response còn có schema, profile, quality, charts. **PASS**.

## 4. Test API tự động theo từng case

Lệnh chạy:

```powershell
D:\AI_BI\AI_BI_DASHBOARD_V1\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

### API-01 - Route gốc và health

- Gọi `GET /`: không nhập dữ liệu.
- Kỳ vọng/thực tế: `200`, trả tên dịch vụ, version, `health = /health`, `docs = /docs`.
- Gọi `GET /health`: kỳ vọng/thực tế `200`, `{"status":"ok","version":"0.1.0"}`.
- Kết quả: **PASS**.

### API-02 - Đăng ký, đăng nhập và `/auth/me`

- Đăng ký `api_user` bằng body `{"username":"api_user","password":"<test-password>"}`.
- Đăng nhập cùng thông tin, lấy JWT rồi gọi `GET /auth/me`.
- Kỳ vọng/thực tế: đăng ký `201`; login `200`; `/auth/me` trả `role = user`.
- Kết quả: **PASS**.

### API-03 - Chặn request không hợp lệ

- `POST /dashboard/kpis` không token → `401`.
- `GET /auth/me` với `Authorization: Basic bad` → `401`.
- `GET /health` với `Content-Length` lớn hơn giới hạn → `413`.
- Kết quả: **PASS**.

### API-04 - CORS

- Gửi `OPTIONS /dashboard/kpis` với origin được cấu hình và method `POST`.
- Thực tế: `200`, có `Access-Control-Allow-Origin` đúng origin.
- Gửi lại với `https://evil.example`.
- Thực tế: không có `Access-Control-Allow-Origin`.
- Kết quả: **PASS**.

### API-05 - OpenAPI và Schemas

- Tải `GET /openapi.json`.
- Kiểm tra: có `components.securitySchemes.HTTPBearer`; `/auth/me` có security requirement; `/datasets/analyze` có `requestBody`; private API khai báo response `401`; RBAC API khai báo `403`.
- Kiểm tra response `200` của `/datasets/analyze` tham chiếu `#/components/schemas/AnalysisResponse`.
- Kết quả: **PASS**.

### API-06 - Upload CSV

- Gửi `POST /datasets/analyze?filename=sales.csv`.
- Header: JWT user và `Content-Type: application/octet-stream`.
- Body: bytes của CSV chuẩn ở mục 2.1.
- Kỳ vọng/thực tế: `200`, `net_profit = 160`. **PASS**.

### API-07 - Profiling

- Gửi `POST /datasets/profile`, body `{"rows": <dataset chuẩn>}` với JWT user.
- Kỳ vọng/thực tế: `200`, `row_count = 2`, có count/null/unique/type và thống kê số cho từng cột. **PASS**.

### API-08 - Quality

- Gửi `POST /datasets/quality` với dataset chuẩn.
- Kỳ vọng/thực tế: `200`, `score = 1.0`, không thiếu, không trùng, không có outlier. **PASS**.

### API-09 - Schema một bảng

- Gửi `POST /datasets/schema` với dataset chuẩn.
- Kỳ vọng/thực tế: `200`; cột `revenue` được suy luận `type = float`, `nullable = false`; có quan hệ correlation giữa cột số. **PASS**.

### API-10 - Schema nhiều bảng và quan hệ khóa

- Endpoint: `POST /schema/infer-relations`.
- Body:

```json
{
  "tables": {
    "customers": [{"customer_id":"C1"},{"customer_id":"C2"}],
    "orders": [{"order_id":"O1","customer_id":"C1"},{"order_id":"O2","customer_id":"C2"}]
  }
}
```

- Kỳ vọng/thực tế: nhận diện `customers.customer_id` là ứng viên primary key và `orders.customer_id` là foreign key. **PASS**.

### API-11 - KPI

- Gửi `POST /dashboard/kpis`, body `{"rows": <dataset chuẩn>}`.
- Kỳ vọng/thực tế: revenue `300`, cost `140`, net profit `160`, order count `2`, AOV `150`. **PASS**.

### API-12 - Charts

- Gửi `POST /dashboard/charts` với dataset chuẩn.
- Kỳ vọng/thực tế: `200`, trả danh sách cấu hình biểu đồ, trong đó có Revenue by Date và Top Products. **PASS**.

### API-13 - Chat phân tích dashboard

- Gửi `POST /chat/query` với `question = "Tóm tắt KPI"` và dataset chuẩn.
- Kỳ vọng/thực tế: `200`, câu trả lời được grounding bằng context hiện tại và chứa tổng doanh thu `300.0`. **PASS**.

### API-14 - Text-to-SQL

- Gửi `POST /chat/sql` với `question = "Doanh thu theo sản phẩm"`.
- Kỳ vọng/thực tế: `200`, câu SQL bắt đầu bằng `SELECT` và được giới hạn read-only.
- Test bổ sung từ chối `DROP`, bảng/cột ngoài allowlist, nhiều statement và `DELETE`. **PASS**.

### API-15 - Xuất báo cáo

- Lần lượt gọi `POST /reports/export?format=json|csv|html|pdf|xlsx|pptx` với dataset chuẩn.
- Kiểm tra `200`, `Content-Disposition` đúng tên file.
- Kiểm tra chữ ký nhị phân: PDF bắt đầu `%PDF`; XLSX/PPTX bắt đầu `PK`.
- Test sâu mở XLSX bằng openpyxl, mở PPTX bằng python-pptx và kiểm tra tiêu đề slide.
- Kết quả: **PASS** cho cả 6 định dạng.

### API-16 - RBAC user

- Dùng JWT role `user` gọi `POST /synthetic/generate`.
- Kỳ vọng/thực tế: `403 Manager or admin role required`. **PASS**.

### API-17 - RBAC manager và synthetic workflow

- Admin test setup gán role `manager`, sau đó đăng nhập lại để nhận JWT chứa role mới.
- Manager gửi:

```json
{"rows": <dataset chuẩn>, "count":3, "seed":42, "model":"bootstrap"}
```

- `/synthetic/generate`: `200`, tạo đúng 3 dòng.
- `/synthetic/validate`: gửi original rows và 3 synthetic rows; `200`, có đủ `validity`, `fidelity`, `privacy`, `utility`, `details`.
- Manager gọi đổi role người khác: `403`.
- Kết quả: **PASS**.

### API-18 - RBAC admin

- Admin gọi `POST /auth/users/{id}/role` với `{"role":"manager"}`.
- Kỳ vọng/thực tế: `200`, response trả đúng id và role mới. **PASS**.

### API-19 - Validation 422 và dữ liệu xấu 400

- `question = ""` → `422`.
- synthetic `count = 0` → `422`.
- thêm field top-level `unexpected` → `422` vì request model dùng `extra = forbid`.
- role `owner` → `422`, chỉ chấp nhận `admin|manager|user`.
- `revenue = "not-a-number"` → `400`.
- Kết quả: **PASS**.

### API-20 - Che thông tin lỗi 500

- Mock hàm KPI phát sinh `RuntimeError("secret C:\\internal\\path")`.
- Gọi endpoint với `raise_server_exceptions = false`.
- Kỳ vọng/thực tế: `500`, mã `INTERNAL_ERROR`; response không chứa secret hoặc đường dẫn nội bộ; có request ID. **PASS**.

### API-21 - JWT và bảo mật bổ sung

- Password lưu dạng hash; sai password không đăng nhập được.
- JWT hợp lệ giải mã đúng; token bị sửa chữ ký và token hết hạn đều bị từ chối.
- CSV export neutralize formula bắt đầu bằng `=`, `@`, kể cả có khoảng trắng/tab.
- Correlation với cột hằng không chia cho 0.
- Kết quả: **PASS**.

## 5. Schemas có tác dụng gì và được kiểm tra thế nào

`Schemas` trong Swagger là hợp đồng dữ liệu giữa frontend và backend:

- Request schema cho biết field bắt buộc, kiểu dữ liệu, giới hạn và giá trị hợp lệ.
- Response schema cho biết cấu trúc frontend sẽ nhận về.
- FastAPI/Pydantic dùng cùng schema để kiểm tra runtime; payload sai trả `422` trước khi vào nghiệp vụ.
- OpenAPI dùng schema để sinh form **Try it out**, tài liệu và client SDK.

Các schema request hiện có: `Credentials`, `RoleRequest`, `DatasetRequest`, `TablesRequest`, `SyntheticRequest`, `SyntheticValidationRequest`, `ChatRequest`.

Các schema response chính: `RootResponse`, `HealthResponse`, `UserResponse`, `TokenResponse`, `CurrentUserResponse`, `RoleResponse`, `ProfileResponse`, `QualityResponse`, `SchemaResponse`, `KpiResponse`, `AnalysisResponse`, `RelationsResponse`, `SyntheticResponse`, `SyntheticValidationResponse`, `ChatResponse`, `SqlResponse`.

Ví dụ kiểm tra schema:

1. Mở `POST /synthetic/generate` → tab **Schema**.
2. Quan sát `count` có min `1`, max `100000`; `model` chỉ nhận các model đã khai báo.
3. Gửi `count = 0`; hệ thống trả `422`.
4. Mở response `200`; Swagger tham chiếu `SyntheticResponse`, không còn object vô danh.

## 6. Phạm vi unit/regression còn lại

11 test lõi trong `tests/test_backend.py` tiếp tục PASS, bao phủ:

- ingest CSV/JSON và từ chối JSON/CSV lỗi;
- KPI, profile, quality, schema và chart;
- rule engine và synthetic deterministic theo seed;
- TSTR regression cho utility;
- JWT, hash password, expired/tampered token;
- SQL read-only và SQLite query-only;
- PDF, XLSX, PPTX, CSV formula-injection;
- suy luận quan hệ nhiều bảng;
- hợp đồng OpenAI Responses API, Gemini và Llama bằng HTTP mock;
- `llm_agent` kiểm tra JSON và thay định danh synthetic.

## 7. Cảnh báo và giới hạn đã biết

- Pytest hiển thị một `DeprecationWarning` bên trong `starlette.testclient` về alias `anyio.abc.BlockingPortal`. Đây là cảnh báo từ dependency test, không phải lỗi API; mọi test vẫn PASS.
- OpenAI/Gemini/Llama được test contract bằng mock, không gọi dịch vụ thật vì môi trường test không cung cấp API key. Provider `deterministic` đã chạy thật offline.
- API integration phải chạy ngoài sandbox hạn chế của Windows vì `TestClient` cần socketpair nội bộ. Khi chạy đúng môi trường, toàn bộ suite hoàn tất trong khoảng 2,4 giây; không có deadlock của ứng dụng.

## 8. File bằng chứng

- `backend/main.py`: security scheme, route, response schema, middleware và error handling.
- `tests/test_api.py`: role matrix, toàn bộ private endpoint, CORS/OpenAPI và error paths.
- `tests/test_backend.py`: unit/regression nghiệp vụ và hardening.
- `tests/conftest.py`: cô lập thư mục tạm trong workspace.
- `tests/fixtures/sales.csv`: file upload dùng cho Swagger case SW-03.
- `AUTH_TEST_REPORT_2026-10-07.md`: báo cáo chuyên sâu cho đăng ký, đăng nhập, JWT và lưu mật khẩu.

Kết luận nghiệm thu backend trong phạm vi code hiện tại: **PASS**, với giới hạn provider cloud nêu ở mục 7.
