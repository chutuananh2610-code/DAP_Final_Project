# DATA DICTIONARY — v1.0

| Tên biến | Kiểu dự kiến | Đơn vị | Ý nghĩa | Nguồn | Missing policy sơ bộ | Model |
|---|---|---|---|---|---|---|
| source | category | — | nguồn record | crawler | không thiếu | No |
| url | string | — | canonical listing URL | search | không thiếu | No |
| listing_id | string | — | mã tài sản | detail/URL | fallback URL id | No |
| listing_date | datetime | ngày | ngày đăng | detail | giữ NA | Maybe |
| title | string | — | tiêu đề raw | search/detail | giữ raw | No v1 |
| description | string | — | mô tả raw | detail/search | giữ raw | No v1 |
| transaction_type | category | — | sale | scope | fixed | No |
| property_type | category | — | loại BĐS | URL/title/detail | Unknown nếu chưa rõ | Yes |
| current_ward | category | — | nhãn vị trí hiện tại | page | giữ NA | Maybe |
| legacy_area | category | — | quận/huyện trong TP.HCM cũ | derived | unresolved → không vào processed | Yes |
| city | category | — | TP.HCM | page | fixed | No |
| price_text | string | — | giá hiển thị | page | raw | No |
| price_vnd | float | VNĐ | giá rao bán chuẩn hóa | derived | missing → không training | Target |
| displayed_price_per_m2 | float | VNĐ/m² | giá/m² website | page | giữ cho EDA | **No** |
| area_text | string | — | diện tích hiển thị | page | raw | No |
| area_m2 | float | m² | diện tích parse | derived | missing → không training | Yes |
| land_area_m2 | float | m² | diện tích đất parse từ text | derived | giữ NA | Maybe |
| floor_area_m2 | float | m² | tổng diện tích sàn parse | derived | giữ NA | Maybe |
| bedrooms | float | phòng | số phòng ngủ | detail/text | nhóm/NA, quyết định sau EDA | Maybe |
| bathrooms | float | phòng | số toilet | detail/text | nhóm/NA | Maybe |
| floors | float | tầng | số tầng | detail/text | nhóm/NA | Maybe |
| legal_status | category | — | pháp lý | detail/text | Unknown | Maybe |
| direction | category | — | hướng nhà | detail | Unknown | Maybe |
| road_width_m | float | m | đường trước nhà | detail/text | NA | Maybe |
| crawl_page | int | trang | trang nguồn | crawler | không thiếu | No |
| crawled_at | datetime | — | thời điểm crawl | crawler | không thiếu | No |
| scope_status | category | — | trạng thái kiểm tra phạm vi | derived | không thiếu | No |
| area_definition_risk | bool | — | cảnh báo area không đồng nghĩa | derived | False default | No |
