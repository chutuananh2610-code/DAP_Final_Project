# DATA QUALITY LOG

## BT3 — Production 20260912_163121

**Input:** `data/processed/hcm_realestate_20260912_163121.csv` — 6.452 dòng × 22 cột.

| Vấn đề | Phát hiện | Quyết định |
|---|---:|---|
| URL hồ sơ môi giới trong processed | 304 | Loại khỏi analytical dataset bằng token `/moi-gioi/` |
| `property_type=unknown` ban đầu | 1.583 | Tái suy luận từ title + URL; không ghi đè nhãn đã biết |
| Unknown còn lại sau cleaning | 282 | Giữ `unknown`, không gán đoán |
| Outlier giá trên log-scale | 32 | Chỉ là một cờ, không xóa riêng lẻ |
| Outlier diện tích trên log-scale | 77 | Chỉ là một cờ, không xóa riêng lẻ |
| Outlier giá/m² trên log-scale | 131 | Chỉ là một cờ, không xóa riêng lẻ |
| Robust outlier ≥2/3 cờ | 62 | Loại khỏi cleaned dataset |
| `description` missing | 100% | Không impute; loại khỏi model v1 |
| `listing_date` missing | 100% | Không impute; hoãn phân tích thời gian |
| `estimated_land_area_from_title` missing | 68,45% cleaned | Dùng QA, không coi là feature chính |
| `area_definition_risk=True` | 467 cleaned | Theo dõi ở BT4/residual analysis |

**Output cleaned:** 6.086 dòng, giữ lại 94,33% input.

## Nguyên tắc

- Không sửa dữ liệu raw.
- Không biến missing cấu trúc thành giá trị giả.
- Không dùng `price_per_m2` làm X khi target là `price_vnd`.
- Mọi ngưỡng BT3 nằm trong `config.yaml` hoặc module EDA, không rải hard-code ở notebook.
