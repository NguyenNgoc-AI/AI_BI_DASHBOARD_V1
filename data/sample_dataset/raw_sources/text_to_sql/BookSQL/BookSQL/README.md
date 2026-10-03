Thư mục chứa Cơ sở dữ liệu BookSQL - cơ sở dữ liệu kế toán (accounting.sqlite), train.json và val.json

* accounting.sqlite
1. master_txn_table - Đây là bảng chính chứa tất cả các bản ghi giao dịch đã diễn ra trong các doanh nghiệp.
2. chart_of_accounts - Bảng này bao gồm tất cả tên các tài khoản và loại tài khoản của các doanh nghiệp.
3. products_service - Bảng này bao gồm tất cả các sản phẩm/dịch vụ và loại của chúng được các doanh nghiệp sử dụng.
4. customers - Bảng này chứa bản ghi của tất cả khách hàng cùng với các chi tiết của họ như tên, địa chỉ thanh toán và giao hàng, v.v., liên kết với các doanh nghiệp.
5. vendors - Bảng này chứa bản ghi của tất cả nhà cung cấp và các chi tiết của họ như tên, địa chỉ thanh toán và giao hàng, v.v., liên kết với các doanh nghiệp.
6. payment_method - Bảng này chứa các phương thức thanh toán được sử dụng bởi các doanh nghiệp.
7. employees - Bảng này chứa chi tiết về nhân viên như tên, mã nhân viên, ngày tuyển dụng, v.v., làm việc tại một doanh nghiệp cụ thể.


* train.json
* Mẫu huấn luyện (Training Samples) - 70828


* val.json
* Mẫu kiểm định (Validation Samples) - 7605


* test.json
* Mẫu kiểm thử (Testing Samples) - 21567


* README.md

Định dạng của tệp train/val/test.json
Ví dụ -

```
{
    "Query":"What was the first invoice for Matthew James?",
    "SQL":"select transaction_id from master_txn_table where customers = \"Matthew James\" and transaction_type = 'invoice' order by transaction_date limit 1",
    "Levels":"medium",
    "split":"test"
}

Query - Truy vấn bằng ngôn ngữ tự nhiên của người dùng
SQL - Câu lệnh SQL chuẩn (GOLD SQL)
Levels - Tất cả các truy vấn được chia thành 3 cấp độ dựa trên độ phức tạp của câu lệnh SQL. 
split - Phân chia dữ liệu (test/train/val)

```