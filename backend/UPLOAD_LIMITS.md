# Giới hạn upload và giải thích quan hệ

Mức mặc định mới: MAX_UPLOAD_BYTES=104857600 (100 MiB), MAX_ROWS=200000.
Frontend: mỗi file phân tích tối đa 100 MiB; nhóm 2–10 file quan hệ có tổng
dung lượng tối đa 100 MiB. JSON request sau chuyển đổi cũng không được vượt 100 MiB.
Mỗi bảng tối đa 200.000 dòng và 100 cột. Sinh dữ liệu synthetic vẫn tối đa 100.000 dòng.

Nếu đã đặt MAX_UPLOAD_BYTES hoặc MAX_ROWS trong môi trường, giá trị đó ghi đè mặc định.
Frontend hiện dùng mức mặc định cố định; chưa tự đọc cấu hình server.
Backend không tự nạp .env. Khởi động lại server để áp dụng config mới.

Đây là giới hạn chấp nhận, không phải bảo đảm hiệu năng: trình duyệt và Backend
vẫn đọc vào RAM, chưa có streaming/background job; file lớn có thể chậm hoặc hết thời gian chờ.
Geolocation Olist hơn 200.000 dòng vẫn cần chia file hoặc bổ sung xử lý nền sau này.

Kết quả quan hệ dùng câu tiếng Việt và đếm mã lặp ở bảng con để diễn giải
một–một hoặc nhiều–một trong dữ liệu hiện có. Dòng thiếu mã được báo riêng.
Các tên Olist thông dụng có nhãn tiếng Việt; tên khác giữ nguyên tên bảng người dùng.
Chi tiết cột và JSON nằm trong phần mở rộng. Không yêu cầu nhập JSON.
Suy luận vẫn cần cột cùng tên, khóa cha duy nhất và đủ mã tham chiếu;
không tìm thấy không có nghĩa hai bảng không liên quan. Không tự ghép bảng.

Kiểm thử: 37 test Backend, 10 test Frontend PASS; có request >10 MiB và chặn vượt mức.
Chưa benchmark file 100 MiB hoặc kiểm thử đa người dùng.
