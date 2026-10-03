# AI BI Dashboard Backend

FastAPI backend cho luồng: xác thực → nạp dữ liệu → EDA/schema/quality → KPI & chart → dữ liệu tổng hợp → chatbot → xuất báo cáo.

## Chạy ứng dụng

```powershell
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

Chạy trực tiếp bằng nút **Run Python File** hoặc `python backend/main.py` cũng được hỗ trợ. Có thể đổi cổng bằng biến `API_PORT`.

Muốn huấn luyện `gaussian_copula`, `ctgan` hoặc `copulagan`:

```powershell
python -m pip install -r requirements-ai.txt
```

Swagger UI: `http://127.0.0.1:8000/docs`.

## Cấu hình chính

Sao chép `.env.example` thành biến môi trường của máy. Trong production bắt buộc đặt `JWT_SECRET` tối thiểu 32 ký tự. `ADMIN_USERNAME` và `ADMIN_PASSWORD` tạo tài khoản quản trị đầu tiên nếu database chưa có tài khoản đó.

`LLM_PROVIDER` nhận một trong `deterministic`, `openai`, `gemini`, `llama`. OpenAI dùng Responses API; Gemini dùng `generateContent`; Llama gọi server tương thích OpenAI tại `LLAMA_BASE_URL`.

## API theo module

- Auth/RBAC: `/auth/register`, `/auth/login`, `/auth/me`, `/auth/users/{id}/role`.
- Dữ liệu/EDA: `/datasets/analyze`, `/datasets/profile`, `/datasets/quality`, `/datasets/schema`.
- Dashboard: `/dashboard/kpis`, `/dashboard/charts`.
- Synthetic: `/synthetic/generate`, `/synthetic/validate` (manager/admin).
- Chatbot: `/chat/query`, `/chat/sql`.
- Báo cáo: `/reports/export?format=json|csv|html|pdf|xlsx|pptx`.

## Điểm kiểm tra và fix bug

- `dashboard_engine/data_pipeline.py`: encoding, định dạng, cột bắt buộc, kiểu số và giới hạn dòng.
- `auth.py`: SQLite, PBKDF2, JWT HS256 và role `admin/manager/user`.
- `chatbot/llm_router.py`: khóa API, endpoint provider, timeout và fallback có metadata.
- `chatbot/text_to_sql.py`: một câu `SELECT`, allowlist bảng/cột, `LIMIT 500`, SQLite query-only.
- `synthetic_generator/generator_model.py`: chọn bootstrap, SDV (`gaussian_copula`, `ctgan`, `copulagan`) hoặc `llm_agent`; chế độ LLM giới hạn 200 dòng và kiểm tra JSON/schema.
- `synthetic_generator/validator.py`: validity, fidelity, privacy và utility; utility dùng TSTR hồi quy khi có `target_column`, nếu không sẽ dùng KPI similarity. Đây không phải cam kết differential privacy.
- `dashboard_engine/report_exporter.py`: tạo PDF/XLSX/PPTX và chống CSV/XLSX formula injection.

## Kiểm thử

```powershell
python -m pytest -q
```

Các phần cần hạ tầng ngoài để kiểm thử tích hợp hoàn chỉnh: API key LLM, server Llama và gói SDV/model training. Unit/API test mặc định không gọi dịch vụ ngoài.
