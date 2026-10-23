# BÁO CÁO TỔNG HỢP THU THẬP VÀ PHÂN TÍCH DỮ LIỆU THỰC TẾ (DATA COLLECTION & PRELIMINARY EDA REPORT)

> **Dự án:** Code Candy – AI BI Dashboard  
> **Ngày tạo:** 04/10/2026  
> **Thư mục quản lý:** `data/`  
> **Phạm vi:** Tổng hợp hiện trạng dữ liệu thực tế, cấu trúc tổ chức, đặc tả kỹ thuật và kết quả phân tích khám phá sơ bộ (EDA) phục vụ thiết lập Semantic Schema (`ecommerce_schema.json`) và Synthetic Data Pipeline.

---

## I. TỔNG QUAN VỀ DỮ LIỆU THU THẬP

- **Tổng số nhóm dữ liệu lớn:** 5 nhóm chính (`Olist E-Commerce`, `Marketing Ad Spend`, `Retail Margins & Fees`, `Online Retail II`, `Text-to-SQL Benchmarks`).
- **Tổng số tệp dữ liệu đã thu thập & phân tích:** 17 tệp/bảng dữ liệu.
- **Tổng dung lượng dữ liệu thô:** ~140+ MB với hơn 1.000.000+ bản ghi giao dịch và kế toán thực tế.
- **Mục tiêu:** Bù đắp 100% các biến tài chính khuyết thiếu (`Unit_Cost/COGS`, `Marketing_Spend`, `Platform_Fee`, `Freight/Shipping`, `Payment_Type`, `Order_Status`) nhằm phục vụ:
  1. Thiết lập **Semantic Schema** chuẩn hóa 5 bảng (`customers`, `products`, `orders`, `sales`, `financials`).
  2. Cung cấp dữ liệu mồi (**Seed Data**) cho bộ sinh dữ liệu tổng hợp (Synthetic Data Generator).
  3. Tạo tập kiểm định độc lập (**Real Holdout Set**) phục vụ phương pháp đánh giá TSTR (Train on Synthetic, Test on Real).
  4. Cung cấp ngữ cảnh thực tế cho **Chatbot Text-to-SQL Engine**.

---

## II. CẤU TRÚC THƯ MỤC DỮ LIỆU CHUẨN HÓA (`data/`)

Toàn bộ dữ liệu thô và các tệp xử lý đã được quy hoạch gọn gàng trong thư mục `data/` theo đúng chuẩn kiến trúc của dự án:

```text
data/
├── sample_dataset/
│   ├── raw_sources/                          # Lưu trữ nguồn dữ liệu thực tế thô đã thu thập
│   │   ├── olist_ecommerce/                  # 1. Dữ liệu vận hành TMĐT & chu trình đơn hàng thực tế
│   │   │   ├── olist_orders_dataset.csv
│   │   │   ├── olist_order_items_dataset.csv
│   │   │   ├── olist_order_payments_dataset.csv
│   │   │   ├── olist_products_dataset.csv
│   │   │   └── olist_customers_dataset.csv
│   │   ├── marketing_ad_spend/               # 2. Dữ liệu chi phí & hiệu quả Ads tiếp thị số
│   │   │   └── ABmarketing_campaign.csv
│   │   ├── retail_margins_and_fees/          # 3. Dữ liệu phân phối Giá vốn COGS & Biên lợi nhuận
│   │   │   └── amazon_sales_margin.csv
│   │   ├── online_retail_ii/                 # 4. Giao dịch mua sắm chi tiết (Cleaned + Raw)
│   │   │   ├── online_retail_II.xlsx
│   │   │   └── eda_output/
│   │   │       └── cleaned_online_retail.csv
│   │   └── text_to_sql/                      # 5. Dữ liệu kế toán doanh nghiệp & Benchmark Text-to-SQL
│   │       ├── BookSQL/                      # Hệ thống bảng kế toán B2B (accounting tables & sqlite)
│   │       │   ├── accounting tables/
│   │       │   │   ├── chart_of_account_OB.csv
│   │       │   │   ├── customer_table.csv
│   │       │   │   ├── employee_table.csv
│   │       │   │   ├── Master_txn_table_1.csv
│   │       │   │   ├── Master_txn_table_2.csv
│   │       │   │   ├── payment_method.csv
│   │       │   │   ├── product_service_table.csv
│   │       │   │   └── vendor_table.csv
│   │       │   └── BookSQL/
│   │       │       └── accounting.sqlite
│   │       └── Spider 2.0-Snow/              # Tập Benchmark câu hỏi đa miền Snowflake/BigQuery
│   │           └── spider2-snow.jsonl
│   └── ecommerce_seed.csv                    # Tệp dữ liệu mồi hợp nhất chuẩn hóa (Giai đoạn 1 - Task 3)
├── generated/
│   └── synthetic_ecommerce.csv               # Tệp dữ liệu tổng hợp sinh ra từ Generator (Giai đoạn 2 - Task 6)
└── warehouse/
    ├── real_holdout.csv                      # Tập dữ liệu thực độc lập phục vụ nghiệm thu (Giai đoạn 1 - Task 3)
    └── app_database.db                       # CSDL lưu Users, RBAC, Settings & Chat History (Giai đoạn 3 - Task 8)
```


---

## III. BÁO CÁO CHI TIẾT TỪNG BỘ DỮ LIỆU & PHÂN TÍCH EDA SƠ BỘ

### 1. Nhóm Dữ liệu Vận hành TMĐT (Olist E-Commerce)

*Số lượng tệp:* 5

#### 📄 Tệp: `olist_orders_dataset.csv`
- **Tên Dataset:** Olist Orders Dataset
- **Nguồn thu thập:** Olist / Kaggle
- **Định dạng & Quy mô:** Bảng quan hệ Đơn hàng (CSV) | **99,441 dòng** | **8 cột** | **Dung lượng:** 16.84 MB
- **Mục đích sử dụng:** Cung cấp chu kỳ vòng đời đơn hàng, trạng thái (delivered, shipped, canceled) và các mốc thời gian đặt/giao hàng.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `order_id` | `str` | 0.0% | 99,441 | `e481f51cbdc54678b7cc49136f2d6af7` |
| `customer_id` | `str` | 0.0% | 99,441 | `9ef432eb6251297304e76186b10a928d` |
| `order_status` | `str` | 0.0% | 8 | `delivered` |
| `order_purchase_timestamp` | `str` | 0.0% | 98,875 | `2017-10-02 10:56:33` |
| `order_approved_at` | `str` | 0.16% | 90,733 | `2017-10-02 11:07:15` |
| `order_delivered_carrier_date` | `str` | 1.79% | 81,018 | `2017-10-04 19:55:00` |
| `order_delivered_customer_date` | `str` | 2.98% | 95,664 | `2017-10-10 21:25:13` |
| `order_estimated_delivery_date` | `str` | 0.0% | 459 | `2017-10-18 00:00:00` |

---

#### 📄 Tệp: `olist_order_items_dataset.csv`
- **Tên Dataset:** Olist Order Items Dataset
- **Nguồn thu thập:** Olist / Kaggle
- **Định dạng & Quy mô:** Bảng chi tiết mặt hàng đơn (CSV) | **112,650 dòng** | **7 cột** | **Dung lượng:** 14.72 MB
- **Mục đích sử dụng:** Cung cấp đơn giá bán thực tế (`price`) và chi phí vận chuyển thực tế (`freight_value`) của từng sản phẩm trong đơn.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `order_id` | `str` | 0.0% | 98,666 | `00010242fe8c5a6d1ba2dd792cb16214` |
| `order_item_id` | `int64` | 0.0% | 21 | `1` |
| `product_id` | `str` | 0.0% | 32,951 | `4244733e06e7ecb4970a6e2683c13e61` |
| `seller_id` | `str` | 0.0% | 3,095 | `48436dade18ac8b2bce089ec2a041202` |
| `shipping_limit_date` | `str` | 0.0% | 93,318 | `2017-09-19 09:45:35` |
| `price` | `float64` | 0.0% | 5,968 | `58.9` |
| `freight_value` | `float64` | 0.0% | 6,999 | `13.29` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `order_item_id`: Min = **1.0**, Max = **21.0**, Mean = **1.2**
- `price`: Min = **0.85**, Max = **6735.0**, Mean = **120.65**
- `freight_value`: Min = **0.0**, Max = **409.68**, Mean = **19.99**

---

#### 📄 Tệp: `olist_order_payments_dataset.csv`
- **Tên Dataset:** Olist Order Payments Dataset
- **Nguồn thu thập:** Olist / Kaggle
- **Định dạng & Quy mô:** Bảng thanh toán đơn hàng (CSV) | **103,886 dòng** | **5 cột** | **Dung lượng:** 5.51 MB
- **Mục đích sử dụng:** Cung cấp các kênh thanh toán thực tế (credit_card, boleto, voucher, debit_card) và số tiền thanh toán.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `order_id` | `str` | 0.0% | 99,440 | `b81ef226f3fe1789b1e8b2acac839d17` |
| `payment_sequential` | `int64` | 0.0% | 29 | `1` |
| `payment_type` | `str` | 0.0% | 5 | `credit_card` |
| `payment_installments` | `int64` | 0.0% | 24 | `8` |
| `payment_value` | `float64` | 0.0% | 29,077 | `99.33` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `payment_sequential`: Min = **1.0**, Max = **29.0**, Mean = **1.09**
- `payment_installments`: Min = **0.0**, Max = **24.0**, Mean = **2.85**
- `payment_value`: Min = **0.0**, Max = **13664.08**, Mean = **154.1**

---

#### 📄 Tệp: `olist_products_dataset.csv`
- **Tên Dataset:** Olist Products Dataset
- **Nguồn thu thập:** Olist / Kaggle
- **Định dạng & Quy mô:** Bảng danh mục sản phẩm (CSV) | **32,951 dòng** | **9 cột** | **Dung lượng:** 2.27 MB
- **Mục đích sử dụng:** Cung cấp tên danh mục sản phẩm (category), kích thước, khối lượng thực tế.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `product_id` | `str` | 0.0% | 32,951 | `1e9e8ef04dbcff4541ed26657ea517e5` |
| `product_category_name` | `str` | 1.85% | 73 | `perfumaria` |
| `product_name_lenght` | `float64` | 1.85% | 66 | `40.0` |
| `product_description_lenght` | `float64` | 1.85% | 2,960 | `287.0` |
| `product_photos_qty` | `float64` | 1.85% | 19 | `1.0` |
| `product_weight_g` | `float64` | 0.01% | 2,204 | `225.0` |
| `product_length_cm` | `float64` | 0.01% | 99 | `16.0` |
| `product_height_cm` | `float64` | 0.01% | 102 | `10.0` |
| `product_width_cm` | `float64` | 0.01% | 95 | `14.0` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `product_name_lenght`: Min = **5.0**, Max = **76.0**, Mean = **48.48**
- `product_description_lenght`: Min = **4.0**, Max = **3992.0**, Mean = **771.5**
- `product_photos_qty`: Min = **1.0**, Max = **20.0**, Mean = **2.19**
- `product_weight_g`: Min = **0.0**, Max = **40425.0**, Mean = **2276.47**
- `product_length_cm`: Min = **7.0**, Max = **105.0**, Mean = **30.82**
- `product_height_cm`: Min = **2.0**, Max = **105.0**, Mean = **16.94**

---

#### 📄 Tệp: `olist_customers_dataset.csv`
- **Tên Dataset:** Olist Customers Dataset
- **Nguồn thu thập:** Olist / Kaggle
- **Định dạng & Quy mô:** Bảng khách hàng (CSV) | **99,441 dòng** | **5 cột** | **Dung lượng:** 8.62 MB
- **Mục đích sử dụng:** Cung cấp định danh khách hàng, thành phố, bang/vùng miền phục vụ phân tích địa lý và phân khúc khách hàng.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `customer_id` | `str` | 0.0% | 99,441 | `06b8999e2fba1a1fbc88172c00ba8bc7` |
| `customer_unique_id` | `str` | 0.0% | 96,096 | `861eff4711a542e4b93843c6dd7febb0` |
| `customer_zip_code_prefix` | `int64` | 0.0% | 14,994 | `14409` |
| `customer_city` | `str` | 0.0% | 4,119 | `franca` |
| `customer_state` | `str` | 0.0% | 27 | `SP` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `customer_zip_code_prefix`: Min = **1003.0**, Max = **99990.0**, Mean = **35137.47**

---

### 2. Nhóm Dữ liệu Chi phí & Hiệu quả Tiếp thị (Marketing Ad Spend)

*Số lượng tệp:* 1

#### 📄 Tệp: `ABmarketing_campaign.csv`
- **Tên Dataset:** A/B Marketing Ad Spend Campaign
- **Nguồn thu thập:** Digital Advertising Benchmark / Kaggle
- **Định dạng & Quy mô:** Chuỗi thời gian Chi phí Tiếp thị đa kênh (CSV) | **365 dòng** | **17 cột** | **Dung lượng:** 0.03 MB
- **Mục đích sử dụng:** Cung cấp số liệu chi tiêu quảng cáo hàng ngày (Facebook Ads vs Google AdWords), lượt xem, lượt click, chuyển đổi và chi phí trên mỗi đơn chuyển đổi để tính ROAS, CAC và bảng financials.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `Date` | `str` | 0.0% | 365 | `1/1/2019` |
| `Facebook Ad Campaign` | `str` | 0.0% | 12 | `FB_Jan19` |
| `Facebook Ad Views` | `int64` | 0.0% | 330 | `2116` |
| `Facebook Ad Clicks` | `int64` | 0.0% | 56 | `18` |
| `Facebook Ad Conversions` | `int64` | 0.0% | 15 | `8` |
| `Cost per Facebook Ad` | `str` | 0.0% | 104 | `$126` |
| `Facebook Click-Through Rate (Clicks / View)` | `str` | 0.0% | 213 | `0.83%` |
| `Facebook Conversion Rate (Conversions / Clicks)` | `str` | 0.0% | 308 | `42.73%` |
| `Facebook Cost per Click (Ad Cost / Clicks)` | `str` | 0.0% | 228 | `$7.14` |
| `AdWords Ad Campaign` | `str` | 0.0% | 12 | `AW_Jan19` |
| `AdWords Ad Views` | `int64` | 0.0% | 335 | `4984` |
| `AdWords Ad Clicks` | `int64` | 0.0% | 58 | `59` |
| `AdWords Ad Conversions` | `int64` | 0.0% | 7 | `5` |
| `Cost per AdWords Ad` | `str` | 0.0% | 118 | `$194` |
| `AdWords Click-Through Rate (Clicks / View)` | `str` | 0.0% | 133 | `1.18%` |
| `AdWords Conversion Rate (Conversions / Click)` | `str` | 0.0% | 291 | `8.40%` |
| `AdWords Cost per Click (Ad Cost / Clicks)` | `str` | 0.0% | 219 | `$3.30` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `Facebook Ad Views`: Min = **1050.0**, Max = **3320.0**, Mean = **2179.69**
- `Facebook Ad Clicks`: Min = **15.0**, Max = **73.0**, Mean = **44.05**
- `Facebook Ad Conversions`: Min = **5.0**, Max = **19.0**, Mean = **11.74**
- `AdWords Ad Views`: Min = **3714.0**, Max = **5760.0**, Mean = **4717.2**
- `AdWords Ad Clicks`: Min = **31.0**, Max = **89.0**, Mean = **60.38**
- `AdWords Ad Conversions`: Min = **3.0**, Max = **9.0**, Mean = **5.98**

---

### 3. Nhóm Dữ liệu Giá vốn & Biên Lợi nhuận Bán lẻ (Retail Margins & Fees)

*Số lượng tệp:* 1

#### 📄 Tệp: `amazon_sales_margin.csv`
- **Tên Dataset:** Retail Sales, COGS & Profit Margin Dataset
- **Nguồn thu thập:** Amazon Sales Analysis / Kaggle
- **Định dạng & Quy mô:** Bảng Bán lẻ & Cơ cấu Giá vốn (CSV) | **100 dòng** | **14 cột** | **Dung lượng:** 0.01 MB
- **Mục đích sử dụng:** Cung cấp phân phối giá vốn thực tế (`Unit Cost`), giá bán (`Unit Price`), tổng doanh thu, tổng chi phí và lợi nhuận gộp theo từng ngành hàng phục vụ ràng buộc business_rules.py.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `Region` | `str` | 0.0% | 7 | `Australia and Oceania` |
| `Country` | `str` | 0.0% | 76 | `Tuvalu` |
| `Item Type` | `str` | 0.0% | 12 | `Baby Food` |
| `Sales Channel` | `str` | 0.0% | 2 | `Offline` |
| `Order Priority` | `str` | 0.0% | 4 | `H` |
| `Order Date` | `str` | 0.0% | 100 | `5/28/2010` |
| `Order ID` | `int64` | 0.0% | 100 | `669165933` |
| `Ship Date` | `str` | 0.0% | 99 | `6/27/2010` |
| `Units Sold` | `int64` | 0.0% | 99 | `9925` |
| `Unit Price` | `float64` | 0.0% | 12 | `255.28` |
| `Unit Cost` | `float64` | 0.0% | 12 | `159.42` |
| `Total Revenue` | `float64` | 0.0% | 100 | `2533654.0` |
| `Total Cost` | `float64` | 0.0% | 100 | `1582243.5` |
| `Total Profit` | `float64` | 0.0% | 100 | `951410.5` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `Order ID`: Min = **114606559.0**, Max = **994022214.0**, Mean = **555020412.36**
- `Units Sold`: Min = **124.0**, Max = **9925.0**, Mean = **5128.71**
- `Unit Price`: Min = **9.33**, Max = **668.27**, Mean = **276.76**
- `Unit Cost`: Min = **6.92**, Max = **524.96**, Mean = **191.05**
- `Total Revenue`: Min = **4870.26**, Max = **5997054.98**, Mean = **1373487.68**
- `Total Cost`: Min = **3612.24**, Max = **4509793.96**, Mean = **931805.7**

---

### 4. Nhóm Dữ liệu Giao dịch Bán lẻ Chi tiết (Online Retail II)

*Số lượng tệp:* 1

#### 📄 Tệp: `cleaned_online_retail.csv`
- **Tên Dataset:** Online Retail II Cleaned Dataset
- **Nguồn thu thập:** UCI Machine Learning Repository
- **Định dạng & Quy mô:** Giao dịch bán lẻ trực tuyến lớn (CSV) | **400,916 dòng** | **15 cột** | **Dung lượng:** 45.58 MB
- **Mục đích sử dụng:** Bộ dữ liệu giao dịch cốt lõi gồm hơn 800.000 dòng ghi nhận chi tiết hành vi mua hàng, giỏ hàng, số lượng và doanh thu theo thời gian.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `Invoice` | `int64` | 0.0% | 19,213 | `489434` |
| `StockCode` | `str` | 0.0% | 4,017 | `85048` |
| `Description` | `str` | 0.0% | 4,444 | `15CM CHRISTMAS GLASS BALL 20 LIGHTS` |
| `Quantity` | `int64` | 0.0% | 343 | `12` |
| `InvoiceDate` | `str` | 0.0% | 18,008 | `2009-12-01 07:45:00` |
| `Price` | `float64` | 0.0% | 448 | `6.95` |
| `Customer ID` | `int64` | 0.0% | 4,312 | `13085` |
| `Country` | `str` | 0.0% | 37 | `United Kingdom` |
| `Amount` | `float64` | 0.0% | 2,421 | `83.4` |
| `Year` | `int64` | 0.0% | 2 | `2009` |
| `Month` | `int64` | 0.0% | 12 | `12` |
| `Day` | `int64` | 0.0% | 31 | `1` |
| `Hour` | `int64` | 0.0% | 14 | `7` |
| `DayOfWeek` | `int64` | 0.0% | 7 | `1` |
| `MonthYear` | `str` | 0.0% | 13 | `2009-12` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `Invoice`: Min = **489434.0**, Max = **538171.0**, Mean = **514731.38**
- `Quantity`: Min = **1.0**, Max = **19152.0**, Mean = **13.77**
- `Price`: Min = **0.001**, Max = **10953.5**, Mean = **3.31**
- `Customer ID`: Min = **12346.0**, Max = **18287.0**, Mean = **15361.54**
- `Amount`: Min = **0.001**, Max = **15818.4**, Mean = **21.95**
- `Year`: Min = **2009.0**, Max = **2010.0**, Mean = **2009.92**

---

### 5. Nhóm Dữ liệu Kế toán Doanh nghiệp & Text-to-SQL (BookSQL & Spider 2.0)

*Số lượng tệp:* 9

#### 📄 Tệp: `Master_txn_table_1.csv`
- **Tên Dataset:** BookSQL Accounting Table (Master_txn_table_1.csv)
- **Nguồn thu thập:** BookSQL Benchmark / Research
- **Định dạng & Quy mô:** Bảng kế toán doanh nghiệp (CSV) | **405,029 dòng** | **32 cột** | **Dung lượng:** 88.18 MB
- **Mục đích sử dụng:** Cung cấp cấu trúc tài khoản kế toán, công nợ A/R, A/P, thuế và phương thức thanh toán phục vụ đào tạo/prompt cho AI Chatbot Text-to-SQL.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `Unnamed: 0.3` | `int64` | 0.0% | 405,029 | `0` |
| `Unnamed: 0.2` | `int64` | 0.0% | 405,029 | `0` |
| `Unnamed: 0.1` | `int64` | 0.0% | 405,029 | `0` |
| `Unnamed: 0` | `int64` | 0.0% | 405,029 | `24925` |
| `business Id` | `int64` | 0.0% | 14 | `2` |
| `Transaction ID` | `int64` | 0.0% | 84,762 | `6422` |
| `Transaction date` | `str` | 0.0% | 10,954 | `2010-12-27` |
| `Transaction type` | `str` | 0.0% | 21 | `Credit Card Credit` |
| `Amount` | `float64` | 0.0% | 55 | `34985.71` |
| `Created date` | `str` | 0.0% | 11,212 | `2011-10-12` |
| `Created user` | `str` | 0.0% | 14 | `Evan Gibbs` |
| `Account` | `str` | 0.0% | 193 | `Accounts Receivable (A/R)` |
| `A/R paid` | `str` | 0.0% | 2 | `Paid` |
| `A/P paid` | `str` | 0.0% | 2 | `--` |
| `Due date` | `str` | 0.0% | 11,343 | `2012-07-23` |
| `Open balance` | `float64` | 0.0% | 83,821 | `6468.78` |
| `PO status` | `str` | 0.0% | 1 | `--` |
| `Estimate status` | `str` | 0.0% | 1 | `--` |
| `Customer name` | `str` | 0.0% | 61,799 | `Larry Mendoza` |
| `Vendor name` | `str` | 0.0% | 549 | `--` |
| `Product_Service` | `str` | 0.0% | 140 | `--` |
| `Quantity` | `str` | 0.0% | 50 | `--` |
| `Rate` | `str` | 0.0% | 72 | `--` |
| `Credit` | `str` | 0.0% | 99 | `--` |
| `Debit` | `str` | 0.0% | 56 | `34985.71` |
| `Sale` | `str` | 0.0% | 2 | `Yes` |
| `Purchase` | `str` | 0.0% | 2 | `No` |
| `Billable` | `str` | 0.0% | 1 | `No` |
| `Invoiced` | `str` | 0.0% | 1 | `--` |
| `Cleared` | `str` | 0.0% | 2 | `--` |
| `payment method` | `str` | 0.0% | 7 | `Discover` |
| `Misc (Business specific fields)` | `str` | 0.0% | 3 | `--` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `Unnamed: 0.3`: Min = **0.0**, Max = **405028.0**, Mean = **202514.0**
- `Unnamed: 0.2`: Min = **0.0**, Max = **405028.0**, Mean = **202514.0**
- `Unnamed: 0.1`: Min = **0.0**, Max = **405028.0**, Mean = **202514.0**
- `Unnamed: 0`: Min = **0.0**, Max = **420031.0**, Mean = **202796.56**
- `business Id`: Min = **2.0**, Max = **15.0**, Mean = **8.26**
- `Transaction ID`: Min = **317.0**, Max = **88219.0**, Mean = **42889.29**

---

#### 📄 Tệp: `Master_txn_table_2.csv`
- **Tên Dataset:** BookSQL Accounting Table (Master_txn_table_2.csv)
- **Nguồn thu thập:** BookSQL Benchmark / Research
- **Định dạng & Quy mô:** Bảng kế toán doanh nghiệp (CSV) | **405,030 dòng** | **32 cột** | **Dung lượng:** 89.34 MB
- **Mục đích sử dụng:** Cung cấp cấu trúc tài khoản kế toán, công nợ A/R, A/P, thuế và phương thức thanh toán phục vụ đào tạo/prompt cho AI Chatbot Text-to-SQL.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `Unnamed: 0.3` | `int64` | 0.0% | 405,030 | `405029` |
| `Unnamed: 0.2` | `int64` | 0.0% | 405,030 | `405029` |
| `Unnamed: 0.1` | `int64` | 0.0% | 405,030 | `405029` |
| `Unnamed: 0` | `int64` | 0.0% | 405,030 | `397337` |
| `business Id` | `int64` | 0.0% | 14 | `15` |
| `Transaction ID` | `int64` | 0.0% | 84,764 | `84071` |
| `Transaction date` | `str` | 0.0% | 10,953 | `2014-11-02` |
| `Transaction type` | `str` | 0.0% | 21 | `Sales Tax Payment` |
| `Amount` | `float64` | 0.0% | 56 | `31397.33` |
| `Created date` | `str` | 0.0% | 11,211 | `2015-09-17` |
| `Created user` | `str` | 0.0% | 14 | `Katrina Dennis` |
| `Account` | `str` | 0.0% | 195 | `Uncategorized Income` |
| `A/R paid` | `str` | 0.0% | 2 | `Paid` |
| `A/P paid` | `str` | 0.0% | 2 | `--` |
| `Due date` | `str` | 0.0% | 11,348 | `2016-07-15` |
| `Open balance` | `float64` | 0.0% | 83,448 | `53.16` |
| `PO status` | `str` | 0.0% | 1 | `--` |
| `Estimate status` | `str` | 0.0% | 1 | `--` |
| `Customer name` | `str` | 0.0% | 61,880 | `Steven Guerra` |
| `Vendor name` | `str` | 0.0% | 548 | `--` |
| `Product_Service` | `str` | 0.0% | 143 | `--` |
| `Quantity` | `str` | 0.0% | 51 | `31` |
| `Rate` | `str` | 0.0% | 72 | `330.57` |
| `Credit` | `str` | 0.0% | 100 | `10247.67` |
| `Debit` | `str` | 0.0% | 57 | `--` |
| `Sale` | `str` | 0.0% | 2 | `Yes` |
| `Purchase` | `str` | 0.0% | 2 | `No` |
| `Billable` | `str` | 0.0% | 1 | `No` |
| `Invoiced` | `str` | 0.0% | 1 | `--` |
| `Cleared` | `str` | 0.0% | 2 | `--` |
| `payment method` | `str` | 0.0% | 7 | `Diners Club` |
| `Misc (Business specific fields)` | `str` | 0.0% | 3 | `--` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `Unnamed: 0.3`: Min = **405029.0**, Max = **810058.0**, Mean = **607543.5**
- `Unnamed: 0.2`: Min = **405029.0**, Max = **810058.0**, Mean = **607543.5**
- `Unnamed: 0.1`: Min = **405029.0**, Max = **810058.0**, Mean = **607543.5**
- `Unnamed: 0`: Min = **390049.0**, Max = **810067.0**, Mean = **607273.83**
- `business Id`: Min = **15.0**, Max = **28.0**, Mean = **21.74**
- `Transaction ID`: Min = **81944.0**, Max = **169848.0**, Mean = **127538.89**

---

#### 📄 Tệp: `chart_of_account_OB.csv`
- **Tên Dataset:** BookSQL Accounting Table (chart_of_account_OB.csv)
- **Nguồn thu thập:** BookSQL Benchmark / Research
- **Định dạng & Quy mô:** Bảng kế toán doanh nghiệp (CSV) | **2,430 dòng** | **5 cột** | **Dung lượng:** 0.12 MB
- **Mục đích sử dụng:** Cung cấp cấu trúc tài khoản kế toán, công nợ A/R, A/P, thuế và phương thức thanh toán phục vụ đào tạo/prompt cho AI Chatbot Text-to-SQL.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `Unnamed: 0` | `int64` | 0.0% | 2,430 | `0` |
| `Business Id` | `int64` | 0.0% | 27 | `2` |
| `Account name` | `str` | 0.0% | 340 | `Bookkeeper` |
| `Account Full Name` | `str` | 0.0% | 340 | `Bookkeeper` |
| `Account type` | `str` | 0.0% | 13 | `Expenses` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `Unnamed: 0`: Min = **0.0**, Max = **2429.0**, Mean = **1214.5**
- `Business Id`: Min = **2.0**, Max = **28.0**, Mean = **15.0**

---

#### 📄 Tệp: `customer_table.csv`
- **Tên Dataset:** BookSQL Accounting Table (customer_table.csv)
- **Nguồn thu thập:** BookSQL Benchmark / Research
- **Định dạng & Quy mô:** Bảng kế toán doanh nghiệp (CSV) | **50,000 dòng** | **13 cột** | **Dung lượng:** 6.14 MB
- **Mục đích sử dụng:** Cung cấp cấu trúc tài khoản kế toán, công nợ A/R, A/P, thuế và phương thức thanh toán phục vụ đào tạo/prompt cho AI Chatbot Text-to-SQL.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `Unnamed: 0` | `int64` | 0.0% | 50,000 | `0` |
| `Business Id` | `int64` | 0.0% | 500 | `2` |
| `Customer name` | `str` | 0.0% | 40,239 | `Valerie Kline` |
| `Customer full name` | `str` | 0.0% | 40,239 | `Valerie Kline` |
| `Billing address` | `str` | 0.0% | 49,339 | `63755 Todd Course` |
| `Billing city` | `str` | 0.0% | 23,378 | `North Teresastad` |
| `Billing state` | `str` | 0.0% | 62 | `MT` |
| `Billing ZIP code` | `int64` | 0.0% | 39,367 | `12753` |
| `Shipping address` | `str` | 0.0% | 49,373 | `3928 Jones Fall Suite 223` |
| `Shipping city` | `str` | 0.0% | 23,404 | `Mosleymouth` |
| `Shipping state` | `str` | 0.0% | 62 | `KS` |
| `Shipping ZIP code` | `int64` | 0.0% | 39,259 | `97173` |
| `Balance` | `str` | 0.0% | 1 | `--` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `Unnamed: 0`: Min = **0.0**, Max = **49999.0**, Mean = **24999.5**
- `Business Id`: Min = **2.0**, Max = **501.0**, Mean = **251.5**
- `Billing ZIP code`: Min = **503.0**, Max = **99950.0**, Mean = **50463.84**
- `Shipping ZIP code`: Min = **504.0**, Max = **99950.0**, Mean = **50393.32**

---

#### 📄 Tệp: `employee_table.csv`
- **Tên Dataset:** BookSQL Accounting Table (employee_table.csv)
- **Nguồn thu thập:** BookSQL Benchmark / Research
- **Định dạng & Quy mô:** Bảng kế toán doanh nghiệp (CSV) | **50,000 dòng** | **7 cột** | **Dung lượng:** 2.3 MB
- **Mục đích sử dụng:** Cung cấp cấu trúc tài khoản kế toán, công nợ A/R, A/P, thuế và phương thức thanh toán phục vụ đào tạo/prompt cho AI Chatbot Text-to-SQL.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `Unnamed: 0` | `int64` | 0.0% | 50,000 | `0` |
| `Business Id` | `int64` | 0.0% | 500 | `1` |
| `Employee name` | `str` | 0.0% | 40,115 | `Brenda Colon` |
| `Employee ID` | `str` | 0.0% | 40,313 | `BRE888` |
| `Hire date` | `str` | 0.0% | 11,297 | `12/26/1995` |
| `Billing rate` | `str` | 0.0% | 1 | `--` |
| `Deleted` | `str` | 0.0% | 2 | `Yes` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `Unnamed: 0`: Min = **0.0**, Max = **49999.0**, Mean = **24999.5**
- `Business Id`: Min = **1.0**, Max = **500.0**, Mean = **250.5**

---

#### 📄 Tệp: `payment_method.csv`
- **Tên Dataset:** BookSQL Accounting Table (payment_method.csv)
- **Nguồn thu thập:** BookSQL Benchmark / Research
- **Định dạng & Quy mô:** Bảng kế toán doanh nghiệp (CSV) | **189 dòng** | **4 cột** | **Dung lượng:** 0.0 MB
- **Mục đích sử dụng:** Cung cấp cấu trúc tài khoản kế toán, công nợ A/R, A/P, thuế và phương thức thanh toán phục vụ đào tạo/prompt cho AI Chatbot Text-to-SQL.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `Unnamed: 0` | `int64` | 0.0% | 189 | `0` |
| `Business Id` | `int64` | 0.0% | 27 | `2` |
| `Payment method` | `str` | 0.0% | 7 | `Visa` |
| `Credit card` | `str` | 0.0% | 2 | `Yes` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `Unnamed: 0`: Min = **0.0**, Max = **188.0**, Mean = **94.0**
- `Business Id`: Min = **2.0**, Max = **28.0**, Mean = **15.0**

---

#### 📄 Tệp: `product_service_table.csv`
- **Tên Dataset:** BookSQL Accounting Table (product_service_table.csv)
- **Nguồn thu thập:** BookSQL Benchmark / Research
- **Định dạng & Quy mô:** Bảng kế toán doanh nghiệp (CSV) | **270 dòng** | **4 cột** | **Dung lượng:** 0.01 MB
- **Mục đích sử dụng:** Cung cấp cấu trúc tài khoản kế toán, công nợ A/R, A/P, thuế và phương thức thanh toán phục vụ đào tạo/prompt cho AI Chatbot Text-to-SQL.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `Unnamed: 0` | `int64` | 0.0% | 270 | `0` |
| `Business Id` | `int64` | 0.0% | 27 | `2` |
| `Product_Service` | `str` | 0.0% | 266 | `Casino Hotels` |
| `Product_Service_Type` | `str` | 0.0% | 1 | `Service` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `Unnamed: 0`: Min = **0.0**, Max = **269.0**, Mean = **134.5**
- `Business Id`: Min = **2.0**, Max = **28.0**, Mean = **15.0**

---

#### 📄 Tệp: `vendor_table.csv`
- **Tên Dataset:** BookSQL Accounting Table (vendor_table.csv)
- **Nguồn thu thập:** BookSQL Benchmark / Research
- **Định dạng & Quy mô:** Bảng kế toán doanh nghiệp (CSV) | **100,000 dòng** | **8 cột** | **Dung lượng:** 6.77 MB
- **Mục đích sử dụng:** Cung cấp cấu trúc tài khoản kế toán, công nợ A/R, A/P, thuế và phương thức thanh toán phục vụ đào tạo/prompt cho AI Chatbot Text-to-SQL.

**Bảng tổng hợp đặc tính thuộc tính & EDA sơ bộ:**

| Cột (Field) | Kiểu dữ liệu | Tỷ lệ khuyết (Null %) | Số giá trị duy nhất | Giá trị mẫu |
| :--- | :--- | :--- | :--- | :--- |
| `Unnamed: 0` | `int64` | 0.0% | 100,000 | `0` |
| `Business Id` | `int64` | 0.0% | 1,000 | `2` |
| `Vendor name` | `str` | 0.0% | 70,942 | `Cassidy Smith DDS` |
| `Billing address` | `str` | 0.0% | 98,344 | `941 Moore Summit` |
| `Billing city` | `str` | 0.0% | 35,709 | `Taylorchester` |
| `Billing state` | `str` | 0.0% | 62 | `MI` |
| `Billing ZIP code` | `int64` | 0.0% | 63,098 | `35380` |
| `Balance` | `str` | 0.0% | 1 | `--` |

**Thống kê mô tả số lượng (Min, Max, Mean):**

- `Unnamed: 0`: Min = **0.0**, Max = **99999.0**, Mean = **49999.5**
- `Business Id`: Min = **2.0**, Max = **1001.0**, Mean = **501.5**
- `Billing ZIP code`: Min = **503.0**, Max = **99949.0**, Mean = **50324.64**

---

#### 📄 Tệp: `spider2-snow.jsonl`
- **Tên Dataset:** Spider 2.0-Snow Enterprise Benchmark
- **Nguồn thu thập:** Spider 2.0 Benchmark (Snowflake / BigQuery)
- **Định dạng & Quy mô:** Tập câu hỏi & Truy vấn đa dạng (JSON Lines) | **547 dòng** | **4 cột** | **Dung lượng:** 0.23 MB
- **Mục đích sử dụng:** Bộ câu hỏi Text-to-SQL chuẩn quốc tế dùng để xây dựng prompt templates, guardrails và benchmark cho module AI Chatbot (Task 14).

---

## IV. ĐÁNH GIÁ MỨC ĐỘ KHẢ THI & KẾ HOẠCH HỢP NHẤT SEED DATA

1. **Tính hoàn chỉnh của Schema:**
   - Sự kết hợp giữa `Online Retail II` (giao dịch mua sắm khối lượng lớn), `Olist E-Commerce` (chu trình trạng thái đơn & phí vận chuyển), `Amazon Margins` (giá vốn COGS theo ngành) và `Marketing Ad Spend` (chi phí Ads Facebook/Google) cho phép xây dựng một **Semantic Schema E-commerce 5 bảng chuẩn hóa 100% không bị khuyết bất kỳ chỉ số tài chính nào**.

2. **Kế hoạch tạo `ecommerce_seed.csv` & `real_holdout.csv` (Task 3):**
   - Hợp nhất các nguồn dữ liệu trên thành 1 bảng phẳng hoặc 5 bảng quan hệ chuẩn.
   - Thực hiện phân tách 70% làm `data/sample_dataset/ecommerce_seed.csv` (dữ liệu mồi huấn luyện) và 30% làm `data/warehouse/real_holdout.csv` (tập kiểm thử độc lập).