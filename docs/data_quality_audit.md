# BÁO CÁO ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU (DATA QUALITY AUDIT REPORT)

> **Tập dữ liệu:** `ecommerce_seed.csv`  
> **Thời gian đánh giá:** `2026-10-04T06:51:36.353797` UTC  
> **Trạng thái:** **PASSED**  
> **Điểm chất lượng tổng hợp (DQS):** **`98.31 / 100`** (Tier A (Excellent - Ready for Synthetic Training & Production))  

---

## I. BẢNG ĐIỂM 4 TRỤ CỘT CHẤT LƯỢNG (4-PILLAR QUALITY SCORECARD)

| Trụ cột chất lượng | Trọng số | Điểm đạt được | Đánh giá chi tiết |
|---|:---:|:---:|---|
| **1. Tính đầy đủ (Completeness)** | 25% | **99.92%** | Ô khuyết: 1,089 ô (3 cột có null) |
| **2. Tính duy nhất (Uniqueness)** | 20% | **100.0%** | Trùng lặp dòng: 0 dòng; Trùng lặp PK (`sales_id`): 0 dòng |
| **3. Tính hợp lệ & Ràng buộc (Validity)** | 35% | **100.0%** | Tỷ lệ pass: Sales 100.0%, Products 100.0%, Orders 100.0% (0 lỗi) |
| **4. Sức khỏe ngoại lệ (Outlier Health)** | 20% | **91.66%** | Ngoại lệ cực trị ($3 \times \text{IQR}$): 2.78% tổng số giá trị kiểm tra |

---

## II. KẾT LUẬN & ĐÁNH GIÁ KỸ THUẬT

- **Khả năng sử dụng cho huấn luyện:** Dữ liệu đáp ứng các tiêu chí định lượng (DQS = 98.31/100) để chuyển sang Giai đoạn 2 (Schema Learning & Synthetic Data Generator).
- **Kiểm tra ràng buộc nghiệp vụ:** Toàn bộ quan hệ giữa Doanh thu, Chi phí, Khuyến mãi và Lợi nhuận ròng khớp với công thức xác định trong `semantic/business_rules.py` (0 vi phạm ghi nhận trên tập mẫu).