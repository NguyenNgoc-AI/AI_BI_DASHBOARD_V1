# Ví dụ EDA Olist sau đồng bộ

## Môi trường
- Source chạy thực tế: D:\AI_BI\AI_BI_DASHBOARD_V1.
- Backend QA: http://127.0.0.1:8001. Frontend: http://localhost:5173.
- Database QA riêng, không đổi tài khoản/database thật.
- 7 file đồng bộ ban đầu được kiểm tra hash; Frontend bổ sung hướng dẫn upload tổng quát và hiển thị warnings.

## Thao tác đã làm
1. Đối chiếu 5 file đã có với bản nền Git để tránh đè thay đổi riêng.
2. Đồng bộ code, tài liệu và test; chạy pytest trong thư mục chính: 36 PASS.
3. Khởi động Backend QA từ thư mục chính.
4. Mở Frontend, dùng kết nối 8001, đăng nhập QA, vào Dữ liệu.
5. Thử file picker hai lần với file Olist: ô file vẫn rỗng. Chưa xác nhận upload qua UI.
6. Gửi chính file đầy đủ qua HTTP bằng Invoke-RestMethod -InFile, Content-Type application/octet-stream và Bearer token từ đăng nhập QA.
7. Endpoint: POST /datasets/analyze?filename=olist_customers_dataset.csv.
8. Đối chiếu độc lập bằng csv.DictReader và tập mã khách, không thay đổi file nguồn.

## Đầu vào và kết quả
File D:\Data_testing\Olist\olist_customers_dataset.csv, 9.033.957 byte.
99.441 dòng, 5 cột. customer_id: 99.441 giá trị duy nhất;
customer_unique_id: 96.096; city: 4.119; state: 27; zip prefix: 14.994.
Không null; không trùng toàn dòng. Các cột đều là string.
capabilities.eda=true; ecommerce_kpis=false; kpis=null; charts=[].
Cảnh báo thiếu cost/date/order_id/product/revenue chỉ giải thích vì sao không tính KPI.
Không có lỗi từ chối upload vì thiếu schema bán hàng.

## Cách tự thử
Khởi động lại Backend từ thư mục chính sau đồng bộ (server cũ không tự nạp code nếu không dùng --reload).
Frontend -> Cài đặt kết nối -> URL của Backend đang chạy -> đăng nhập -> Dữ liệu -> chọn file -> Tải lên & phân tích.
Mở Schema & thống kê: xem Profiling và Chi tiết chất lượng.
Server demo dùng cổng 8001; khi chạy server riêng ở 8000, cần đổi lại kết nối Frontend.

## Giới hạn
Chưa kiểm chứng browser upload end-to-end vì file picker không nhận file.
Các file Olist lớn hơn 10 MiB vẫn bị chặn. Chưa ghép bảng, Excel, lưu dataset hoặc AI mapping.
Không suy ra doanh thu/lợi nhuận từ bảng khách hàng. Không suy diễn quality=1 là dữ liệu đúng nghiệp vụ.
Ảnh báo cáo là trang trình bày response API thực tế, không phải ảnh chụp Frontend đã upload thành công.
