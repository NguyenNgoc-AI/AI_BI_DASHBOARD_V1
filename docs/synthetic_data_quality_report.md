# BÁO CÁO KIỂM ĐỊNH CHẤT LƯỢNG DỮ LIỆU TỔNG HỢP (SYNTHETIC DATA QUALITY AUDIT)

> **Thời gian đánh giá:** 2026-10-04 08:11:24 UTC  
> **Tập dữ liệu kiểm định:** `synthetic_ecommerce` (50,000 bản ghi)  
> **Tập dữ liệu mồi (Seed):** 35,000 bản ghi | **Tập kiểm định độc lập (Holdout):** 15,000 bản ghi  
> **Điểm Tổng hợp (Synthetic Quality Index - SQI):** **`98.58 / 100`** — **Tier A (Excellent)**  
> **Trạng thái Cổng Chất lượng (Quality Gate):** **`PASSED`**  

---

## 1. TỔNG QUAN 4 TRỤ CỘT ĐÁNH GIÁ (QUALITY GATE PILLARS)

| Trụ cột Đánh giá | Trọng số | Điểm số Đạt được | Ngưỡng Đạt | Đánh giá Trạng thái |
|---|:---:|:---:|:---:|:---:|
| **1. Validity (Tính hợp lệ & Ràng buộc logic)** | 30% | **`100.0%`** | >= 95% | [x] ĐẠT |
| **2. Fidelity (Tính trung thực phân phối)** | 30% | **`96.33%`** | >= 80% | [x] ĐẠT |
| **3. Privacy (Tính bảo mật & Chống rò rỉ ID)** | 20% | **`100.0%`** | >= 90% | [x] ĐẠT |
| **4. Utility (Tính hữu ích cho Machine Learning)** | 20% | **`98.41%`** | >= 75% | [x] ĐẠT |
| **TỔNG HỢP (SQI SCORE)** | **100%** | **`98.58 / 100`** | $\ge 80$ | **`PASSED`** |

---

## 2. KẾT QUẢ CHI TIẾT TỪNG TRỤ CỘT

### 2.1. Trụ cột 1: Validity (Tính hợp lệ & Ràng buộc Nghiệp vụ)
* **Tỷ lệ bản ghi hợp lệ 100% invariants:** **`100.0%`** (50,000 / 50,000 bản ghi).
* **Lỗi vi phạm nghiêm trọng (Blocking Errors):** `False`.
* **Chi tiết kiểm định 11 Business Rules:**
  - `BR_SALES_001` (Gross Sales Calculation Invariant): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `BR_SALES_002` (Discount Boundary Invariant): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `BR_SALES_003` (Net Sales Calculation Invariant): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `BR_SALES_004` (Positive Line Item Quantity): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `BR_SALES_005` (Platform Fee Boundary): 0 vi phạm (0.0%) — Trạng thái: **WARNING**
  - `BR_PROD_001` (Product Pricing & Cost Invariant): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `BR_PROD_002` (Cost-to-Price Ratio Guard): 0 vi phạm (0.0%) — Trạng thái: **WARNING**
  - `BR_ORD_001` (Payment Value Non-negative): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `BR_ORD_002` (Lifecycle Timestamp Monotonicity): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `BR_ORD_003` (Delivered Status Completeness): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `BR_FIN_001` (Financial Net Profit Formula Invariant): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `BR_FIN_002` (Marketing Funnel Monotonicity): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `BR_FIN_003` (Non-negative Financial Costs): 0 vi phạm (0.0%) — Trạng thái: **ERROR**

### 2.2. Trụ cột 2: Fidelity (Tính trung thực Phân phối & Tương quan)
* **Điểm tương đồng phân phối số học (KS-Test):** **`96.85%`**.
* **Điểm tương đồng phân phối danh mục (TVD):** **`95.87%`**.
* **Điểm tương đồng ma trận tương quan Pearson:** **`96.09%`**.
* **Số cột đạt chuẩn:** `27` đạt / `28` cột kiểm định.

### 2.3. Trụ cột 3: Privacy (Tính bảo mật & Nguy cơ Rò rỉ Dữ liệu)
* **Số bản ghi trùng lặp nguyên vẹn (Exact Match):** **`0`** (`0.0%`).
* **Số mã định danh thực tế bị rò rỉ (Real ID Leakage):** **`0`**.
* **Khoảng cách tới bản ghi thực gần nhất (DCR 5th Percentile):** **`0.0292`** (Median: `0.0682`, Min: `0.0056`).
* **Cảnh báo học vẹt (Memorization Detected):** `False`.
* **Mức độ rủi ro bảo mật:** **`LOW`**.

### 2.4. Trụ cột 4: Utility (Tính hữu ích khi huấn luyện Mô hình ML)
* **Năng lực dự báo hồi quy (TSTR Regression vs TRTR on `net_profit`):** Tỷ lệ bảo toàn **`96.82%`**.
* **Năng lực phân loại (TSTR Classification vs TRTR on `customer_segment`):** Tỷ lệ bảo toàn **`99.99%`**.

---

## 3. DANH SÁCH VẤN ĐỀ & NHẬN XÉT ĐƯỢC PHÁT HIỆN (FINDINGS & ISSUES)

1. [Fidelity] Categorical frequency mismatch on 'city': TVD=0.3487 (Similarity: 65.13%).

---

## 4. KẾT LUẬN & ĐỀ XUẤT HÀNH ĐỘNG

* **Kết luận:** Bộ dữ liệu tổng hợp `synthetic_ecommerce` đạt **`98.58/100` điểm**, đủ điều kiện vượt qua Cổng Kiểm định Chất lượng (**PASSED**).
* **Lưu ý:** Bộ dữ liệu tổng hợp đã được lưu trữ an toàn, đảm bảo 100% tính toàn vẹn toán học và bảo mật thông tin.