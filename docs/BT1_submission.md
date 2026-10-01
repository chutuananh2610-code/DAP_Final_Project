# BÀI TẬP 1 — Lựa chọn Domain & Định nghĩa Vấn đề

## 1. Domain & case study

- Domain: Bất động sản Việt Nam.
- Case study trung tâm: CafeLand / Nhà Đất CafeLand.
- Phạm vi phân tích: tin **bán** trong ranh giới TP.HCM trước sáp nhập cấp tỉnh 2025.

## 2. Brainstorm 5 câu hỏi theo 5W1H

1. **What:** Đặc điểm nào liên hệ mạnh nhất với giá rao bán BĐS?
2. **Where:** Chênh lệch giá giữa các khu vực/quận-huyện thể hiện như thế nào?
3. **How:** Có thể dự đoán giá từ diện tích, vị trí, loại hình và đặc điểm tài sản không?
4. **When:** Giá và cơ cấu tin đăng có khác theo thời gian đăng không?
5. **Why:** Vì sao cùng diện tích nhưng giá khác mạnh giữa loại hình/khu vực?

## 3. Câu hỏi chính đã chọn

> Dựa trên vị trí, loại hình và các đặc điểm của bất động sản tại TP.HCM,
> có thể ước tính mức giá rao bán hợp lý của một bất động sản hay không?

- Target: `price_vnd`
- Task: regression
- Giá trị thực tế: hỗ trợ tham khảo định giá, so sánh listing và phân tích thị trường.

## 4. Đánh giá tính khả thi

- CafeLand có trang kết quả phân trang và trang chi tiết.
- Search page có title, price, area, location, excerpt, update time, URL.
- Detail page bổ sung listing ID/date, bedrooms và nhóm thuộc tính “Kiến trúc - Tiện ích”.
- Quy mô hiển thị trên trang tìm kiếm lớn hơn rất nhiều ngưỡng 5.000.
- Rủi ro chính: phạm vi TP.HCM mới, trường thiếu, “Thỏa thuận”, area definition, HTML thay đổi.

## 5. Phương án dự phòng

Nguồn bổ sung chỉ kích hoạt nếu CafeLand không đáp ứng:
1. Batdongsan.com.vn
2. Nhatot.com
3. Kaggle/MOSO cho validation/bổ sung

Giai đoạn hiện tại vẫn khóa **CafeLand 100%**.

## 6. Phân công

- Chu Tuấn Anh: crawler + integration.
- Đinh Duy Đức: Pandas/NumPy + quality.
- Dương Trừng Hân: feasibility + validation + docs/QA.

## 7. Elevator pitch

“Nhóm 4 xây dựng một pipeline dữ liệu từ CafeLand để trả lời liệu giá rao bán BĐS
TP.HCM có thể được ước tính từ vị trí, loại hình và đặc điểm tài sản hay không.
Khác với việc chỉ so sánh giá/m², nhóm kiểm soát data leakage, sự thay đổi địa giới
TP.HCM sau 2025 và tính không đồng nhất của diện tích. Kết quả hướng tới một mô hình
hồi quy có thể giải thích và tái lập, phục vụ tham khảo định giá thực tế.”
