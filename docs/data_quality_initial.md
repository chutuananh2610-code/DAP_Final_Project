# Initial Data Quality Report — Verified Pilot

> **Cảnh báo:** báo cáo này chỉ mô tả pilot 13 record, không đại diện cho dataset production.

## Kết quả

- Rows: **13**
- Columns sau normalize: **20**
- Duplicate listing ID: **0**
- Scope status: `{'confirmed_by_current_ward': 12, 'conflict': 1}`
- Area-definition risk flags: **1**

## Vấn đề đã phát hiện

1. `area_m2` có thể là tổng diện tích sàn ở một số nhà riêng.
2. Text/location hiện tại đôi khi không đủ để suy ra quận cũ; cần scope whitelist + text fallback.
3. Một số bedrooms chỉ nằm trong title/description, không có value ở structured field.
4. Giá có nhiều kiểu định dạng; parser phải hỗ trợ `tỷ`, `triệu`, số dài và `Thương lượng`.
5. Raw text có thể chứa trực tiếp giá → không dùng title/description cho model v1.

## Quyết định chuyển sang Bài 3

- Không hard-code outlier threshold ở Bài 2.
- Không impute missing trước khi xem missing pattern production.
- Giữ `area_definition_risk` để phân tích riêng theo property type.
