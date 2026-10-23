# Bộ dữ liệu kiểm thử AI BI Dashboard

Dữ liệu hoàn toàn giả lập, gồm 30 đơn hàng, 10 khách hàng, 3 sản phẩm.
Ngày 01–30/10/2026 là khoảng thời gian giả định (có ngày tương lai so với lúc tạo).
Mỗi dòng là một đơn một sản phẩm. Đơn vị tiền: VND.
CSV và JSON chứa cùng dữ liệu: upload một trong hai, không gộp hai file.

## Cách test
1. Đăng nhập Frontend, vào Dữ liệu, chọn sales_test.csv, nhấn tải lên và phân tích.
2. Kiểm tra 30 dòng, 30 order_id khác nhau, không có ô thiếu.
3. Sang Tổng quan, đối chiếu các chỉ số bên dưới.
4. Sang Báo cáo, lọc sản phẩm Tai nghe: 10 đơn, doanh thu 5.000.000, chi phí 3.000.000, lợi nhuận 2.000.000.
5. Bỏ lọc sản phẩm, lọc 01–03/10/2026 (bao gồm hai đầu): 3 đơn, doanh thu 1.600.000, chi phí 980.000, lợi nhuận 620.000.
6. Xuất báo cáo rồi đối chiếu số liệu với bộ lọc đang dùng.
7. Upload sales_test.json thay thế CSV: KPI toàn bộ phải giống nhau.
8. Hỏi chatbot "Tổng doanh thu là bao nhiêu?" khi không lọc: đối chiếu 16.000.000.
9. Với manager/admin, thử bootstrap, count=50, seed=42: kiểm tra trả 50 dòng. Không kỳ vọng KPI tổng của dữ liệu sinh bằng dữ liệu gốc.

## Kết quả mong đợi khi không lọc
- Doanh thu: 16.000.000
- Chi phí: 9.800.000
- Lợi nhuận theo công thức hiện tại revenue - cost: 6.200.000
- Số đơn: 30
- AOV: 533.333,333333... (giao diện có thể làm tròn)
- Chi phí quảng cáo: 1.500.000
- Khách hàng mới: 10 (chỉ đánh dấu lần mua đầu tiên của từng khách)
- CAC: 150.000
- ROAS: 10,666666...
- LTV theo công thức đơn giản hiện tại: 1.600.000
- Doanh thu theo sản phẩm: Ban phim 8.000.000; Tai nghe 5.000.000; Chuot 3.000.000.

Chi phí quảng cáo được phân bổ mỗi đơn một lần. cost là chi phí dùng trực tiếp trong công thức lợi nhuận của ứng dụng; không trừ ad_spend thêm một lần khi đối chiếu.
LTV là doanh thu / khách hàng duy nhất, không phải dự báo vòng đời.
Không dùng dữ liệu nhỏ, lặp lại này để kết luận về chất lượng mô hình AI hoặc bảo đảm privacy.
