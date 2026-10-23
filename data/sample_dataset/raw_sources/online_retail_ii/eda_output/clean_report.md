
### Báo Cáo Tóm Tắt Quá Trình Làm Sạch Dữ Liệu (Clean Report)

Quá trình làm sạch dữ liệu đã được thực hiện theo các bước sau:

1.  **Tải Dữ Liệu:** Dữ liệu được tải từ file `online_retail_II.xlsx` (sheet mặc định hoặc 'Year 2010-2011' nếu có nhiều sheet).
    *   Kích thước ban đầu của DataFrame: (525461, 8)

2.  **Thay Đổi Tên Cột:** Đã kiểm tra tên cột và xác nhận không cần đổi tên mặc định.

3.  **Xóa Hàng Trùng Lặp:** Các hàng trùng lặp hoàn toàn trong DataFrame đã được loại bỏ.
    *   Số hàng trước khi xóa trùng lặp: 525461
    *   Số hàng sau khi xóa trùng lặp: 518596 (Đã xóa 6865 hàng)

4.  **Xử Lý Thiếu Dữ Liệu:**
    *   Các hàng có giá trị thiếu trong cột 'Customer ID' và 'Description' đã được xóa.
    *   Số hàng sau khi xóa thiếu dữ liệu: 410763 (Đã xóa 107833 hàng)

5.  **Xử Lý Dữ Liệu Không Hợp Lệ:**
    *   Loại bỏ các giao dịch trả lại bằng cách xóa các hàng có 'Invoice' chứa chữ cái.
    *   Loại bỏ các giao dịch có 'Quantity' không hợp lệ (<= 0).
    *   Loại bỏ các giao dịch có 'Price' không hợp lệ (<= 0).
    *   Số hàng sau khi loại bỏ dữ liệu không hợp lệ: 400916 (Đã xóa 9847 hàng)

6.  **Chuyển Đổi Kiểu Dữ Liệu:**
    *   Cột `InvoiceDate` đã được chuyển đổi sang kiểu `datetime`.
    *   Cột `Quantity` đã được chuyển đổi sang kiểu `int`.
    *   Cột `Price` đã được chuyển đổi sang kiểu `float`.
    *   Cột `Customer ID` đã được chuyển đổi sang kiểu `int`.

7.  **Tạo Các Cột Mới:**
    *   Cột `Amount` được tính bằng `Quantity * Price`.
    *   Các cột thời gian như `Year`, `Month`, `Day`, `Hour`, `DayOfWeek`, `MonthYear` đã được tạo từ cột `InvoiceDate`.

8.  **Lưu Trữ Dữ Liệu Đã Làm Sạch:**
    *   DataFrame đã làm sạch (`df_cleaned`) được lưu vào file `cleaned_online_retail.csv`.
