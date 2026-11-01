# DESIGN.md — Quy Chuẩn Thiết Kế: Chuẩn Hóa & Tự Động Hóa Dựng Dashboard

Tài liệu này hợp nhất toàn bộ quy chuẩn thiết kế về **Chiến lược màu sắc (Color Strategy)** và **Khung ra quyết định lựa chọn biểu đồ (Chart Selection Decision Framework)**. Đây là căn cứ kỹ thuật bắt buộc để tự động hóa quá trình sinh Dashboard (Automated Dashboard Generation Engine) và xây dựng giao diện người dùng (GUI) trong hệ thống **AI BI Dashboard (v2)**.

---

## Mục Lục (Table of Contents)

- [Phần I: Chiến Lược Màu Sắc (Color Strategy)](#phần-i-chiến-lược-màu-sắc-color-strategy)
  - [1. Nguyên tắc cốt lõi (Core Principles)](#1-nguyên-tắc-cốt-lõi-core-principles)
  - [2. Bảng tra cứu hệ màu chuẩn (Palette Reference Tables)](#2-bảng-tra-cứu-hệ-màu-chuẩn-palette-reference-tables)
  - [3. Chuẩn tiếp cận mù màu (CVD) và độ tương phản WCAG](#3-chuẩn-tiếp-cận-mù-màu-cvd-và-độ-tương-phản-wcag)
  - [4. Quy tắc màu ngữ nghĩa (Semantic Color Rules)](#4-quy-tắc-màu-ngữ-nghĩa-semantic-color-rules)
  - [5. Nền tảng Theme BI & Ánh xạ Token](#5-nền-tảng-theme-bi--ánh-xạ-token)
  - [6. Chiến lược gán màu cho Dashboard (Color Assignment Strategy)](#6-chiến-lược-gán-màu-cho-dashboard-color-assignment-strategy)
  - [7. Bảng màu theo hình thái báo cáo (Archetype Calibration)](#7-bảng-màu-theo-hình-thái-báo-cáo-archetype-calibration)
  - [8. Mẫu hình điểm nhấn nổi bật (Highlight Pattern)](#8-mẫu-hình-điểm-nhấn-nổi-bật-highlight-pattern)
  - [9. Kỹ thuật định dạng có điều kiện (Conditional Formatting)](#9-kỹ-thuật-định-dạng-có-điều-kiện-conditional-formatting)
  - [10. Quy tắc gán màu tổng quát](#10-quy-tắc-gán-màu-tổng-quát)
  - [11. Cây quyết định chọn bảng màu (Palette Selection Tree)](#11-cây-quyết-định-chọn-bảng-màu-palette-selection-tree)
- [Phần II: Khung Quyết Định Chọn Biểu Đồ (Chart Selection Framework)](#phần-ii-khung-quyết-định-chọn-biểu-đồ-chart-selection-framework)
  - [1. Nguyên tắc cốt lõi (Core Principle)](#1-nguyên-tắc-cốt-lõi-core-principle)
  - [2. Ma trận quyết định chính (Primary Decision Matrix)](#2-ma-trận-quyết-định-chính-primary-decision-matrix)
  - [3. Bộ lọc lựa chọn thứ cấp (Secondary Selection Filters)](#3-bộ-lọc-lựa-chọn-thứ-cấp-secondary-selection-filters)
  - [4. Ánh xạ loại biểu đồ (Visual Type Crosswalk)](#4-ánh-xạ-loại-biểu-đồ-visual-type-crosswalk)
  - [5. Khả năng áp dụng theo Archetype](#5-khả-năng-áp-dụng-theo-archetype)
  - [6. Danh sách kiểm tra quyết định (Decision Checklist)](#6-danh-sách-kiểm-tra-quyết-định-decision-checklist)
  - [7. Ánh xạ từ điển trực quan FT (Visual Vocabulary)](#7-ánh-xạ-từ-điển-trực-quan-ft-visual-vocabulary)
  - [8. Giới hạn số lượng danh mục (Cardinality Limits)](#8-giới-hạn-số-lượng-danh-mục-cardinality-limits)
  - [9. Thứ bậc độ chính xác trực quan (Encoding Accuracy Hierarchy)](#9-thứ-bậc-độ-chính-xác-trực-quan-encoding-accuracy-hierarchy)
  - [10. Cây quyết định theo số lượng chuỗi (Series Count Tree)](#10-cây-quyết-định-theo-số-lượng-chuỗi-series-count-tree)
  - [11. Các trường hợp ngoại lệ & Quy tắc biên (Edge Cases)](#11-các-trường-hợp-ngoại-lệ--quy-tắc-biên-edge-cases)
- [Phần III: Quy Tắc Áp Dụng Vào Hệ Thống Tự Động Hóa](#phần-iii-quy-tắc-áp-dụng-vào-hệ-thống-tự-động-hóa)

---

# Phần I: Chiến Lược Màu Sắc (Color Strategy)

## 1. Nguyên tắc cốt lõi (Core Principles)

1. **Họ bảng màu phải khớp với bản chất dữ liệu (Palette family matches data family):** Dùng *sequential* cho dữ liệu thứ bậc/định lượng tăng dần, *diverging* cho dữ liệu phân kỳ âm/dương $(\pm)$, và *categorical* cho dữ liệu danh mục định danh.
2. **Tuyệt đối không dùng màu cầu vồng (Never rainbow on ordered data):** Màu cầu vồng không mang tính trực giác theo trật tự nhận thức; gây méo mó và dẫn dắt sai lệch.
3. **Màu sắc không bao giờ là kênh truyền tải duy nhất (Color is never the sole channel):** Luôn kết hợp màu sắc với hình dạng, nhãn chữ hoặc họa tiết (tuân thủ WCAG 1.4.1).
4. **Giới hạn bảng màu phân loại ở mức 7–8 sắc thái (Cap categorical palettes at 7–8 hues):** Vượt quá ngưỡng này, mắt người không còn phân biệt được sự khác nhau giữa các nhóm.
5. **Tiết chế hiệu quả hơn sặc sỡ (Restraint beats vibrance):** Phần lớn diện tích canvas phải ở tông trung tính; màu sắc chỉ dùng để kéo sự chú ý vào thông tin then chốt.
6. **Độ tương phản là yêu cầu bắt buộc (Contrast is non-negotiable):** Mọi cặp văn bản trên nền phải đạt chuẩn WCAG AA ($\ge 4.5:1$ đối với văn bản thông thường, $\ge 3:1$ đối với văn bản lớn).
7. **Bảo tồn các màu mang ngữ nghĩa (Reserve semantic colors):** Các màu xanh lục, đỏ, vàng hổ phách mang ý nghĩa mặc định mạnh mẽ; không được lãng phí chúng vào mục đích trang trí thuần túy.

---

## 2. Bảng tra cứu hệ màu chuẩn (Palette Reference Tables)

### Bảng màu tuần tự (Sequential Palettes)

| Tên bảng màu | Dải màu Hex (5 mức độ) | An toàn CVD | Trường hợp sử dụng |
|---|---|---|---|
| **Blues** (ColorBrewer) | `#EFF3FF` `#BDD7E7` `#6BAED6` `#3182BD` `#08519C` | ✅ Tất cả | Tuần tự mặc định; thể hiện độ lớn từ thấp đến cao |
| **YlOrRd** (ColorBrewer) | `#FFFFB2` `#FECC5C` `#FD8D3C` `#F03B20` `#BD0026` | ⚠️ Cận Deutan | Mã hóa nhiệt độ / mức độ cấp bách, nóng bỏng |
| **Viridis** | `#440154` `#3B528B` `#21908C` `#5DC863` `#FDE725` | ✅ Tất cả | Độ sáng đồng đều tri giác; an toàn khi in ấn |
| **Cividis** | `#002051` `#3F5B75` `#8E8E52` `#CBBE2D` `#FDEA45` | ✅ Tất cả + thang xám | Lựa chọn tốt nhất cho CVD; chỉ dùng sắc xanh - vàng |

### Bảng màu phân kỳ (Diverging Palettes)

| Tên bảng màu | Thấp $\rightarrow$ Trung tâm $\rightarrow$ Cao | Điểm giữa (Midpoint) | An toàn CVD |
|---|---|---|---|
| **RdBu** | `#B2182B` $\rightarrow$ `#F7F7F7` $\rightarrow$ `#2166AC` | Xám/trắng trung tính | ✅ |
| **BrBG** | `#8C510A` $\rightarrow$ `#F5F5F5` $\rightarrow$ `#01665E` | Xám/trắng trung tính | ✅ |
| **PiYG** | `#C51B7D` $\rightarrow$ `#F7F7F7` $\rightarrow$ `#4D9221` | Xám/trắng trung tính | ⚠️ Cận Protan |

### Bảng màu phân loại (Categorical Palettes)

| Tên bảng màu | Mã màu Hex | Số màu | An toàn CVD |
|---|---|---|---|
| **Okabe-Ito** | `#E69F00` `#56B4E9` `#009E73` `#F0E442` `#0072B2` `#D55E00` `#CC79A7` `#000000` | 8 | ✅ Toàn diện |
| **Set2** (ColorBrewer) | `#66C2A5` `#FC8D62` `#8DA0CB` `#E78AC3` `#A6D854` `#FFD92F` `#E5C494` `#B3B3B3` | 8 | ✅ |
| **Tableau 10** | `#4E79A7` `#F28E2B` `#E15759` `#76B7B2` `#59A14F` `#EDC948` `#B07AA1` `#FF9DA7` `#9C755F` `#BAB0AC` | 10 | ⚠️ Xung đột cặp ở mức 9-10 (Deutan) |

---

## 3. Chuẩn tiếp cận mù màu (CVD) và độ tương phản WCAG

* Bảng màu danh mục ưu tiên số 1 luôn là **Okabe-Ito**.
* Mọi biểu đồ không được sử dụng màu đỏ và xanh lá cây làm yếu tố phân biệt duy nhất (phải có thêm nhãn text hoặc icon).
* Đảm bảo tỷ lệ tương phản tối thiểu:
  * Text thường trên nền: $\ge 4.5:1$.
  * Giao diện UI / icon trạng thái: $\ge 3.0:1$.

---

## 4. Quy tắc màu ngữ nghĩa (Semantic Color Rules)

| Màu sắc | Ý nghĩa mặc định | Quy tắc áp dụng |
|---|---|---|
| **Green (Xanh lục)** | Tốt / Tích cực / Đạt chỉ tiêu | Chỉ dành riêng cho trạng thái có lợi, vượt kế hoạch |
| **Red (Đỏ)** | Xấu / Tiêu cực / Nguy hiểm, báo động | Chỉ dành riêng cho trạng thái bất lợi, cảnh báo nghiêm trọng |
| **Amber/Yellow (Vàng hổ phách)** | Cảnh báo / Tiến sát ngưỡng nguy cơ | Dùng làm vùng đệm trung gian giữa Xanh và Đỏ |
| **Grey (Xám)** | Trung tính / Bối cảnh / Chuẩn đối sánh | Mặc định cho các phần tử không cần nhấn mạnh |
| **Blue (Xanh lam)** | Thông tin / Màu thương hiệu chủ đạo | Mặc định an toàn khi không mang ngữ nghĩa đánh giá tốt/xấu |

**Ràng buộc:**
- Tuyệt đối không đảo ngược ngữ nghĩa (ví dụ: gán xanh = xấu) trừ khi có yêu cầu đặc thù rõ ràng.
- Lưu ý văn hóa: Trong một số thị trường tài chính Đông Á, màu đỏ biểu thị tăng giá/lãi; cần chú thích nếu báo cáo phục vụ thị trường này.

---

## 5. Nền tảng Theme BI & Ánh xạ Token

| Khóa Theme | Mục đích sử dụng | Ghi chú kỹ thuật |
|---|---|---|
| `dataColors` | Danh sách màu định danh cho các chuỗi | 8 màu đầu tiên quyết định tính nhất quán |
| `good` / `neutral` / `bad` | Bộ ba sắc thái cảm xúc | Ánh xạ trực tiếp tới Xanh lục / Xám / Đỏ |
| `firstLevelElements` | Văn bản chính và các điểm dấu chính | Phải đạt chuẩn tương phản 4.5:1 trên canvas |
| `secondLevelElements` | Nhãn trục, phụ đề, văn bản thứ cấp | Đạt tương phản trên nền chính/nền phụ |
| `thirdLevelElements` | Đường lưới (gridlines), đường phân cách | Giữ mức độ hiển thị vừa đủ, không lấn át dữ liệu |
| `fourthLevelElements` | Nhãn mờ, bối cảnh cấp thấp | Chỉ dùng cho thông tin ngữ cảnh phụ trợ |
| `background` | Nền canvas trang | Màu trắng (`#FFFFFF`) hoặc gần trắng (`#FAFBFF`) |
| `secondaryBackground` | Nền card, container phụ | Hơi lệch sắc độ so với background chính |
| `tableAccent` | Đường viền bảng, thanh phân cách | Giữ cấu trúc bảng mạch lạc |

---

## 6. Chiến lược gán màu cho Dashboard (Color Assignment Strategy)

Gán màu theo trang sao cho các thành phần trực quan được **liên kết về mặt thị giác khi chia sẻ cùng một độ đo (measure)** và **khác biệt khi đo lường các khía cạnh khác nhau**.

### Các quy tắc thực thi:

1. **Cùng độ đo $\rightarrow$ Cùng màu sắc (Same measure $\rightarrow$ same color):**
   * Nếu thẻ KPI hiển thị "Tổng Doanh thu" với thanh màu Sky Blue (`#56B4E9`), thì biểu đồ đường (Line chart) thể hiện xu hướng Doanh thu cũng **bắt buộc phải dùng màu Sky Blue**. Điều này tạo ra sự kết nối nhận thức tức thì.
2. **Phân rã một độ đo $\rightarrow$ Dải Gradient của màu đó (Breakdown of a measure $\rightarrow$ gradient of that color):**
   * Biểu đồ cột hiển thị Doanh thu *theo Nhóm sản phẩm* sẽ dùng dải gradient từ nhạt $\rightarrow$ đậm của màu Sky Blue. Gradient vừa gắn kết dữ liệu với độ đo cha, vừa củng cố trực quan thứ tự sắp xếp giá trị.
3. **Độ đo khác nhau $\rightarrow$ Màu sắc khác nhau (Different measure $\rightarrow$ different hue):**
   * Biểu đồ hiển thị Số đơn hàng theo Tỉnh/Thành sẽ dùng một màu khác trong mảng `dataColors` so với màu của biểu đồ Doanh thu.
4. **Các thẻ KPI tiêu thụ slot màu trước tiên:**
   * Theo thứ tự đọc từ trên xuống dưới, từ trái sang phải. Biểu đồ chi tiết sẽ kế thừa hoặc lấy slot màu tiếp theo còn trống.
5. **Nhãn dữ liệu trên biểu đồ:** Luôn dùng màu xám đậm trung tính (`#252423`), không dùng màu accent để tránh gây rối mắt.

### Ví dụ minh họa (4 Thẻ KPI + 3 Biểu đồ trên một màn hình):

| Thành phần trực quan | Độ đo hiển thị | Màu sắc áp dụng | Nguồn gốc |
|---|---|---|---|
| Card 1: Tổng Sự kiện | Số lượng (count) | `#D55E00` | Slot 0 |
| Card 2: Tổng Doanh thu | Doanh thu (revenue) | `#56B4E9` | Slot 1 |
| Card 3: Khách hàng mới | Số lượng (count) | `#009E73` | Slot 2 |
| Card 4: Tỷ lệ hoàn thành | Tỷ lệ (rate) | `#0072B2` | Slot 3 |
| Line: Doanh thu theo thời gian | Tổng Doanh thu | `#56B4E9` | **Trùng màu Card 2** |
| Bar: Doanh thu theo Loại SP | Phân rã Doanh thu | Gradient `#56B4E9` | **Gradient từ Card 2** |
| Bar: Sự kiện theo Quốc gia | Phân rã Sự kiện | Gradient `#D55E00` | **Gradient từ Card 1** |

---

## 7. Bảng màu theo hình thái báo cáo (Archetype Calibration)

| Hình thái (Archetype) | Chiến lược bảng màu | Số lượng màu điển hình |
|---|---|---|
| **Executive (Điều hành)** | 3 màu ngữ nghĩa (xanh/vàng/đỏ) + 1 màu thương hiệu + xám | Tối đa 5 màu |
| **Operational (Vận hành)** | Bộ ba RAG (đỏ/vàng/xanh) + xám trạng thái + 1 màu highlight | Tối đa 5 màu |
| **Analytical (Phân tích)** | Toàn bộ bảng Okabe-Ito hoặc Set2 + bảng sequential cho heatmap | Lên tới 8 màu |
| **Narrative (Kể chuyện)** | 1 màu điểm nhấn nổi bật + xám bối cảnh | 2–3 màu |
| **Comparative (So sánh)** | Bảng phân kỳ (RdBu) hoặc cặp màu định danh | 4–6 màu |

---

## 8. Mẫu hình điểm nhấn nổi bật (Highlight Pattern)

Sử dụng màu bão hòa để tập trung ánh nhìn vào điểm dữ liệu then chốt, đồng thời chuyển toàn bộ các dữ liệu bối cảnh còn lại sang sắc xám mờ:

| Phần tử | Cách xử lý màu sắc | Ví dụ |
|---|---|---|
| **Cột/Đường được làm nổi bật** | Màu bão hòa (thương hiệu hoặc ngữ nghĩa) | `#3182BD` (Xanh) hoặc `#E15759` (Đỏ) |
| **Các cột/đường bối cảnh còn lại** | Màu xám nhạt trung tính | `#D9D9D9` hoặc `#E0E0E0` |
| **Đường tham chiếu chuẩn (Baseline)** | Màu xám vừa, nét đứt 1px | `#999999` nét gạch đứt |
| **Nền canvas** | Trắng hoặc gần trắng | `#FFFFFF` |

---

## 9. Kỹ thuật định dạng có điều kiện (Conditional Formatting)

| Kỹ thuật | Áp dụng trên | Hiệu ứng trực quan |
|---|---|---|
| **Màu theo chuỗi (Per-series color)** | Biểu đồ cột / thanh | Mỗi thanh một màu khi định danh danh mục là thông điệp chính |
| **Màu theo ngưỡng (Threshold color)** | Thẻ KPI | Nền hoặc chữ đổi màu dựa trên ngưỡng Đạt / Cảnh báo / Nguy cơ |
| **Thanh dữ liệu (Data bars)** | Cột số trong bảng dữ liệu | Vẽ thanh ngang mini trong cell thể hiện ngay độ lớn |
| **Bộ Icon trạng thái (Icon sets)** | Cột trạng thái bảng | Icon đạt/hỏng hoặc tốt/cảnh báo giúp quét nhanh thông tin |
| **Gradient màu ô (Color gradient)** | Ma trận, Heatmap | Thang màu Min $\rightarrow$ Mid $\rightarrow$ Max làm lộ rõ quy luật dữ liệu |
| **Điểm nhấn + Xám (Highlight + grey)** | Mọi biểu đồ | 1 chuỗi dùng màu accent, các chuỗi còn lại dùng `#BDBDBD` |

---

## 10. Quy tắc gán màu tổng quát

1. **Nhất quán xuyên suốt:** Cùng một danh mục phải giữ nguyên một mã màu trên toàn bộ các trang và biểu đồ của hệ thống.
2. **Ưu tiên màu ngữ nghĩa:** Nếu một danh mục mang bản chất ngữ nghĩa nội tại (ví dụ: "Critical", "Thất bại"), ưu tiên dùng màu ngữ nghĩa tương ứng trước.
3. **Thứ tự theo bảng màu:** Chuỗi đầu tiên lấy màu index 0; không nhảy cóc qua các index.
4. **Chú giải (Legend) = Thứ tự hiển thị:** Trật tự trong legend phải khớp đúng trật tự xuất hiện của các phần tử đồ họa trên biểu đồ.
5. **Tiết chế định dạng có điều kiện:** Chỉ áp dụng cho cảnh báo ngưỡng, heatmap hoặc đèn giao thông (RAG).
6. **Không dùng màu để trang trí thuần túy:** Mỗi màu sắc xuất hiện trên màn hình đều phải mã hóa một thông tin cụ thể.

---

## 11. Cây quyết định chọn bảng màu (Palette Selection Tree)

```text
Dữ liệu thuộc loại nào?
├── Định danh / Phân loại (Nominal / Categorical - không có trật tự)
│   ├── ≤8 danh mục → Dùng bảng Okabe-Ito hoặc Set2
│   └── >8 danh mục → Gom phần dư vào nhóm "Khác"; giới hạn ở 7–8 sắc thái
├── Thứ bậc / Tuần tự (Ordinal / Sequential - từ thấp đến cao)
│   ├── Cần đảm bảo an toàn tuyệt đối cho người mù màu → Dùng Cividis hoặc Viridis
│   └── Tiêu chuẩn thông thường → Dùng Blues (ColorBrewer)
├── Phân kỳ (Diverging - lệch âm/dương quanh điểm cân bằng 0)
│   ├── Cần an toàn CVD cao → Dùng BrBG
│   └── Tiêu chuẩn thông thường → Dùng RdBu
└── Ngữ nghĩa trạng thái (Semantic - đánh giá tốt/xấu/nguy cơ)
    └── Sử dụng bộ ba trạng thái: Good (Xanh) / Neutral (Xám) / Bad (Đỏ)
```

---

# Phần II: Khung Quyết Định Chọn Biểu Đồ (Chart Selection Framework)

## 1. Nguyên tắc cốt lõi (Core Principle)

> **"Hãy chọn biểu đồ trả lời trực tiếp cho CÂU HỎI của người dùng, không chọn theo kiểu dữ liệu."**

Mỗi biểu đồ sinh ra phải trả lời một trong các câu hỏi phân tích cốt lõi: *So sánh (Comparison), Cơ cấu (Composition), Phân phối (Distribution), Mối quan hệ (Relationship), Xu hướng (Trend), Thứ hạng (Ranking), Độ lệch (Deviation), Dòng chảy (Flow)* hoặc *Chỉ số đơn lẻ (Status/Single KPI)*.

---

## 2. Ma trận quyết định chính (Primary Decision Matrix)

| Mục đích phân tích | Lựa chọn ưu tiên | Khi nào nên dùng | Lựa chọn thay thế | Tuyệt đối tránh |
|---|---|---|---|---|
| **So sánh (Comparison)** | Horizontal bar (Thanh ngang) | $\ge 7$ mục hoặc nhãn tên dài | Clustered bar, Dot plot | Biểu đồ tròn (Pie), Biểu đồ 3D |
| **Cơ cấu (Composition)** | 100% Stacked bar, Treemap | Thể hiện các phần trong một tổng thể | Waterfall (phân tích cộng dồn) | Pie có $> 5$ lát cắt |
| **Phân phối (Distribution)** | Histogram, Box plot | Hình dạng phân bố và độ phân tán | Violin, Jitter plot | Dùng 1 cột đơn thể hiện giá trị trung bình |
| **Mối quan hệ (Relationship)**| Scatter plot (Điểm phân tán) | Kiểm định tương quan / cụm dữ liệu | Bubble chart (thêm biến thứ 3) | Biểu đồ đường 2 trục tung (Dual-axis line) |
| **Xu hướng (Trend)** | Line chart (Đường) | Trục thời gian liên tục, $\ge 7$ mốc | Column chart ($\le 6$ mốc thời gian) | Đường cong làm mịn che giấu biến động thực |
| **Thứ hạng (Ranking)** | Sorted horizontal bar | Nhấn mạnh Top-N / Bottom-N | Lollipop chart | Các thanh không được sắp xếp thứ tự |
| **Độ lệch (Deviation)** | Diverging bar (Thanh phân kỳ) | Biến động $\pm$ so với mốc tham chiếu | Bullet graph, Waterfall | Dùng cột thường với baseline tùy tiện |
| **Dòng chảy (Flow)** | Sankey diagram | Chuyển dịch qua các giai đoạn/kênh | Funnel (phễu thu hẹp đơn điệu) | Sankey cho các dòng chảy quá nhỏ |
| **Chỉ số đơn (Single KPI)** | Compact card + sparkline/context | Đọc nhanh chỉ số điều hành quan trọng | Bullet graph (so với mục tiêu) | Đồng hồ đo (Gauge) hoặc Card khổng lồ trơ trọi |
| **Địa lý (Geospatial)** | Bản đồ ký hiệu / Choropleth | Phân bố không gian mang thông điệp cốt lõi | Sorted bar (nếu chỉ xếp hạng quốc gia) | Bản đồ bong bóng thiếu chú giải kích cỡ |

---

## 3. Bộ lọc lựa chọn thứ cấp (Secondary Selection Filters)

| Bộ lọc | Quy tắc áp dụng |
|---|---|
| **Độ chính xác vs Mẫu hình** | Cần số liệu chính xác từng dòng $\rightarrow$ Dùng Bảng/Ma trận. Cần nhìn xu hướng/hình dạng $\rightarrow$ Dùng Biểu đồ. |
| **Số lượng biến (Cardinality)** | $> 15$ danh mục $\rightarrow$ Bắt buộc gom nhóm / lọc Top-N. Tuyệt đối không vẽ 40 thanh bar trên một biểu đồ. |
| **Số phần tử cơ cấu** | $\le 5$ phần tử $\rightarrow$ Donut/Pie; $6–15$ phần tử $\rightarrow$ Sorted Bar; $> 15$ phần tử $\rightarrow$ Treemap. |
| **Độ chênh lệch độ lớn** | Chênh lệch giá trị $> 100\times$ $\rightarrow$ Tách riêng thành 2 biểu đồ hoặc dùng thang Log. Không để 1 cột đè bẹp các cột khác. |
| **Khác biệt đơn vị đo** | Doanh thu (\$) vs Số lượng (#) $\rightarrow$ Tách thành 2 biểu đồ riêng biệt. Tuyệt đối không gộp chung bằng 2 trục tung (dual-axis). |
| **Tâm lý người dùng** | Cấp lãnh đạo: Card + 1 biểu đồ Hero duy nhất. Chuyên viên phân tích: Chấp nhận Scatter plot, Box plot, Ma trận chi tiết. |
| **Mật độ dữ liệu** | Dữ liệu thưa $\rightarrow$ Dot plot, Strip. Dữ liệu dày đặc $\rightarrow$ Histogram, Hex-bin scatter. |

---

## 4. Ánh xạ loại biểu đồ (Visual Type Crosswalk)

| Mục đích | Loại trực quan đề xuất (PBI / Web SVG) | Ghi chú kỹ thuật |
|---|---|---|
| So sánh danh mục | `barChart` (Ngang) | Đặt hướng ngang (`orientation: horizontal`) để nhãn không bị chéo |
| So sánh nhóm | `clusteredBarChart` | Giới hạn tối đa 2–3 chuỗi con |
| Cơ cấu tỷ trọng | `hundredPercentStackedBarChart`, `treemap` | Treemap phù hợp khi có phân cấp dữ liệu |
| Phân phối | `histogram` (chia khoảng binning) | Hiển thị tần suất phân bố |
| Tương quan | `scatterChart` | Thể hiện 2 biến số định lượng |
| Xu hướng dài hạn | `lineChart` | Trục thời gian liên tục $\ge 7$ điểm |
| Xu hướng ngắn hạn | `columnChart` | Tối đa $\le 6$ chu kỳ thời gian rời rạc |
| Thứ hạng | `barChart` sắp xếp giảm dần | Luôn áp dụng sắp xếp theo giá trị (`sortBy value desc`) |
| Biến động âm dương | `divergingBarChart` | Cần định dạng có điều kiện quanh mốc 0 |
| Thẻ chỉ số | `cardVisual` | Kết hợp thẻ giá trị lớn với sparkline mini |
| Bảng chi tiết | `tableEx`, `pivotTable` | Dùng khi người dùng cần đối soát con số chính xác |

---

## 5. Khả năng áp dụng theo Archetype

| Hình thái | Biểu đồ ưu tiên | Biểu đồ chấp nhận được | Biểu đồ cấm kỵ |
|---|---|---|---|
| **Executive** | Thẻ KPI, Biểu đồ Hero đơn (Line/Bar), Bullet | Waterfall, Treemap | Scatter plot, Box plot, Histogram, Ma trận rối |
| **Operational** | Thẻ KPI + Sparkline xu hướng, Bảng RAG | Bar chart, Funnel | Scatter plot, Sankey phức tạp |
| **Analytical** | Scatter, Histogram, Box plot, Small Multiples, Ma trận | Mọi biểu đồ có mục đích rõ ràng | Đồng hồ đo (Gauge), 3D, Pie chart rối |
| **Narrative** | Đường xu hướng có chú thích điểm uốn, Waterfall | Slope chart | Biểu đồ đa chuỗi quá nhiều đường giao cắt |
| **Comparative**| Small multiples, Grouped bar, Slope chart | Scatter plot phân cụm màu | Stacked bar thông thường để so sánh độ lớn |

---

## 6. Danh sách kiểm tra quyết định (Decision Checklist)

Trước khi hệ thống quyết định loại biểu đồ cần sinh ra, phải tự động kiểm tra 7 câu hỏi:

1. **Biểu đồ này trả lời câu hỏi cụ thể nào?** — Phát biểu thành một câu đơn rõ nghĩa.
2. **Loại biểu đồ này có phải là cách mã hóa trực tiếp nhất cho câu trả lời không?** — Đối chiếu với Ma trận quyết định.
3. **Số lượng danh mục có vượt ngưỡng không?** — Bar $\le 15$, Pie $\le 5$, Line $\le 5$ chuỗi, Small multiples $\le 16$ bảng.
4. **Trục cơ sở (Baseline) có trung thực không?** — Mọi biểu đồ Bar/Column **bắt buộc phải bắt đầu từ số 0**.
5. **Có thể dùng một giải pháp đơn giản hơn không?** — Nếu một thẻ KPI đã trả lời trọn vẹn, không cần vẽ biểu đồ cồng kềnh.
6. **Hình thái giao diện có cho phép loại biểu đồ này không?** — Báo cáo Executive không vẽ Scatter plot.
7. **Người dùng có thể giải mã thông tin trong dưới 5 giây không?** — Nếu không, phải tinh gọn hoặc tách đôi biểu đồ.

---

## 7. Ánh xạ từ điển trực quan FT (Visual Vocabulary)

| Nhóm danh mục FT | Biểu đồ khuyến nghị |
|---|---|
| **Độ lệch (Deviation)** | Diverging bar, Waterfall |
| **Tương quan (Correlation)** | Scatter plot, Bubble chart |
| **Thứ hạng (Ranking)** | Sorted horizontal bar, Lollipop chart |
| **Phân phối (Distribution)** | Histogram (binned column), Box plot |
| **Biến đổi theo thời gian** | Line chart, Column chart ($\le 6$ kỳ) |
| **Thành phần tổng thể** | Treemap, 100% stacked bar, Donut ($\le 5$ phần) |
| **Độ lớn (Magnitude)** | Horizontal bar, Paired bar |
| **Không gian (Spatial)** | Bản đồ ký hiệu / Bản đồ vùng |
| **Dòng chảy (Flow)** | Sankey, Funnel |

---

## 8. Giới hạn số lượng danh mục (Cardinality Limits)

| Loại biểu đồ | Giới hạn Danh mục | Giới hạn Chuỗi | Hành vi xử lý khi vượt ngưỡng |
|---|---|---|---|
| **Horizontal bar** | 15–20 | 1 (tốt nhất), 2–3 (ghép cụm) | Cuộn trang hoặc tự động gom phần dư vào nhóm "Khác" |
| **Clustered bar** | 10 | 2–3 chuỗi | Vượt quá 3 chuỗi $\rightarrow$ Chuyển sang Small Multiples |
| **Line chart** | n/a (trục liên tục) | Tối đa 5 đường | Vượt quá 5 đường $\rightarrow$ Rối loạn (Spaghetti chart), cần lọc Top-N |
| **Pie / Donut** | **Tối đa 5 lát cắt** | 1 chuỗi | Vượt quá 5 lát $\rightarrow$ Chuyển sang Horizontal Bar |
| **Scatter plot** | Hàng trăm điểm | 3–5 nhóm màu | Quá 5 nhóm $\rightarrow$ Tách nhỏ thành nhiều ô (Facets) |
| **Treemap** | 20–30 ô gạch | 1–2 cấp phân tầng | Quá nhiều tầng lồng nhau sẽ gây khó đọc |
| **Small multiples**| 4–16 bảng con | 1 chuỗi mỗi bảng | Quá 16 bảng $\rightarrow$ Quá tải nhận thức |
| **Bảng dữ liệu** | Không giới hạn dòng | 5–8 cột hiển thị | Cuộn ngang hoặc ẩn các cột phụ |
| **Thẻ KPI (Card)** | 1 giá trị | 1 độ đo | Mỗi thẻ chỉ tập trung vào 1 chỉ số duy nhất |

---

## 9. Thứ bậc độ chính xác trực quan (Encoding Accuracy Hierarchy)

Theo các thí nghiệm nhận thức thị giác của *Cleveland & McGill*, mức độ chính xác khi mắt người giải mã các kênh đồ họa giảm dần theo thứ tự:

| Thứ hạng | Kênh mã hóa trực quan | Mức độ chính xác | Phù hợp nhất cho |
|---|---|---|---|
| **1** | Vị trí trên cùng một trục chuẩn (Position on common scale) | ★★★★★ | Bar chart, Dot plot, Scatter plot |
| **2** | Vị trí trên trục không thẳng hàng (Position on non-aligned scale) | ★★★★ | Small multiples (chia sẻ chung dải trục) |
| **3** | Độ dài (Length) | ★★★★ | Bar chart (độ dài thanh tương ứng với giá trị) |
| **4** | Hướng / Độ dốc (Direction / Slope) | ★★★ | Line chart (độ dốc thể hiện tốc độ tăng/giảm) |
| **5** | Góc (Angle) | ★★ | Pie chart — lý do tại sao biểu đồ tròn kém chính xác |
| **6** | Diện tích (Area) | ★★ | Bubble chart, Treemap |
| **7** | Thể tích (Volume / 3D) | ★ | Biểu đồ 3D — **Tuyệt đối cấm sử dụng** |
| **8** | Độ bão hòa / Sắc thái màu | ★ | Heatmap (nhận diện quy luật mẫu, không dùng cho độ chính xác) |

---

## 10. Cây quyết định theo số lượng chuỗi (Series Count Tree)

```text
Có bao nhiêu chuỗi dữ liệu (Data Series)?
├── 1 chuỗi dữ liệu
│   ├── Giá trị đơn lẻ → Thẻ KPI (Card)
│   ├── Biến thiên theo thời gian → Biểu đồ đường (Line chart)
│   └── So sánh giữa các danh mục → Biểu đồ thanh ngang sắp xếp (Sorted bar)
├── 2–3 chuỗi dữ liệu
│   ├── Cùng chung đơn vị đo → Clustered bar hoặc Multi-line chart
│   └── Khác đơn vị đo → Tách thành các biểu đồ riêng (KHÔNG dùng trục kép)
├── 4–5 chuỗi dữ liệu
│   ├── Trọng tâm là so sánh → Dùng Small Multiples
│   └── Trọng tâm là cơ cấu → Dùng Stacked Bar (100%)
└── 6+ chuỗi dữ liệu
    ├── Tự động gom nhóm thành "Top 5 + Khác"
    └── Hoặc phân tách thành lưới Small Multiples
```

---

## 11. Các trường hợp ngoại lệ & Quy tắc biên (Edge Cases)

| Tình huống | Quy tắc mặc định | Ngoại lệ được chấp thuận | Điều kiện áp dụng |
|---|---|---|---|
| **Trục cơ sở của biểu đồ Bar** | Luôn luôn bắt đầu từ 0 | Không có ngoại lệ | Cột/thanh cắt gốc tọa độ gây bóp méo thị giác |
| **Trục cơ sở của biểu đồ Line** | Bắt đầu từ 0 | Có thể cắt trục (Non-zero) | Khi phân tích biến động tương đối nhỏ của chuỗi dài |
| **Biểu đồ tròn (Pie chart)** | Tránh sử dụng | Chấp nhận được | Chỉ khi $\le 5$ lát, ghi rõ nhãn tỷ lệ %, câu hỏi là phần trăm tổng thể |
| **Biểu đồ miền (Area chart)** | Tránh sử dụng (gây hiểu nhầm thể tích) | Chấp nhận được | Khi thể hiện cấu phần tích lũy qua thời gian, $\le 3$ chuỗi |
| **Trục tung kép (Dual axis)** | Tuyệt đối cấm | Chấp nhận có điều kiện | Chỉ khi cả 2 chuỗi chia sẻ cùng một đơn vị đo lường |
| **Biểu đồ 3D** | **Tuyệt đối cấm** | Không có ngoại lệ | Làm sai lệch góc nhìn và khoảng cách thị giác |
| **Sắp xếp thứ tự các thanh** | Luôn xếp giảm dần theo giá trị | Sắp xếp theo trật tự tự nhiên | Khi danh mục có thứ bậc sẵn (tháng 1, 2, 3... hoặc các giai đoạn phễu) |
| **Đường cong làm mịn (Smoothed)**| Tránh sử dụng | Chấp nhận được | Khi biểu diễn đường trung bình động (Moving Average) có nhãn rõ |

---

# Phần III: Quy Tắc Áp Dụng Vào Hệ Thống Tự Động Hóa

Khi module `backend/dashboard_engine/chart_generator.py` và giao diện `Frontend/` sinh biểu đồ tự động, hệ thống phải tuân thủ nghiêm ngặt:

1. **Bộ lọc Cardinality tự động:**
   * Nếu dữ liệu danh mục có $> 5$ phần tử: Cấm sinh `pie`. Tự động chuyển hướng sang `horizontal_bar` có `sortBy value desc`.
   * Nếu danh mục $> 8$ phần tử: Tự động gom Top 7 và nhóm thứ 8 là `"Khác (Other)"`.
2. **Gán màu sắc theo quy tắc "Same measure $\rightarrow$ Same color":**
   * Chỉ số chính Doanh thu: Luôn dùng màu `#56B4E9` (Sky Blue) từ thẻ KPI cho tới biểu đồ Trend.
   * Phân rã Doanh thu: Dùng gradient dải đơn sắc từ nhạt đến đậm của `#56B4E9`.
3. **An toàn trực quan:**
   * Mọi nhãn dữ liệu trục tọa độ: Dùng màu trung tính tối (`#252423`), không dùng màu accent.
   * Toàn bộ thanh Bar có gốc trục $Y = 0$.

