# AI_BI_DASHBOARD_V1

Backend cho hệ thống **AI BI Dashboard**, xây dựng bằng Python, FastAPI và SQLite. Dự án cung cấp một luồng xử lý BI hoàn chỉnh từ nhập dữ liệu, EDA, kiểm tra chất lượng, suy luận schema, tính KPI, tạo cấu hình biểu đồ đến sinh dữ liệu tổng hợp, chatbot, text-to-SQL an toàn và xuất báo cáo.

Hệ thống sử dụng kiến trúc monolith chia module, ưu tiên code rõ ràng, dễ kiểm thử và có thể chạy local mà không cần dịch vụ bên ngoài khi dùng `LLM_PROVIDER=deterministic`.

## Tính năng chính

- Đăng ký tài khoản theo quy trình phê duyệt: request → approve/reject → provision → activate.
- JWT cho access token và activation token; PBKDF2-SHA256 cho mật khẩu.
- RBAC với ba role `admin`, `manager`, `user`, permission allowlist và data scope.
- Nhập và chuẩn hóa dữ liệu CSV/JSON.
- EDA, data profiling, missing/duplicate/outlier và đánh giá chất lượng dữ liệu.
- Suy luận kiểu dữ liệu, khóa tiềm năng, tương quan và quan hệ giữa nhiều bảng.
- KPI E-commerce: doanh thu, chi phí, lợi nhuận, AOV, CAC, ROAS và LTV.
- Cấu hình dữ liệu cho biểu đồ xu hướng, top sản phẩm và cơ cấu.
- Sinh dữ liệu tổng hợp bằng `bootstrap`, `gaussian_copula`, `ctgan`, `copulagan` hoặc `llm_agent`.
- Đánh giá synthetic data theo validity, fidelity, privacy, utility và TSTR khi có `target_column`.
- Chatbot với deterministic fallback, OpenAI Responses API, Gemini và Llama OpenAI-compatible.
- RAG context từ dashboard và chuyển câu hỏi tiếng Việt thành SQL chỉ đọc.
- Xuất báo cáo JSON, CSV, HTML, PDF, XLSX và PPTX.
- CORS allowlist, request ID, process time, giới hạn payload và lỗi nội bộ đã được làm sạch.

## Cấu trúc dự án

```text
AI_BI_DASHBOARD_V1/
├── backend/
│   ├── main.py                 # FastAPI app, routes, middleware và error handlers
│   ├── config.py               # Cấu hình từ biến môi trường
│   ├── auth.py                 # SQLite auth, JWT, RBAC và registration workflow
│   ├── eda/                    # Profiling và kiểm tra chất lượng dữ liệu
│   ├── schema_learning/        # Schema, quan hệ bảng và business rules
│   ├── synthetic_generator/    # Generator, pipeline và validator
│   ├── dashboard_engine/       # Ingestion, KPI, charts và report exporter
│   └── chatbot/                # LLM router, RAG, prompts và text-to-SQL
├── data/                       # SQLite và dữ liệu local
├── tests/                      # Unit/core và API integration tests
├── .env.example
├── requirements.txt
├── requirements-ai.txt
├── requirements-dev.txt
└── README.md
```

Luồng BI chính:

```text
CSV/JSON → validation/cleaning → EDA/quality → schema → KPI/charts
         → dashboard context → chat/SQL/report
```

## Yêu cầu môi trường

- Python 3.11 trở lên.
- Windows, Linux hoặc macOS.
- SQLite đi kèm Python.
- `pandas` và `sdv` chỉ bắt buộc khi dùng các model synthetic nâng cao.

## Cài đặt

### Windows PowerShell

```powershell
git clone <repository-url>
cd AI_BI_DASHBOARD_V1

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Cài thêm dependency cho Gaussian Copula, CTGAN hoặc CopulaGAN:

```powershell
pip install -r requirements-ai.txt
```

Cài dependency phục vụ phát triển và kiểm thử:

```powershell
pip install -r requirements-dev.txt
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Cấu hình

Ứng dụng đọc biến từ **process environment**. Dùng `.env.example` làm mẫu rồi khai báo các biến trong PowerShell, IDE hoặc công cụ triển khai. Source hiện không tự nạp file `.env` nếu chạy trực tiếp bằng lệnh Uvicorn.

```env
APP_ENV=development
JWT_SECRET=replace-with-at-least-32-random-characters
DATABASE_PATH=data/app_database.db
CORS_ORIGINS=http://localhost:5173
MAX_UPLOAD_BYTES=10485760
MAX_ROWS=100000

ADMIN_USERNAME=admin
ADMIN_PASSWORD=replace-with-a-strong-password

LLM_PROVIDER=deterministic
LLM_TIMEOUT_SECONDS=30
OPENAI_API_KEY=
OPENAI_MODEL=gpt-6-astra
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
LLAMA_BASE_URL=http://localhost:11434
LLAMA_MODEL=llama
```

Không commit secret, mật khẩu hoặc token thật. Ở `APP_ENV=production`, `JWT_SECRET` phải có ít nhất 32 ký tự.

`ADMIN_USERNAME` và `ADMIN_PASSWORD` được dùng để bootstrap tài khoản quản trị. Nếu database đã tồn tại, thay đổi hai biến này không tự động đổi thông tin tài khoản đã lưu.

## Chạy backend

Chạy từ **project root** để Python nhận đúng package `backend`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Hoặc khi virtual environment đã được kích hoạt:

```powershell
python -m uvicorn backend.main:app --reload
```

Các địa chỉ mặc định:

- API: <http://127.0.0.1:8000>
- Health check: <http://127.0.0.1:8000/health>
- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

Không nên chạy `python backend/main.py` từ bên trong thư mục `backend/`, vì cách đó có thể gây `ModuleNotFoundError: backend`.

## Quy trình đăng ký và đăng nhập

```text
Registration request
  → PENDING
  → Admin APPROVE hoặc REJECT
  → Admin provision
  → PENDING_ACTIVATION
  → Login bằng mật khẩu tạm
  → Activation token (10 phút)
  → POST /auth/activate
  → ACTIVE
  → Login lại
  → Access token (mặc định 60 phút)
```

### 1. Nhân viên gửi yêu cầu cấp tài khoản

```http
POST /auth/register-request
Content-Type: application/json
```

```json
{
  "employee_id": "NV00125",
  "full_name": "Nguyen Van A",
  "position": "Truong phong",
  "department": "Sales"
}
```

`POST /auth/register` là alias deprecated và chỉ nhận cùng payload trên. Payload cũ chứa `username`/`password` sẽ bị từ chối với `422`.

### 2. Admin duyệt hoặc từ chối

Admin lấy danh sách tại `GET /admin/registration-requests`, sau đó gọi một trong hai endpoint:

```http
POST /admin/registration-requests/{request_id}/approve
POST /admin/registration-requests/{request_id}/reject
```

Body approve có thể là `{}`. Reject bắt buộc có lý do:

```json
{
  "rejection_reason": "Thong tin nhan su chua duoc xac minh"
}
```

Approve chỉ đổi trạng thái request; không tự tạo user và không tự cấp quyền.

### 3. Admin provision tài khoản

```http
POST /admin/users/provision
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

```json
{
  "registration_request_id": 12,
  "temporary_password": "TemporaryPassword123!",
  "role": "manager",
  "permissions": ["dashboard:view", "report:view"],
  "data_scope": "department"
}
```

Tài khoản được tạo với username bằng `employee_id` và trạng thái `PENDING_ACTIVATION`.

### 4. Đăng nhập bằng mật khẩu tạm và kích hoạt

```http
POST /auth/login
Content-Type: application/json
```

```json
{
  "username": "NV00125",
  "password": "TemporaryPassword123!"
}
```

Backend trả token có `purpose=activation`, mặc định hết hạn sau 10 phút. Gửi token này bằng Bearer header tới:

```http
POST /auth/activate
Authorization: Bearer <activation_token>
Content-Type: application/json
```

```json
{
  "new_password": "MyNewStrongPassword123!",
  "confirm_password": "MyNewStrongPassword123!"
}
```

Sau response `204`, đăng nhập lại bằng mật khẩu mới để nhận token có `purpose=access`. Activation token không truy cập được API private thông thường.

### 5. Kiểm tra user hiện tại

```http
GET /auth/me
Authorization: Bearer <access_token>
```

Response gồm role, account status, permissions và data scope hiện tại.

## Phân quyền

### Roles và account status

| Nhóm | Giá trị |
|---|---|
| Role | `admin`, `manager`, `user` |
| Account status | `PENDING_ACTIVATION`, `ACTIVE`, `DISABLED` |
| Data scope | `own`, `department`, `all` |

Private API chỉ chấp nhận access token của account `ACTIVE`. Mỗi request đều đối chiếu `token_version` và trạng thái account trong SQLite.

Permission allowlist và bộ quyền mặc định hiện tại:

```text
dashboard:view    dataset:upload    dataset:view
kpi:view          chart:view        synthetic:generate
chat:use          report:view       report:export
user:manage
```

- `user`: các quyền xem dashboard/data/KPI/chart, dùng chat, upload và xem report.
- `manager`: toàn bộ permission trừ `user:manage`.
- `admin`: toàn bộ permission.
- `/synthetic/*`: chỉ `manager` hoặc `admin`.
- `/admin/*` và đổi role: chỉ `admin`.

> Route authorization hiện enforce account state và role. `permissions`/`data_scope` được validate, lưu và trả về trong account context nhưng chưa được kiểm tra riêng cho từng analytics route. Analytics cũng nhận `rows` trực tiếp trong request và chưa có đầy đủ bảng dataset/resource persisted với `owner_id`/`department`, nên resource ownership ở cấp dataset chưa được enforce hoàn chỉnh.

## API theo module

| Module | Method và endpoint | Quyền truy cập |
|---|---|---|
| Root | `GET /`, `GET /health` | Public |
| Auth | `POST /auth/register-request`, `POST /auth/register`, `POST /auth/login` | Public |
| Auth | `POST /auth/activate` | Activation token |
| Auth | `GET /auth/me` | Access token |
| User management | `POST /auth/users/{user_id}/role` | Admin |
| Registration admin | `GET /admin/registration-requests` | Admin |
| Registration admin | `GET /admin/registration-requests/{request_id}` | Admin |
| Registration admin | `POST .../{request_id}/approve`, `POST .../{request_id}/reject` | Admin |
| Registration admin | `POST /admin/users/provision` | Admin |
| Data/EDA | `POST /datasets/analyze?filename=...` | Active user |
| Data/EDA | `POST /datasets/profile`, `/datasets/quality`, `/datasets/schema` | Active user |
| Schema | `POST /schema/infer-relations` | Active user |
| Dashboard | `POST /dashboard/kpis`, `/dashboard/charts` | Active user |
| Synthetic | `POST /synthetic/generate`, `/synthetic/validate` | Manager/Admin |
| Chat | `POST /chat/query`, `/chat/sql` | Active user |
| Reports | `POST /reports/export?format=...` | Active user |

Các request model và response model chi tiết được hiển thị trong Swagger UI.

## Ví dụ gọi API

### Health check

```powershell
curl.exe http://127.0.0.1:8000/health
```

### Gửi registration request

```powershell
curl.exe -X POST "http://127.0.0.1:8000/auth/register-request" `
  -H "Content-Type: application/json" `
  -d '{"employee_id":"NV00125","full_name":"Nguyen Van A","position":"Truong phong","department":"Sales"}'
```

### Login và gọi API private

```powershell
curl.exe -X POST "http://127.0.0.1:8000/auth/login" `
  -H "Content-Type: application/json" `
  -d '{"username":"NV00125","password":"MyNewStrongPassword123!"}'

curl.exe "http://127.0.0.1:8000/auth/me" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Phân tích raw CSV

`/datasets/analyze` nhận raw UTF-8 CSV/JSON body; đuôi của query `filename` quyết định parser:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/datasets/analyze?filename=sales.csv" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -H "Content-Type: application/octet-stream" `
  --data-binary "@data/sales.csv"
```

Các endpoint analytics còn lại nhận JSON dạng:

```json
{
  "rows": [
    {
      "order_id": "OD001",
      "date": "2026-10-01",
      "product": "Laptop",
      "quantity": 1,
      "revenue": 25000000,
      "cost": 21000000
    }
  ]
}
```

## Synthetic data

`POST /synthetic/generate` hỗ trợ:

- `bootstrap`: chạy với base requirements, deterministic khi cung cấp `seed`.
- `gaussian_copula`, `ctgan`, `copulagan`: cần `requirements-ai.txt`.
- `llm_agent`: cần `LLM_PROVIDER=openai|gemini|llama` và provider tương ứng hoạt động.

Ví dụ phần cấu hình request:

```json
{
  "rows": [{"order_id": "OD001", "date": "2026-10-01", "product": "A", "quantity": 1, "revenue": 100, "cost": 60}],
  "count": 100,
  "seed": 42,
  "model": "bootstrap",
  "target_column": null
}
```

## LLM providers và text-to-SQL

Chọn provider qua `LLM_PROVIDER`:

| Giá trị | Cấu hình bổ sung | Ghi chú |
|---|---|---|
| `deterministic` | Không | Mặc định cho local/test, không gọi mạng |
| `openai` | `OPENAI_API_KEY`, `OPENAI_MODEL` | OpenAI Responses API |
| `gemini` | `GEMINI_API_KEY`, `GEMINI_MODEL` | Gemini `generateContent` |
| `llama` | `LLAMA_BASE_URL`, `LLAMA_MODEL` | Server OpenAI-compatible |

Provider thật cần API key hoặc server tương ứng. Bộ test mặc định mock hoặc dùng chế độ offline, không chứng minh dịch vụ bên ngoài đang khả dụng.

`/chat/sql` chỉ trả SQL đã qua guardrail:

- Chỉ cho phép `SELECT`.
- Chỉ truy cập bảng/cột trong allowlist.
- Chặn multi-statement và các lệnh ghi/xóa/attach/pragma nguy hiểm.
- Giới hạn tối đa `LIMIT 500`.
- Lớp thực thi SQLite dùng `query_only` và authorizer.

## Xuất báo cáo

`POST /reports/export?format=<format>` hỗ trợ:

| Format | Media type/đầu ra |
|---|---|
| `json` | JSON |
| `csv` | CSV |
| `html` | HTML |
| `pdf` | PDF |
| `xlsx` | Excel workbook |
| `pptx` | PowerPoint presentation |

CSV/XLSX có xử lý chống formula injection. Nếu dependency tạo file tương ứng không khả dụng, endpoint có thể trả `501` thay vì tạo file giả.

## Chạy test

Từ project root:

```powershell
.\.venv\Scripts\python.exe -u -m unittest discover -s tests -v
```

Kết quả gần nhất: **17/17 test PASS**.

Phạm vi kiểm thử gồm auth guard, registration/approval/rejection/provision/activation, conflict/duplicate, role matrix, private analytics, OpenAPI/CORS, schema relations, synthetic data, chatbot, SQL read-only, các report binary, JWT tamper/expiry và sanitized error.

Khi thay đổi backend, hãy chạy lại toàn bộ suite thay vì chỉ chạy test của module vừa sửa.

## Giới hạn hiện tại

- Chưa có refresh token, logout/revocation list, MFA, OAuth/SSO hoặc password reset self-service.
- Chưa có email verification/gửi email tự động và HR synchronization.
- Chưa có dataset persistence đầy đủ để enforce ownership/department trên mọi tài nguyên analytics.
- SQLite phù hợp local/MVP; cần đánh giá lại storage và concurrency trước khi triển khai tải lớn.
- Khả dụng thực tế của OpenAI, Gemini và Llama phụ thuộc credential, model và server bên ngoài; không được xác nhận bởi test offline.

## Troubleshooting

### `ModuleNotFoundError: backend`

Đứng tại project root và chạy:

```powershell
python -m uvicorn backend.main:app --reload
```

### PowerShell không cho activate virtual environment

Không bắt buộc activate; có thể dùng trực tiếp:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

### SQLite không tạo được database

Kiểm tra `DATABASE_PATH` và bảo đảm thư mục cha có quyền ghi. Mặc định là `data/app_database.db`.

### API trả `401`

Kiểm tra Bearer header và loại token. Private API cần **access token**, không phải activation token. Token cũng bị từ chối khi hết hạn, chữ ký sai, `token_version` cũ hoặc account không còn `ACTIVE`.

### API trả `403`

User đã được xác thực nhưng không đủ role/quyền cho endpoint. Synthetic cần manager/admin; admin workflow cần admin.

### Model synthetic nâng cao không chạy

```powershell
pip install -r requirements-ai.txt
```

### Provider LLM không hoạt động

Kiểm tra `LLM_PROVIDER` cùng API key/base URL/model tương ứng. Nếu chỉ cần chạy local ổn định:

```env
LLM_PROVIDER=deterministic
```

### Request bị từ chối vì quá lớn

Kiểm tra `MAX_UPLOAD_BYTES` và `MAX_ROWS`. Giá trị mặc định lần lượt là 10 MiB và 100.000 dòng.

## Ghi chú bảo mật

- Không commit `JWT_SECRET`, `ADMIN_PASSWORD`, API key hoặc JWT.
- Dùng secret ngẫu nhiên đủ dài và giới hạn `CORS_ORIGINS` khi triển khai production.
- Không cho client tự chọn role, permission hoặc data scope ngoài workflow admin.
- Không chạy trực tiếp SQL do LLM tạo ra mà bỏ qua text-to-SQL guardrails.
- Bảo vệ file SQLite và thư mục `data/` bằng quyền filesystem phù hợp.
