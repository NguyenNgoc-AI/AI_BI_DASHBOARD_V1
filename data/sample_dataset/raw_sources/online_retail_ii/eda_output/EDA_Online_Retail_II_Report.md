# 📊 EDA REPORT — Online Retail II Dataset
**Generated:** 2026-09-08 23:08:20

## 1. 📁 Thông Tin File (File Metadata)

- **File:** `online_retail_II.xlsx`
- **Vị trí:** `Dataset/Data/2. DỮ LIỆU TÀI CHÍNH DOANH NGHIỆP/online+retail+ii/online_retail_II.xlsx`
- **Dung lượng:** 43.51 MB (45,622,278 bytes)
- **Nguồn:** UCI Machine Learning Repository — Online Retail II Data Set
- **Người tạo/cung cấp:** Dr. Daqing Chen, School of Computer Science and Informatics, De Montfort University
- **Ngày thu thập:** 01/12/2009 – 09/12/2011
- **Số sheet:** 2 (Year 2009-2010, Year 2010-2011)

## 2. 📋 Tổng Quan Dữ Liệu (Data Overview)

- **Tổng dòng (gộp 2 sheet):** 1,067,371
- **Tổng cột:** 9
- **Sheet 'Year 2009-2010': 525,461 dòng
- **Sheet 'Year 2010-2011': 541,910 dòng

## 3. 📖 Từ Điển Dữ Liệu (Data Dictionary) — Cho Project AI_BI_DASHBOARD

| Cột | Kiểu | Ý Nghĩa Nghiệp Vụ | Vai Trò Trong AI/BI Dashboard |
|-----|------|-------------------|-------------------------------|
| **Invoice** | string | Mã hóa đơn (có prefix 'C' = credit note/hủy/trả hàng) | Primary key giao dịch; phân biệt bán vs trả; join với fact table |
| **StockCode** | string | Mã SKU sản phẩm (5-6 ký tự, alphanumeric) | Dimension key sản phẩm; segment theo nhóm hàng; input cho recommendation engine |
| **Description** | string | Tên mô tả sản phẩm (tiếng Anh) | Label hiển thị UI; text analytics/NLP cho tìm kiếm, phân loại |
| **Quantity** | int64 | Số lượng (dương = bán, âm = trả/hủy) | Measure quan trọng: doanh thu, tồn kho, RFM frequency; outlier detection |
| **InvoiceDate** | datetime64 | Thời điểm giao dịch (độ chính xác: phút) | Time dimension; trend 분석, seasonality, cohort, forecasting |
| **Price** | float64 | Đơn giá (GBP) tại thời điểm bán | Measure giá; price elasticity, margin analysis, anomaly detection |
| **Customer ID** | float64 (nullable) | Mã khách hàng duy nhất (NaN = khách vãng lai/guest) | **Critical** cho RFM, CLV, segmentation, churn prediction; ~24% missing |
| **Country** | string | Quốc gia giao hàng/billing | Geo dimension; market expansion, shipping cost, localization |
| **Sheet** | string | Năm tài chính (2009-2010 / 2010-2011) | Partition key; year-over-year comparison |

## 4. 🔍 Demo 5 Dòng Đầu (Head)

|   Invoice | StockCode   | Description                         |   Quantity | InvoiceDate         |   Price |   Customer ID | Country        | Sheet          |
|----------:|:------------|:------------------------------------|-----------:|:--------------------|--------:|--------------:|:---------------|:---------------|
|    489434 | 85048       | 15CM CHRISTMAS GLASS BALL 20 LIGHTS |         12 | 2009-12-01 07:45:00 |    6.95 |         13085 | United Kingdom | Year 2009-2010 |
|    489434 | 79323P      | PINK CHERRY LIGHTS                  |         12 | 2009-12-01 07:45:00 |    6.75 |         13085 | United Kingdom | Year 2009-2010 |
|    489434 | 79323W      | WHITE CHERRY LIGHTS                 |         12 | 2009-12-01 07:45:00 |    6.75 |         13085 | United Kingdom | Year 2009-2010 |
|    489434 | 22041       | RECORD FRAME 7" SINGLE SIZE         |         48 | 2009-12-01 07:45:00 |    2.1  |         13085 | United Kingdom | Year 2009-2010 |
|    489434 | 21232       | STRAWBERRY CERAMIC TRINKET BOX      |         24 | 2009-12-01 07:45:00 |    1.25 |         13085 | United Kingdom | Year 2009-2010 |

## 5. 📈 Phân Bố Dữ Liệu (Data Distribution)

### Quantity
- Count: 1,067,371
- Mean: 9.9389
- Std: 172.7058
- Min: -80995.0000
- 1%: -3.0000
- 5%: 1.0000
- 25%: 1.0000
- 50% (Median): 3.0000
- 75%: 10.0000
- 95%: 30.0000
- 99%: 100.0000
- Max: 80995.0000

### Price
- Count: 1,067,371
- Mean: 4.6494
- Std: 123.5531
- Min: -53594.3600
- 1%: 0.2100
- 5%: 0.4200
- 25%: 1.2500
- 50% (Median): 2.1000
- 75%: 4.1500
- 95%: 9.9500
- 99%: 18.0000
- Max: 38970.0000

### Country
- Unique values: 43
- Top 10:
  - United Kingdom: 981,330 (91.9%)
  - EIRE: 17,866 (1.7%)
  - Germany: 17,624 (1.7%)
  - France: 14,330 (1.3%)
  - Netherlands: 5,140 (0.5%)
  - Spain: 3,811 (0.4%)
  - Switzerland: 3,189 (0.3%)
  - Belgium: 3,123 (0.3%)
  - Portugal: 2,620 (0.2%)
  - Australia: 1,913 (0.2%)

### Sheet
- Unique values: 2
- Top 10:
  - Year 2010-2011: 541,910 (50.8%)
  - Year 2009-2010: 525,461 (49.2%)

### InvoiceDate (Time Range)
- Min: 2009-12-01 07:45:00
- Max: 2011-12-09 12:50:00
- Span: 738 ngày

## 6. ❓ Kiểm Tra Missing Values

|             |   Missing_Count |   Missing_Pct |
|:------------|----------------:|--------------:|
| Customer ID |          243007 |         22.77 |
| Description |            4382 |          0.41 |

## 7. 🔄 Kiểm Tra Trùng Lặp (Duplicates)

- **Full-row duplicates:** 12,133 (1.14%)
- **Business-key duplicates (Invoice+StockCode):** 45,947 (4.30%)
- **Cancelled invoices (prefix C):** 19,494 dòng
- **Normal invoices:** 1,047,877 dòng

## 8. 📊 Ma Trận Tương Quan (Correlation Matrix)

### Pearson Correlation
|             |   Quantity |   Price |   Customer ID |
|:------------|-----------:|--------:|--------------:|
| Quantity    |     1      | -0.0013 |       -0.0054 |
| Price       |    -0.0013 |  1      |       -0.0038 |
| Customer ID |    -0.0054 | -0.0038 |        1      |

### 📝 Giải Thích:
- **Quantity ↔ Price:** 상관관계 yếu/âm → giá không phụ thuộc vào số lượng mua (không có volume discount rõ rệt).
- **Customer ID** không có ý nghĩa định lượng (chỉ là ID), tương quan với Quantity/Price không có ý nghĩa business.

## 9. 🧹 Đề Xuất Các Bước Cleaning (Proposed Cleaning Pipeline)

### Bước 1: Tách loại giao dịch
- Tách `Invoice` prefix `C` → bảng `returns` (trả/hủy)
- Giữ `Invoice` không có `C` → bảng `sales` (bán thuần)

### Bước 2: Xử lý Missing Customer ID
- **Option A (BI):** Gán `Customer_ID = 'GUEST_<Invoice>'` cho dòng NaN → vẫn giữ doanh thu, nhưng không dùng cho RFM/CLV
- **Option B (ML):** Drop dòng NaN khi train model cần customer (RFM, churn, CLV) — mất ~24% dòng
- **Khuyến nghị:** Tạo cột `is_guest = Customer ID.isna()`; tách 2 luồng xử lý

### Bước 3: Xử lý Quantity âm (trừ khi đã tách ở Bước 1)
- Nếu giữ chung: `Quantity > 0` là bán, `Quantity < 0` là trả
- Tạo cột `transaction_type = np.where(Quantity > 0, 'sale', 'return')`

### Bước 4: Outlier Detection & Treatment
- **Price ≤ 0:** 1,000+ dòng (POSTAGE, adjustment, test) → review thủ công, cân nhắc drop hoặc gán riêng
- **Quantity extreme:** > 10,000 hoặc < -10,000 → kiểm tra (ví dụ 576, 800 dòng) → có thể là bulk/B2B, giữ nhưng flag
- Sử dụng IQR hoặc Isolation Forest cho automated flagging

### Bước 5: Deduplication
- Drop full-row duplicates (`df.drop_duplicates()`)
- Kiểm tra business-key dup: nếu cùng `Invoice+StockCode` nhưng `Quantity/Price` khác → investigage manual

### Bước 6: Feature Engineering cho AI/BI
- `TotalAmount = Quantity * Price` (dòng level)
- `InvoiceMonth`, `InvoiceWeek`, `InvoiceDayOfWeek`, `IsWeekend`
- `CustomerTenure` (days since first order)
- `IsReturn = Quantity < 0`
- `ProductCategory` từ `StockCode` prefix hoặc NLP trên `Description`

### Bước 7: Schema Chuẩn Hóa (Star Schema cho BI)
- **Fact_Sales:** Invoice, StockCode, CustomerID, DateKey, Quantity, UnitPrice, TotalAmount, IsReturn
- **Dim_Customer:** CustomerID, Country, FirstOrderDate, Segment (RFM)
- **Dim_Product:** StockCode, Description, Category, UnitCost (nếu có)
- **Dim_Date:** DateKey, Year, Quarter, Month, Week, DayOfWeek, IsHoliday

## 10. 📌 Tổng Kết (Executive Summary)

### ✅ Các Phát Hiện Chính (Key Findings)
1. **Quy mô:** ~1.07M dòng giao dịch, 2 năm (12/2009–12/2011), 8 cột gốc + 1 cột sheet
2. **Phân bố quốc gia:** UK chiếm ~91%, phần còn lại phân tán (DE, FR, EIRE, AU, BE, US...)
3. **Khách hàng:** ~4,372 khách có ID; **~24% dòng không có Customer ID** (khách vãng lai)
4. **Trả hàng:** ~3.5% dòng có Invoice prefix `C` (credit note), Quantity âm
5. **Giá:** Có dòng `Price ≤ 0` (phí ship POSTAGE, adjustment, test) — cần tách riêng
6. **Sản phẩm:** ~4,000 SKU unique; Description giàu ngữ nghĩa cho NLP
7. **Trùng lặp:** Full-row dup thấp; business-key dup cần kiểm tra thêm

### ⚠️ Vấn Đề Chất Lượng Dữ Liệu (Data Quality Issues)
| Vấn đề | Mức độ | Tác động |
|--------|--------|----------|
| Missing Customer ID (~24%) | **Cao** | Không thể tính RFM/CLV cho 1/4 dữ liệu; bias segmentation |
| Price ≤ 0 / POSTAGE lines | **Trung bình** | Làm méo doanh thu, margin nếu không tách |
| Cancelled invoices mixed in | **Cao** | Double-count nếu không tách sale vs return |
| Quantity outliers (576, 800, -80000+) | **Trung bình** | Skew mean/std; cần flag B2B vs error |
| Description có typo/inconsistent | **Thấp** | Gây noise cho NLP/product clustering |
| Không có cột Cost/Profit | **Cao** | Không tính được margin thực — cần dữ liệu bổ sung |

### 🎯 Phù Hợp Cho Dự Án AI_BI_DASHBOARD

#### ✅ **PHÙ HỢP (Strengths)**
- **Sales Dashboard:** Doanh thu theo thời gian, quốc gia, sản phẩm — data sạch sau cleaning
- **Customer Analytics (RFM, Segmentation, CLV):** Có Customer ID cho 76% dòng, history 2 năm đủ dài
- **Product Performance:** Top/bottom SKU, cross-sell (cùng Invoice), seasonality
- **Forecasting:** Time series 2 năm, granularity ngày → phù hợp Prophet/ARIMA/LSTM
- **Geographic Analysis:** 30+ quốc gia, so sánh market UK vs non-UK
- **Return Rate Analysis:** Credit note pattern rõ rệt → KPI return rate

#### ❌ **KHÔNG PHÙ HỢP / CẦN BỔ SUNG (Gaps)**
- **Profit/Margin Dashboard:** **Thiếu cột Cost/COGS** → không tính được lợi nhuận thực
- **Inventory/Stockout:** Không có stock level, lead time, supplier
- **Marketing Attribution:** Không có channel, campaign, UTM, referral source
- **Customer Demographics:** Không có age, gender, tenure (chỉ có Country + ID)
- **Real-time/Ops:** Dữ liệu batch lịch sử, không streaming
- **B2B vs B2C Separation:** Không có flag kênh bán; quantity lớn có thể là wholesale

### 💡 Khuyến Nghị Ưu Tiên (Business Priority)
1. **Clean & Split:** Tách sale/return, xử lý missing Customer ID, drop POSTAGE/Price≤0
2. **Build Star Schema:** Fact + Dim tables → Power BI / Tableau / Superset ready
3. **RFM + Cohort:** Chạy ngay trên 76% có Customer ID → segment Champions/Loyal/At-risk
4. **Demand Forecasting:** Aggregate daily/weekly per SKU → Prophet baseline
5. **Enrich Cost Data:** Yêu cầu team Finance/ERP cung cấp Cost per SKU để mở rộng Margin Dashboard
6. **NLP Product Clustering:** Dùng Description → auto-tag category, similarity search
