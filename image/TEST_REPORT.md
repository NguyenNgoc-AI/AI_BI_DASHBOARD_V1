# Báo cáo kiểm thử Frontend — 19/10/2026

## Môi trường và phạm vi

- Frontend: http://localhost:5173, static ES modules; backend QA: http://127.0.0.1:8001.
- Database QA riêng `.test-temp/frontend-20261019.db`; không dùng dữ liệu tài khoản thật.
- Tài khoản admin kiểm thử: `frontend_test_admin`. Mật khẩu QA không ghi vào source.
- Backend Python trong sandbox không khởi động; đã chạy server QA ngoài sandbox và kiểm tra thành công.
- Kết quả dưới đây phân biệt browser, adapter tích hợp và unit. Không tuyên bố toàn bộ sản phẩm đã nghiệm thu.

## Unit: 7/7 PASS

Lệnh `node --test Frontend/tests/core.test.mjs`.

| Case | Input / thao tác | Kết quả |
|---|---|---|
| CORE-01 | CSV có BOM, comma trong quotes, newline trong quotes, escaped quote | Parse đúng 2 record, giữ nội dung |
| CORE-02 | JSON data-envelope; empty array; nested object; header trùng; CSV thiếu cột/quote | Chấp nhận envelope; từ chối dữ liệu cấu trúc sai |
| CORE-03 | Chuỗi HTML/script, dấu quote, ampersand | Escape đúng trước khi render |
| CORE-04 | Lọc 2 dòng theo ngày biên | Giữ đúng dòng; không sửa dataset gốc |
| CORE-05 | 100.000 giá trị doanh thu = 3 | Chart tối đa 60 điểm; tổng vẫn 300.000 |
| CORE-06 | user/manager/null và Pydantic detail | Guard đúng; lỗi chứa field/message |
| CORE-07 | Mock fetch JSON/raw/Blob/403/204 | Đúng header, body, token; 403 giữ status; 204 trả null |

## Tích hợp qua API client thật: PASS

Script: `Frontend/tests/live-api.mjs`. Chạy trên backend QA, credentials truyền qua environment.

| Case | Input / hành động | Kết quả assert |
|---|---|---|
| API-01 | Login admin và GET /auth/me | role admin |
| API-02 | Upload raw CSV 2 dòng revenue 100/200, cost 60/80 | revenue 300; net_profit 160 |
| API-03 | Export json/csv/html/pdf/xlsx/pptx cùng dataset | Blob không rỗng; PDF bắt đầu %PDF, XLSX/PPTX bắt đầu PK |
| API-04 | Hỏi “Tổng doanh thu?” ở chat/query và chat/sql | Có answer; SQL chứa SELECT |
| API-05 | Bootstrap count=8, seed=42 trên 24 dòng mẫu | Trả 8 dòng |
| API-06 | register-request → approve → provision user/own | Request PENDING, provision thành công |
| API-07 | Login mật khẩu tạm, gọi /auth/me | purpose activation; /auth/me trả 401 |
| API-08 | Activate mật khẩu mới rồi login | purpose access |
| API-09 | User token gọi admin list và synthetic | 403 ở cả hai endpoint |

API-03 kiểm tra định dạng, chưa phải so sánh toàn bộ nội dung/layout mỗi report.

## Browser đã thực hiện

| Case | Thao tác, dữ liệu nhập | Kết quả quan sát |
|---|---|---|
| UI-01 | Cài đặt kết nối → nhập http://127.0.0.1:8001 → Lưu | Quay về login; yêu cầu đăng nhập lại |
| UI-02 | Login frontend_test_admin bằng mật khẩu QA | Vào dashboard rỗng; thấy role admin/ACTIVE |
| UI-03 | Nhấn Dùng dữ liệu mẫu | 24 dòng qua API; doanh thu 40.548.000đ, lợi nhuận 21.744.000đ, AOV 1.689.500đ; nhãn Dữ liệu mẫu |
| UI-04 | Báo cáo → sản phẩm Tai nghe Air → Áp dụng | Doanh thu 12.932.000đ |
| UI-05 | Nhấn PDF trên báo cáo đã lọc | Download report.pdf thành công, lịch sử phiên cập nhật |
| UI-06 | Chat → nhập “Tổng doanh thu là bao nhiêu?” → Gửi | Trả 12.932.000, chi phí 6.036.000, lợi nhuận 6.896.000; nguồn deterministic |
| UI-07 | Synthetic → bootstrap, count=8, seed=42 → Sinh | Hiện validity/fidelity/privacy/utility, có nút tải JSON |
| UI-08 | Logout → đăng ký employee_id=FE_UI_1019, name=Frontend UI Test, position=Tester, department=QA | Hiện “Đã gửi yêu cầu!”, chưa vào dashboard |
| UI-09 | Login admin với wrong-password | Hiện alert Invalid username or password, vẫn ở login |
| UI-10 | Login đúng → tìm trang “Quản trị” → Tải yêu cầu | Thấy FE_UI_1019 trạng thái PENDING |
| UI-11 | Từ chối FE_UI_1019 → nhập “Yêu cầu QA kiểm tra nhánh từ chối” → xác nhận | REJECTED, nút duyệt không còn |
| UI-12 | Data → chọn tests/valid.csv bằng file picker → Tải lên & phân tích | Bảng 2 dòng Bag/Pen; schema/profiling/quality xuất hiện |
| UI-13 | Chọn tests/invalid.json (date=bad date, revenue=-1) → upload | Hiện lỗi date từ backend; bảng CSV cũ vẫn còn |
| UI-14 | Chọn tests/valid.json → upload | Thấy JSON product, revenue 500, cost 100 |
| UI-15 | Reload sau phiên đã login và có dataset | Quay về login, token/dataset không khôi phục |
| UI-16 | Màn hình 375px, 768px, 1440px; kiểm tra Data | Sau sửa grid min-width: scrollWidth lần lượt 360/753/1425, không vượt viewport |
| UI-17 | Màn hình 375px login và loaded dashboard | Login scrollWidth=375; dashboard=360; navigation qua nút menu/tìm trang |

## Lỗi đã sửa trong quá trình test

1. `prompt()` không được hỗ trợ trong in-app browser: thay bằng form inline cho kết nối và reject.
2. Nút hành động nằm trong form có thể submit ngầm: helper button dùng type=button.
3. Cache static file giữ app cũ: server dev dùng Cache-Control no-store.
4. Grid chứa bảng làm tràn mobile (388 > 375px): thêm min-width:0 và minmax(0,1fr).
5. Chart có nguy cơ tạo quá nhiều SVG nodes: gộp tối đa 60 khoảng và giữ nguyên tổng doanh thu.

## Review của ChatGPT

Đã gửi thiết kế/contract trước triển khai và gửi bằng chứng sau triển khai. Kết luận reviewer: CONDITIONAL; chưa full acceptance. Reviewer không trực tiếp đọc toàn bộ source. Sau review đã bổ sung UI registration/reject, CSV/JSON file picker/invalid upload và breakpoint375/768/1440.

Không coi việc chưa push là lỗi chức năng; push không thuộc yêu cầu hiện tại.

## Chưa xác minh / giới hạn

- Toàn bộ provision/activation bằng UI và manager/user navigation end-to-end. Vòng đời auth và 401/403 đã pass qua API client; không thay thế browser test.
- Lỗi offline/timeout/422/500/export thất bại qua browser, upload >10MiB và nhiều trình duyệt chưa chạy đầy đủ.
- Chưa so sánh nội dung từng định dạng PDF/XLSX/PPTX sau export với bộ lọc. Chỉ PDF được download qua browser.
- Provider LLM ngoài và huấn luyện SDV chưa chạy; test hiện dùng deterministic/bootstrap.
- Backend thiếu persisted dataset/resource ownership và granular permission enforcement; frontend không khắc phục được giới hạn này.

Đây là bản Frontend MVP để kiểm tra và tiếp tục hoàn thiện, không phải xác nhận production-ready.
