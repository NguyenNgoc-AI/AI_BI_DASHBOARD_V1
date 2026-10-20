# Code Candy Frontend

Giao diện theo UI board của dự án: sidebar trắng, nền xanh tím nhạt, KPI pastel, auth chia hai cột và dashboard có trạng thái chưa/đã tải dữ liệu.

## Chạy

Từ project root, chạy backend trong terminal thứ nhất (thiết lập ADMIN_USERNAME/ADMIN_PASSWORD nếu database mới). Backend đọc biến môi trường, không tự nạp `.env`.

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Terminal thứ hai:

```powershell
python Frontend/serve.py
```

Mở **http://localhost:5173** để khớp CORS mặc định của backend. Frontend không cần npm install/build. Chỉ phục vụ folder Frontend; server không lộ database hoặc file repo.

Nếu backend ở cổng khác, dùng “Cài đặt kết nối” ở màn hình đăng nhập. Địa chỉ API lưu localStorage; JWT và dataset chỉ giữ trong bộ nhớ, mất khi refresh/đăng xuất. Đổi API sẽ yêu cầu đăng nhập lại.

## Luồng sử dụng

1. Nhân viên gửi employee_id, full_name, position, department; chưa được tạo account ngay.
2. Admin đăng nhập → Quản trị tài khoản → Tải yêu cầu → Duyệt/Từ chối.
3. Admin cấp tài khoản với ID request đã duyệt, mật khẩu tạm, role, scope.
4. Nhân viên login bằng mã nhân viên/mật khẩu tạm → đổi mật khẩu → login lại.
5. Dữ liệu → upload CSV/JSON UTF-8, tối đa 10 MiB, có date/order_id/product/revenue/cost.
6. Tổng quan hiển thị kết quả API; Báo cáo lọc ngày/sản phẩm và tải 6 định dạng.
7. Chat dùng dữ liệu hiện tại; SQL chỉ hiển thị SELECT. Manager/admin có thêm synthetic.

Nút dữ liệu mẫu gửi 24 dòng minh họa qua API thật và có nhãn “Dữ liệu mẫu”. Không có cơ chế fallback ngầm khi API lỗi. Preview bảng giới hạn 50 dòng, phân tích vẫn dùng toàn bộ tập sau lọc.

## Kiểm thử

```powershell
node --test Frontend/tests/core.test.mjs
```

`tests/live-api.mjs` chỉ chạy trên backend test với database riêng. Đặt TEST_API_URL và TEST_ADMIN_PASSWORD; bootstrap username `frontend_test_admin`. Script tạo request/tài khoản QA trong database test, không dùng database thật.

## Phạm vi hiện tại

- Nối API: auth, activation, request administration, upload, analytics, schema relations, exports, chat/SQL, synthetic.
- UI dùng permission theo role để ẩn trang; backend vẫn là nơi quyết định quyền. Backend chưa enforce permissions/data scope theo từng resource analytics.
- Chưa có API danh sách nhân viên, persistent dataset, customer CRUD, notifications, subscription, HR, connector Excel/Sheets/SQL, lập lịch báo cáo, reset password. Giao diện không giả lập các chức năng này.
- Synthetic model lớn có thể vượt timeout 120 giây; cần backend job queue nếu triển khai tải lớn.
- Font dùng Segoe UI/system; robot minh họa bằng CSS, không sao chép ảnh mờ từ PDF.

Xem [kế hoạch phase](PHASES.md) và [báo cáo test](TEST_REPORT.md).
