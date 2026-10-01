# Khảo sát nguồn CafeLand — BQ01

## 1. Entry point

`https://nhadat.cafeland.vn/nha-dat-ban-tai-tp-ho-chi-minh/`

Pagination đã xác nhận theo dạng:

```text
/page-2/
/page-3/
...
```

## 2. Trường quan sát được trên search page

- title
- asking price text
- area text
- current location label
- short description/excerpt
- update text
- listing URL
- seller label (không cần cho model)

Search page thích hợp để thu lượng lớn record với ít request hơn.

## 3. Trường quan sát được trên detail page

- `Mã tài sản`
- `Ngày đăng`
- `Giá bán`
- giá/m² hiển thị
- `Diện tích`
- `Phòng ngủ`
- mô tả
- `Loại địa ốc`
- `Hướng nhà`
- `Số tầng`
- `Số toilet`
- `Đường trước nhà`
- `Số phòng khách`
- `Số phòng ngủ`
- `Pháp lý`
- link bản đồ

Detail enrichment là tùy chọn vì 5.000+ detail requests có thể gây tải không cần thiết.

## 4. Vấn đề kỹ thuật đã phát hiện

### 4.1 Phạm vi TP.HCM hiện tại khác Business Question

CafeLand hiện có thể gắn nhãn TP.HCM cho khu vực trước đây thuộc Bình Dương/
Bà Rịa–Vũng Tàu. Không lọc chỉ bằng city label.

### 4.2 Area không phải lúc nào cũng là cùng một khái niệm

Pilot phát hiện nhà riêng có thể hiển thị tổng diện tích sàn ở trường `Diện tích`,
trong khi mô tả nêu diện tích đất khác. Vì vậy:
- giữ `area_text`;
- tạo `area_m2` nhưng gắn `area_definition_risk`;
- Bài 3 phải kiểm tra theo property type.

### 4.3 Missing

Nhiều trường “Kiến trúc - Tiện ích” có label nhưng value rỗng.

### 4.4 Giá

Có listing giá số và listing “Thương lượng”.
Record “Thương lượng” được giữ ở raw nhưng không dùng làm target.

## 5. Quy tắc crawl có trách nhiệm

- Kiểm tra `robots.txt` trước khi crawl.
- Đọc điều khoản sử dụng.
- Chỉ thu trường cần cho mục đích học thuật.
- Không tải ảnh.
- Không thu/sử dụng số điện thoại, email người đăng.
- Rate-limit + retry/backoff.
- Checkpoint để không request lại khi job gián đoạn.
- Không vượt tải website.

## 6. Rủi ro pháp lý/điều khoản

Điều khoản CafeLand nêu nội dung được bảo vệ và giới hạn việc sao chép/phân phối.
Dataset của nhóm nên:
- dùng nội bộ cho bài học;
- chỉ commit sample nhỏ;
- không public raw production lên GitHub nếu chưa xác định quyền phù hợp;
- public code/schema/insight thay vì phát tán toàn bộ nội dung listing.
