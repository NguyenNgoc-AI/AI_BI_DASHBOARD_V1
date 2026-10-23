# Nhập dữ liệu tổng quát — bước 1

POST /datasets/analyze nhận raw UTF-8 CSV/JSON và query filename như trước.
Không còn bắt buộc năm cột bán hàng để chạy EDA. Cần JWT của tài khoản ACTIVE.

Response giữ dataset, schema, profile, quality, kpis, charts; bổ sung capabilities và warnings.
- Bảng bán hàng hợp lệ: KPI/biểu đồ giữ hành vi cũ.
- Bảng khác hoặc dữ liệu nghiệp vụ không hợp lệ: EDA vẫn trả về; kpis=null,
  charts=[], capabilities.ecommerce_kpis=false, warnings giải thích lý do.
- Thiếu dữ liệu không được thay bằng KPI bằng 0.

POST /datasets/profile, /datasets/quality, /datasets/schema nhận bảng tổng quát.
Các API dashboard, chat, export và synthetic vẫn cần schema bán hàng ở bước này.
Frontend chưa có dashboard tổng quát; chỉ bổ sung guard tránh crash khi kpis=null.

## Quy tắc
- CSV phân cách dấu phẩy; JSON là danh sách object phẳng hoặc {"data": [...]}.
- UTF-8, tối đa 100 cột cho cả hai dạng; giới hạn upload mặc định 10 MiB,
  số dòng theo MAX_ROWS (mặc định 100.000).
- Chặn tên cột rỗng/trùng sau chuẩn hóa, JSON trùng khóa, cấu trúc lồng,
  số không hữu hạn, CSV thừa/thiếu ô. Không âm thầm bỏ dòng lỗi.
- Tên cột chuẩn hóa như trước; chưa dịch tên cột tiếng Việt hoặc map nghiệp vụ.
- Key thiếu/chuỗi rỗng thành null trong bản phân tích. Không ghi đè file gốc.
- Chỉ chuyển chuỗi số đơn giản khi toàn bộ giá trị có dữ liệu của cột phù hợp.
  Giữ chuỗi có số 0 đầu và cột chứa thành phần id/code/zip/phone.
  Đây là suy luận kiểu, chưa phải xác nhận ngữ nghĩa; mã số không có dấu hiệu
  định danh vẫn có thể được suy luận là số.
- Bảng không có order_id kiểm tra trùng toàn dòng; bảng có order_id vẫn báo trùng mã đơn.
- Điểm quality/valid chưa có quy tắc nghiệp vụ tùy chỉnh, không phải chứng nhận dữ liệu đúng.
- Nghiệp vụ bán hàng kiểm tra null trước khi ép chuỗi, chặn boolean ở cột số,
  số âm ở quantity/ad_spend/new_customers và số lẻ ở quantity/new_customers.

## Chưa thuộc bước này
Excel, nhận diện encoding/delimiter, chuẩn hóa ngày tổng quát, ánh xạ AI,
ghép nhiều bảng, lưu dataset, xử lý nền, tải lớn, xác nhận làm sạch qua UI.
Không tự suy ra giá vốn từ phí vận chuyển hoặc tạo doanh thu cho bảng khách hàng.
File Olist vượt giới hạn vẫn bị từ chối; không tuyên bố hỗ trợ cả bộ nguyên vẹn.

## Kiểm thử
python -m pytest tests -q
Đã chạy 36 test PASS trên database test riêng, gồm hồi quy và test mới cho
generic upload/EDA, giới hạn, null, boolean, số âm, CSV sai và JSON trùng khóa.
Chưa kiểm thử end-to-end trên browser hoặc tải lớn.
