# Quy tắc phạm vi — TP.HCM trước sáp nhập cấp tỉnh 2025

## Vấn đề

Trang CafeLand hiện tại có thể hiển thị các phường/xã thuộc TP.HCM mới sau sắp xếp cấp tỉnh.
Trong khi Business Question của nhóm chọn phạm vi **TP.HCM cũ**.

Vì vậy, không được lọc chỉ bằng chuỗi `TP. Hồ Chí Minh`.

## Quy tắc pipeline

Record được xác nhận thuộc scope nếu:

1. `location_text` chứa một đơn vị hiện hành hình thành từ địa bàn TP.HCM cũ trong
   `docs/hcm_pre2025_scope_map.json`; hoặc
2. title/description chứa quận/huyện cũ rõ ràng, ví dụ `Quận 1`, `Q10`, `Hóc Môn`,
   `Bình Chánh`, `TP Thủ Đức`.

Nếu hai nguồn mâu thuẫn:
- giữ raw;
- gắn `scope_status = conflict`;
- không đưa vào processed cho đến khi kiểm tra.

Nếu không xác định:
- `scope_status = unresolved`;
- không tự suy diễn;
- loại khỏi modeling dataset.

## Nguồn xây whitelist

Whitelist được xây từ Nghị quyết 1685/NQ-UBTVQH15 năm 2025, dùng các đơn vị mới
hình thành từ địa bàn TP.HCM trước sáp nhập cấp tỉnh. Đây là lớp kiểm soát để tránh
lấy nhầm các khu vực thuộc Bình Dương/Bà Rịa–Vũng Tàu trước sáp nhập.
