# DECISION LOG

## D-EDA-01 — Không impute missing cấu trúc

- `description` và `listing_date` thiếu do card-only crawl không cung cấp đầy đủ.
- Quyết định: giữ missing, không điền median/mode giả tạo.
- Tác động: hai trường này không vào model v1 nếu chưa detail enrichment.

## D-EDA-02 — Xử lý outlier bảo thủ

- Giá và diện tích có phân phối đuôi dài.
- Quyết định: dùng log-scale + IQR theo `property_type`, multiplier 3.0.
- Một dòng chỉ bị loại nếu nhận ít nhất 2 trong 3 cờ: giá, diện tích, giá/m².
- Tác động: giảm nguy cơ xóa listing hợp lệ chỉ vì một đặc điểm cực trị.

## D-EDA-03 — Cải thiện property type nhưng không gán đoán

- Unknown ban đầu: 1.583/6.452.
- Dùng title + URL để tái suy luận chỉ khi nhãn hiện tại là unknown.
- Sau cleaning còn 282 unknown; giữ nguyên thay vì ép nhãn.

## D-EDA-04 — Chính sách leakage

- `price_per_m2`, `price_billion`, `log_price_vnd` được phép dùng cho EDA.
- Các biến trên không được dùng làm X khi target là `price_vnd`.
- Model v1 hiện ưu tiên `area_m2`, `log_area_m2`, `property_type`, `legacy_area`.

## D-EDA-05 — Peer review

- Không tự tạo phản hồi giả.
- `docs/peer_review.md` chỉ được hoàn tất sau khi có review chéo nhóm thực tế.

## D-EDA-06 — Biên giới giữa EDA cleaning và modeling

- Cleaned BT3 là analytical snapshot phục vụ EDA và chuẩn bị feature.
- Các ngưỡng preprocessing nào học từ dữ liệu trong BT4 phải được fit trên train, không fit trên toàn bộ train+test.
- Mục tiêu là tránh data leakage khi chuyển từ EDA sang modeling.
