# BÁO CÁO KIỂM ĐỊNH CHẤT LƯỢNG DỮ LIỆU TỔNG HỢP (SYNTHETIC DATA QUALITY AUDIT)

> **Thời gian đánh giá:** 2026-10-07 19:32:08 UTC  
> **Tập dữ liệu kiểm định:** `synthetic_ecommerce` (50,000 bản ghi)  
> **Tập dữ liệu mồi (Seed):** 35,000 bản ghi | **Tập kiểm định độc lập (Holdout):** 15,000 bản ghi  
> **Điểm Tổng hợp (Synthetic Quality Index - SQI):** **`95.78 / 100`** — **Tier A (Excellent)**  
> **Trạng thái Cổng Chất lượng (Quality Gate):** **`PASSED`**  

---

## 1. TỔNG QUAN 4 TRỤ CỘT ĐÁNH GIÁ (QUALITY GATE PILLARS)

| Trụ cột Đánh giá | Trọng số | Điểm số Đạt được | Ngưỡng Đạt | Đánh giá Trạng thái |
|---|:---:|:---:|:---:|:---:|
| **1. Validity (Tính hợp lệ & Ràng buộc logic)** | 30% | **`100.0%`** | >= 95% | [x] ĐẠT |
| **2. Fidelity (Tính trung thực phân phối)** | 30% | **`91.34%`** | >= 80% | [x] ĐẠT |
| **3. Privacy (Tính bảo mật & Chống rò rỉ ID)** | 20% | **`91.88%`** | >= 90% | [x] ĐẠT |
| **4. Utility (Tính hữu ích cho Machine Learning)** | 20% | **`100.0%`** | >= 75% | [x] ĐẠT |
| **TỔNG HỢP (SQI SCORE)** | **100%** | **`95.78 / 100`** | $\ge 80$ | **`PASSED`** |

---

## 2. KẾT QUẢ CHI TIẾT TỪNG TRỤ CỘT

### 2.1. Trụ cột 1: Validity (Tính hợp lệ & Ràng buộc Nghiệp vụ)
* **Tỷ lệ bản ghi hợp lệ 100% invariants:** **`100.0%`** (50,000 / 50,000 bản ghi).
* **Lỗi vi phạm nghiêm trọng (Blocking Errors):** `False`.
* **Chi tiết kiểm định Business Rules:**
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
  - `HR_SALES_001` (Gross Sales Calculation Invariant): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `HR_SALES_002` (Discount Boundary Invariant): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `HR_SALES_003` (Net Sales Calculation Invariant): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `HR_SALES_004` (Positive Line Item Quantity): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `SR_SALES_001` (Platform Fee Boundary): 0 vi phạm (0.0%) — Trạng thái: **WARNING**
  - `HR_PROD_001` (Product Pricing & Cost Invariant): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `SR_PROD_001` (Cost-to-Price Ratio Guard): 0 vi phạm (0.0%) — Trạng thái: **WARNING**
  - `HR_ORD_001` (Payment Value Non-negative): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `HR_ORD_002` (Lifecycle Timestamp Monotonicity): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `HR_FIN_001` (Financial Net Profit Formula Invariant): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `HR_FIN_002` (Marketing Funnel Monotonicity): 0 vi phạm (0.0%) — Trạng thái: **ERROR**
  - `HR_FIN_003` (Non-negative Financial Costs): 0 vi phạm (0.0%) — Trạng thái: **ERROR**

### 2.2. Trụ cột 2: Fidelity (Tính trung thực Phân phối & Tương quan)
* **Điểm tương đồng phân phối số học (KS-Test):** **`96.43%`**.
* **Điểm tương đồng phân phối danh mục (TVD):** **`85.64%`**.
* **Điểm tương đồng ma trận tương quan Pearson:** **`92.54%`**.
* **Số cột được đánh giá:** `29` cột.

### 2.3. Trụ cột 3: Privacy (Tính bảo mật & Nguy cơ Rò rỉ Dữ liệu)
* **Số bản ghi trùng lặp nguyên vẹn (Exact Match):** **`0`** (`0.0%`).
* **Số mã định danh thực tế bị rò rỉ (Real ID Leakage):** **`0`**.
* **Khoảng cách tới bản ghi thực gần nhất (DCR Mean):** **`0.0941`** (Median: `0.0713`, Min: `0.0025`).

### 2.4. Trụ cột 4: Utility (Tính hữu ích khi huấn luyện Mô hình ML)
* **Năng lực dự báo hồi quy (TSTR vs TRTR on `net_sales`):** Tỷ lệ bảo toàn **`99.99%`**.
* **Năng lực phân loại (TSTR vs TRTR on `customer_segment`):** Tỷ lệ bảo toàn **`100.0%`**.

---

## 3. DANH SÁCH VẤN ĐỀ & NHẬN XÉT ĐƯỢC PHÁT HIỆN

1. [Fidelity] Categorical distribution drift on 'city': 63.98% (TVD: 0.3602)
2. [Fidelity] Categorical distribution drift on 'order_approved_at': 0.02% (TVD: 0.9998)

---

## 4. KẾT LUẬN & ĐỀ XUẤT HÀNH ĐỘNG

* **Kết luận:** Bộ dữ liệu tổng hợp `synthetic_ecommerce` đạt **`95.78/100` điểm**, đủ điều kiện vượt qua Cổng Kiểm định Chất lượng (**PASSED**).
* **Lưu ý:** Bộ dữ liệu tổng hợp đảm bảo 100% tính toàn vẹn toán học và an toàn bảo mật thông tin.