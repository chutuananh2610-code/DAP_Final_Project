# data/processed

Thư mục chứa dữ liệu đã qua validation và dữ liệu cleaned phục vụ EDA/modeling.

Hai snapshot ổn định được giữ trong GitHub để giảng viên có thể chạy lại BT3/BT4 mà không cần crawl web:

- `hcm_realestate_latest.csv`: production processed đầu vào cho EDA.
- `hcm_realestate_cleaned_latest.csv`: cleaned dataset đầu vào cho feature engineering/modeling.

Các file có timestamp và bản JSON/Parquet được tạo lại từ pipeline nên không commit để tránh làm repository nặng.
