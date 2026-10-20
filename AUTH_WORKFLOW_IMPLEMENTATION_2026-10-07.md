# Báo cáo chỉnh sửa Login và Register

Ngày thực hiện: 07/10/2026
Phạm vi: Backend AI BI Dashboard

## 1. Kết luận

Luồng đăng ký trực tiếp bằng `username/password` đã được thay bằng quy trình có phê duyệt:

1. Nhân viên gửi yêu cầu bằng mã nhân viên và thông tin công việc.
2. Admin xem, phê duyệt hoặc từ chối yêu cầu.
3. Admin cấp tài khoản với mật khẩu tạm, role, permissions và data scope.
4. Lần đăng nhập đầu tiên chỉ trả về activation token.
5. Nhân viên đổi mật khẩu để kích hoạt tài khoản.
6. Sau khi kích hoạt, đăng nhập lại mới nhận access token để dùng API riêng tư.

Endpoint `/auth/register` được giữ làm alias tương thích nhưng chỉ nhận dữ liệu yêu cầu đăng ký mới. Payload cũ chứa `username/password` bị từ chối với HTTP 422.

## 2. API đã triển khai

| API | Ai được gọi | Công việc |
|---|---|---|
| `POST /auth/register-request` | Public | Tạo yêu cầu đăng ký `PENDING` |
| `POST /auth/register` | Public | Alias cũ của register-request |
| `GET /admin/registration-requests` | Admin | Liệt kê, lọc theo trạng thái |
| `GET /admin/registration-requests/{id}` | Admin | Xem chi tiết yêu cầu |
| `POST /admin/registration-requests/{id}/approve` | Admin | Xác minh nhân viên và duyệt |
| `POST /admin/registration-requests/{id}/reject` | Admin | Từ chối; bắt buộc có lý do |
| `POST /admin/users/provision` | Admin | Cấp tài khoản `PENDING_ACTIVATION` |
| `POST /auth/login` | Public | Trả activation token hoặc access token theo trạng thái |
| `POST /auth/activate` | Activation token | Đổi mật khẩu và kích hoạt |
| `GET /auth/me` | Access token | Trả hồ sơ quyền hiện tại |

## 3. Database và migration

Migration chạy cộng dồn, không xóa tài khoản cũ. Tài khoản cũ được giữ ở trạng thái `ACTIVE`.

Các bảng mới:

- `employees`: hồ sơ nhân viên đã được admin xác minh.
- `registration_requests`: yêu cầu và kết quả xét duyệt.
- `audit_logs`: lưu hành động duyệt, từ chối và cấp tài khoản.

Các cột bổ sung vào `users`:

- `employee_id`
- `status`
- `permissions_json`
- `data_scope`
- `registration_request_id`
- `token_version`
- `activated_at`

Các unique index ngăn hai yêu cầu `PENDING` cho cùng nhân viên và ngăn cấp tài khoản hai lần từ cùng yêu cầu.

## 4. Quy tắc bảo mật chính

- Mật khẩu dùng PBKDF2-SHA256 với salt riêng và 310.000 vòng.
- Token có mục đích rõ ràng: `typ=activation` hoặc `typ=access`.
- Activation token sống 10 phút và không truy cập được API riêng tư.
- Access token mặc định sống 60 phút.
- Mỗi request riêng tư đọc lại user trong database, kiểm tra `ACTIVE` và `token_version`.
- Đổi role hoặc kích hoạt làm tăng `token_version`, khiến token cũ mất hiệu lực.
- Tài khoản `DISABLED` bị HTTP 403 dù nhập đúng mật khẩu.
- Sai username hoặc password đều trả cùng một HTTP 401 để hạn chế dò tài khoản.
- Phê duyệt/từ chối dùng conditional update; request đã xử lý trả HTTP 409.
- Cấp tài khoản chạy trong transaction `BEGIN IMMEDIATE`; lỗi sẽ rollback toàn bộ.
- Role, permission và data scope được kiểm tra theo allowlist cố định.

## 5. Dữ liệu nhập trong case luồng đầy đủ

### Bước 1 — Gửi yêu cầu

```json
{
  "employee_id": "emp-2026",
  "full_name": "Nguyen Van An",
  "position": "Data Analyst",
  "department": "Finance"
}
```

Kết quả mong đợi: HTTP 201, mã nhân viên được chuẩn hóa thành `EMP-2026`, trạng thái `PENDING`.

### Bước 2 — Admin duyệt

Admin đăng nhập, lấy Bearer access token, sau đó gọi:

```text
POST /admin/registration-requests/{request_id}/approve
Body: {}
```

Kết quả mong đợi: HTTP 200, trạng thái `APPROVED`. Gọi lại lần hai trả HTTP 409.

### Bước 3 — Admin cấp tài khoản

```json
{
  "registration_request_id": 1,
  "temporary_password": "Temporary-password-2026",
  "role": "user",
  "permissions": ["dashboard:view", "dataset:view", "kpi:view"],
  "data_scope": "own"
}
```

Kết quả mong đợi: HTTP 201, username bằng mã nhân viên, trạng thái `PENDING_ACTIVATION`. Gọi lại lần hai trả HTTP 409.

### Bước 4 — Đăng nhập lần đầu

```json
{
  "username": "EMP-2026",
  "password": "Temporary-password-2026"
}
```

Kết quả mong đợi: HTTP 200, `purpose=activation`, thời hạn 600 giây. Token này gọi `/auth/me` phải nhận HTTP 401.

### Bước 5 — Kích hoạt

Header: `Authorization: Bearer <activation_token>`

```json
{
  "new_password": "New-password-2026",
  "confirm_password": "New-password-2026"
}
```

Kết quả mong đợi: HTTP 204. Activation token không thể dùng lại và mật khẩu tạm không thể đăng nhập lại.

### Bước 6 — Đăng nhập chính thức

Đăng nhập bằng mật khẩu mới trả `purpose=access`. Access token gọi `/auth/me` trả trạng thái `ACTIVE`, permissions và data scope.

## 6. Case từ chối

Payload từ chối:

```json
{
  "rejection_reason": "Employee record could not be verified"
}
```

Không truyền lý do trả HTTP 400. Có lý do hợp lệ trả HTTP 200 và trạng thái `REJECTED`.

## 7. Kết quả test

Lệnh chạy tại dự án thật:

```powershell
.\.venv\Scripts\python.exe -u -m unittest discover -s tests -v
```

Kết quả: **17/17 test PASS** trong 4,690 giây.

Các nhóm đã kiểm tra:

- Public auth guard, CORS và OpenAPI.
- Đăng ký, đăng ký trùng và payload đăng ký cũ.
- Quyền admin cho danh sách, duyệt, từ chối và provision.
- Duyệt hai lần và provision hai lần.
- Activation token khác access token.
- Sai xác nhận mật khẩu.
- Vô hiệu mật khẩu tạm sau kích hoạt.
- User, manager và admin trên các API riêng tư hiện có.
- RBAC của synthetic và quản lý role.
- Toàn bộ analytics, schema, chat và report export.
- Hash mật khẩu, chữ ký JWT và token hết hạn.
- Validation đầu vào và ẩn lỗi nội bộ.

## 8. Giới hạn đã ghi nhận

`data_scope` và `permissions` đã được lưu, trả về và kiểm tra khi provision. Các API phân tích hiện nhận dữ liệu trực tiếp trong request, chưa có bảng dataset/resource lưu `owner_id` hoặc `department`, nên chưa thể áp dụng Resource Ownership thực sự mà không thiết kế thêm lớp lưu trữ dataset. Không có kiểm tra giả tạo dựa trên dữ liệu client gửi lên.

Các phần chưa triển khai theo phạm vi đã thống nhất: refresh token, logout/revocation list, MFA, OAuth/SSO, email và đồng bộ HR.
