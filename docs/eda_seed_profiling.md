# BÁO CÁO PHÂN TÍCH PHÂN PHỐI DỮ LIỆU (DATA PROFILING REPORT)

> **Tập dữ liệu:** `ecommerce_seed.csv`  
> **Thời gian khởi tạo:** `2026-10-04T06:51:34.984526` UTC  
> **Quy mô:** **35,000 dòng** | **38 cột** | **44.51 MB**  
> **Tỷ lệ ô khuyết (Null density):** `0.08%` (1,089 ô)  

---

## I. BẢNG TỔNG QUAN THUỘC TÍNH (COLUMN METRICS)

| STT | Tên cột | Kiểu dữ liệu | Semantic Type | Null % | Số giá trị duy nhất | Min | Max | Mean | Median |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `sales_id` | `str` | `identifier` | 0.0% | 35,000 | - | - | - | - |
| 2 | `order_id` | `str` | `identifier` | 0.0% | 33,312 | - | - | - | - |
| 3 | `customer_id` | `str` | `identifier` | 0.0% | 33,312 | - | - | - | - |
| 4 | `customer_segment` | `str` | `categorical` | 0.0% | 4 | - | - | - | - |
| 5 | `city` | `str` | `text` | 0.0% | 2,835 | - | - | - | - |
| 6 | `state` | `str` | `categorical` | 0.0% | 27 | - | - | - | - |
| 7 | `country` | `str` | `categorical` | 0.0% | 1 | - | - | - | - |
| 8 | `zip_code` | `int64` | `identifier` | 0.0% | 10,920 | 1003.0 | 99990.0 | 35238.6348 | 24450.0 |
| 9 | `product_id` | `str` | `identifier` | 0.0% | 16,211 | - | - | - | - |
| 10 | `category` | `str` | `categorical` | 0.0% | 10 | - | - | - | - |
| 11 | `sub_category` | `str` | `categorical` | 0.0% | 31 | - | - | - | - |
| 12 | `quantity` | `int64` | `boolean` | 0.0% | 1 | 1.0 | 1.0 | 1.0 | 1.0 |
| 13 | `unit_price` | `float64` | `numerical_currency` | 0.0% | 3,625 | 1.2 | 6729.0 | 121.2963 | 74.9 |
| 14 | `unit_cost` | `float64` | `numerical_currency` | 0.0% | 12,369 | 0.4 | 3939.16 | 60.5914 | 36.44 |
| 15 | `margin_rate` | `float64` | `numerical_ratio` | 0.0% | 3,651 | 0.3003 | 0.6999 | 0.4984 | 0.4902 |
| 16 | `gross_sales` | `float64` | `numerical_currency` | 0.0% | 3,625 | 1.2 | 6729.0 | 121.2963 | 74.9 |
| 17 | `discount_amount` | `float64` | `numerical_quantity` | 0.0% | 3,798 | 0.0 | 1136.56 | 5.9965 | 0.0 |
| 18 | `net_sales` | `float64` | `numerical_currency` | 0.0% | 11,447 | 0.98 | 5592.44 | 115.2998 | 69.9 |
| 19 | `cogs` | `float64` | `numerical` | 0.0% | 12,369 | 0.4 | 3939.16 | 60.5914 | 36.44 |
| 20 | `gross_profit` | `float64` | `numerical_currency` | 0.0% | 11,916 | 0.55 | 2372.63 | 54.7083 | 32.88 |
| 21 | `gross_margin_pct` | `float64` | `numerical_ratio` | 0.0% | 4,455 | 14.69 | 70.0 | 46.9473 | 46.74 |
| 22 | `freight_value` | `float64` | `numerical_currency` | 0.0% | 4,724 | 0.0 | 409.68 | 20.0634 | 16.28 |
| 23 | `platform_fee` | `float64` | `numerical_currency` | 0.0% | 4,284 | 0.07 | 651.35 | 10.3786 | 6.22 |
| 24 | `order_status` | `str` | `categorical` | 0.0% | 7 | - | - | - | - |
| 25 | `order_purchase_timestamp` | `str` | `datetime` | 0.0% | 33,252 | - | - | - | - |
| 26 | `order_approved_at` | `str` | `text` | 0.01% | 32,189 | - | - | - | - |
| 27 | `order_delivered_carrier_date` | `str` | `datetime` | 0.99% | 30,322 | - | - | - | - |
| 28 | `order_delivered_customer_date` | `str` | `datetime` | 2.11% | 32,525 | - | - | - | - |
| 29 | `order_estimated_delivery_date` | `str` | `datetime` | 0.0% | 438 | - | - | - | - |
| 30 | `payment_type` | `str` | `categorical` | 0.0% | 4 | - | - | - | - |
| 31 | `payment_installments` | `int64` | `numerical_currency` | 0.0% | 22 | 0.0 | 24.0 | 3.0106 | 2.0 |
| 32 | `payment_value` | `float64` | `numerical_currency` | 0.0% | 16,246 | 10.89 | 13664.08 | 179.5528 | 114.645 |
| 33 | `marketing_channel` | `str` | `categorical` | 0.0% | 6 | - | - | - | - |
| 34 | `marketing_spend` | `float64` | `numerical_currency` | 0.0% | 643 | 0.0 | 8.0 | 3.9666 | 4.33 |
| 35 | `tax_amount` | `float64` | `numerical_currency` | 0.0% | 3,165 | 0.08 | 447.4 | 9.2236 | 5.59 |
| 36 | `operating_expenses` | `float64` | `numerical` | 0.0% | 2,084 | 1.04 | 224.7 | 5.6129 | 3.8 |
| 37 | `net_profit` | `float64` | `numerical_currency` | 0.0% | 8,919 | -36.12 | 1298.81 | 25.5265 | 12.85 |
| 38 | `net_margin_pct` | `float64` | `numerical_ratio` | 0.0% | 6,874 | -650.83 | 50.27 | 14.9354 | 17.21 |

---

## II. TƯƠNG QUAN BIẾN TÀI CHÍNH HÀNG ĐẦU (TOP CORRELATIONS)

| Biến 1 | Biến 2 | Pearson $r$ | Đánh giá tương quan |
|---|---|---|---|
| `unit_price` | `gross_sales` | **1.0** | Strong Positive |
| `unit_cost` | `cogs` | **1.0** | Strong Positive |
| `net_sales` | `tax_amount` | **1.0** | Strong Positive |
| `net_sales` | `operating_expenses` | **1.0** | Strong Positive |
| `tax_amount` | `operating_expenses` | **1.0** | Strong Positive |
| `unit_price` | `net_sales` | **0.9961** | Strong Positive |
| `unit_price` | `tax_amount` | **0.9961** | Strong Positive |
| `unit_price` | `operating_expenses` | **0.9961** | Strong Positive |
| `gross_sales` | `net_sales` | **0.9961** | Strong Positive |
| `gross_sales` | `tax_amount` | **0.9961** | Strong Positive |