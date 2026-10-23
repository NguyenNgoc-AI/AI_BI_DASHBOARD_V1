# 📦 TÀI LIỆU BÀN GIAO DỮ LIỆU & BENCHMARK MANIFEST
## Dự án: AI BI Dashboard (Code Candy)
**Ngày bàn giao:** 07/10/2026  
**Phân loại nhiệm vụ:** Task 3 - Master Todolist

---

## 1. TỔNG QUAN PHÂN BỔ DỮ LIỆU (DATASET ALLOCATION)

Để đảm bảo quy trình phát triển song song (Parallel Development) giữa nhóm **Data/AI Engine** và nhóm **Backend/API/Dashboard**, dữ liệu được phân chia thành 3 tập độc lập với vai trò cụ thể:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            TỔNG THỂ DỮ LIỆU DỰ ÁN                             │
├──────────────────────────────┬───────────────────────────────────────────────┤
│    DỮ LIỆU THỰC (REAL DATA)   │      DỮ LIỆU TỔNG HỢP (SYNTHETIC DATA)        │
│         (50,000 dòng)        │                 (50,000 dòng)                 │
├──────────────┬───────────────┼───────────────────────────────────────────────┤
│  Benchmark   │  Holdout Test │               Gold Mock Data                  │
│  Seed Data   │     Set       │           (Bàn giao cho Backend)              │
│ (35,000 dòng)│ (15,000 dòng) │                (50,000 dòng)                  │
└──────────────┴───────────────┴───────────────────────────────────────────────┘
```

| Tên tập dữ liệu | Đường dẫn tệp | Số lượng dòng | Số lượng cột | Vai trò & Mục đích sử dụng | Trạng thái |
|---|---|:---:|:---:|---|:---:|
| **Gold Mock Data** | `data/generated/synthetic_ecommerce.csv` | **50,000** | **38** | **Bàn giao cho Backend**: Dùng làm nguồn dữ liệu mẫu để xây dựng và test API Ingestion (Task 10), KPI Calculator (Task 11), Chart Generator (Task 11) và Report Exporter (Task 12). | 🟢 **ĐÃ BÀN GIAO** |
| **Benchmark Seed Data** | `data/sample_dataset/ecommerce_seed.csv` | **35,000** | **38** | **Tập mồi chuẩn**: Dùng cho Profiler (Task 4), Schema Extractor (Task 5) và huấn luyện Generator Engine (Task 6). | 🟢 **CHUẨN HÓA** |
| **Real Holdout Set** | `data/warehouse/real_holdout.csv` | **15,000** | **38** | **Tập kiểm thử độc lập (Cách ly)**: Dùng để đánh giá Utility Score (TSTR) ở Task 7 và nghiệm thu độc lập ở Task 23. Không được dùng để huấn luyện. | 🔒 **ĐÃ KHÓA** |

---

## 2. CẤU TRÚC LƯỢC ĐỒ CHUẨN (38 THUỘC TÍNH ĐỒNG BỘ)

Tất cả 3 tệp dữ liệu đều tuân thủ chính xác $100\%$ cấu trúc 38 cột đại diện cho 5 thực thể cốt lõi:

### 🔹 Khách hàng (`customers`)
1. `customer_id`: Mã định danh duy nhất của khách hàng (VD: `CUST_00000001`).
2. `customer_segment`: Phân khúc khách hàng (`Consumer`, `Corporate`, `Home Office`, `VIP`, `Wholesale`).
3. `city`: Thành phố sinh sống / nhận hàng.
4. `state`: Bang / Tỉnh thành.
5. `country`: Quốc gia.
6. `zip_code`: Mã bưu chính.

### 🔹 Sản phẩm (`products`)
7. `product_id`: Mã SKU sản phẩm (VD: `PROD_ELEC_0001`).
8. `category`: Danh mục cấp cao (10 danh mục: `Electronics`, `Computers & Accessories`, `Home & Kitchen`, v.v.).
9. `sub_category`: Phân nhóm sản phẩm chi tiết.
10. `unit_price`: Đơn giá bán lẻ niêm yết (USD).
11. `unit_cost`: Đơn vị giá vốn hàng bán (COGS) (USD).
12. `margin_rate`: Tỷ suất lợi nhuận định mức `(unit_price - unit_cost) / unit_price`.

### 🔹 Bán hàng & Dòng đơn (`sales`)
13. `sales_id`: Mã định danh chi tiết bán hàng (VD: `SALE_00000001`).
14. `quantity`: Số lượng mua ($quantity \ge 1$).
15. `gross_sales`: Doanh số gộp `$gross\_sales = quantity \times unit\_price$`.
16. `discount_amount`: Tiền giảm giá/khuyến mãi (`$0 \le discount\_amount \le gross\_sales$`).
17. `net_sales`: Doanh số thuần `$net\_sales = gross\_sales - discount\_amount$`.
18. `cogs`: Tổng giá vốn sản phẩm `$cogs = quantity \times unit\_cost$`.
19. `gross_profit`: Lợi nhuận gộp dòng `$gross\_profit = net\_sales - cogs$`.
20. `gross_margin_pct`: Tỷ suất lợi nhuận gộp (`%`).
21. `freight_value`: Cước phí vận chuyển.
22. `platform_fee`: Phí hoa hồng/giao dịch sàn thương mại điện tử.

### 🔹 Đơn hàng (`orders`)
23. `order_id`: Mã đơn hàng (VD: `ORD_2023_00000001`).
24. `order_status`: Trạng thái đơn (`delivered`, `shipped`, `processing`, `canceled`, `invoiced`, v.v.).
25. `order_purchase_timestamp`: Thời điểm đặt hàng.
26. `order_approved_at`: Thời điểm xác nhận thanh toán.
27. `order_delivered_carrier_date`: Thời điểm giao hàng cho đơn vị vận chuyển.
28. `order_delivered_customer_date`: Thời điểm giao thành công tới khách hàng.
29. `order_estimated_delivery_date`: Ngày dự kiến giao hàng.
30. `payment_type`: Hình thức thanh toán (`credit_card`, `boleto`, `voucher`, `e_wallet`, v.v.).
31. `payment_installments`: Số kỳ trả góp ($1$ nếu trả thẳng).
32. `payment_value`: Tổng giá trị thanh toán đơn hàng.

### 🔹 Tài chính & Tiếp thị (`financials`)
33. `marketing_channel`: Kênh tiếp thị/quảng cáo (`Facebook Ads`, `Google Ads`, `TikTok Ads`, `Organic Search`, v.v.).
34. `marketing_spend`: Chi phí quảng cáo phân bổ cho giao dịch.
35. `tax_amount`: Tiền thuế VAT/thu nhập doanh nghiệp.
36. `operating_expenses`: Chi phí vận hành phân bổ (OPEX).
37. `net_profit`: Lợi nhuận ròng cuối cùng (`Net Profit = net_sales - cogs - marketing_spend - platform_fee - freight_value - tax_amount - operating_expenses`).
38. `net_margin_pct`: Tỷ suất lợi nhuận ròng (`%`).

---

## 3. HƯỚNG DẪN TÍCH HỢP CHO BACKEND TEAM

```python
import pandas as pd

# 1. Đọc dữ liệu Mock Data phục vụ phát triển Dashboard & API
mock_df = pd.read_csv("data/generated/synthetic_ecommerce.csv")
print(f"Loaded {len(mock_df)} records for Dashboard Engine.")

# 2. Ví dụ: Tính toán Top KPIs ngay trên Mock Data
total_gmv = (mock_df["gross_sales"] + mock_df["freight_value"]).sum()
total_net_revenue = mock_df["net_sales"].sum()
total_net_profit = mock_df["net_profit"].sum()
net_margin_overall = (total_net_profit / total_net_revenue) * 100

print(f"GMV: ${total_gmv:,.2f}")
print(f"Net Revenue: ${total_net_revenue:,.2f}")
print(f"Net Profit: ${total_net_profit:,.2f} ({net_margin_overall:.2f}%)")
```

---

## 4. XÁC NHẬN CHẤT LƯỢNG & BÀN GIAO (ACCEPTANCE SIGNOFF)
- [x] **Tính toàn vẹn dữ liệu:** Toàn bộ 50,000 dòng dữ liệu `synthetic_ecommerce.csv` đạt $100\%$ tính hợp lệ đối với Hard Constraints toán học (`HR_SALES_001`, `HR_SALES_002`, `HR_SALES_003`, `HR_FIN_001`).
- [x] **Phân tách Holdout Test:** Tập 15,000 dòng `real_holdout.csv` đã được cách ly độc lập, không rò rỉ dữ liệu sang tập Seed Data.
- [x] **Sẵn sàng bàn giao:** Đội ngũ Backend có thể bắt đầu triển khai Task 8 đến Task 12 ngay lập tức.

