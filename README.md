# DAP Final Project — BQ01: Dự đoán giá bán bất động sản TP.HCM

**Học phần:** Lập trình Phân tích Dữ liệu (Data Analysis Programming)  
**Case study chính:** Nhà Đất CafeLand (`nhadat.cafeland.vn`)  
**Business Question:** Dựa trên vị trí, loại hình và các đặc điểm của bất động sản tại phạm vi TP.HCM trước sáp nhập cấp tỉnh năm 2025, có thể ước tính mức giá rao bán hợp lý hay không?  
**Target:** `price_vnd`  
**Loại bài toán:** Supervised Learning — Regression

## 1. Thành viên

| Thành viên | MSSV | Vai trò đề xuất |
|---|---|---|
| Chu Tuấn Anh | 24650541 | Team Lead, Data Acquisition & Integration |
| Đinh Duy Đức |  | Data Quality, Pandas/NumPy & Data Dictionary |
| Dương Trừng Hân |  | Feasibility, Validation, Documentation & QA |

## 2. Phạm vi đã khóa

- Giao dịch: **Bán**.
- Nguồn chính: **CafeLand 100%** ở giai đoạn hiện tại.
- Không giới hạn ngày đăng; giữ `listing_date` để phân tích thời gian sau này.
- Không gian: **ranh giới TP.HCM trước sáp nhập cấp tỉnh năm 2025**.
- Vì CafeLand hiện gắn nhãn “TP. Hồ Chí Minh” cho cả các khu vực thuộc Bình Dương/Bà Rịa–Vũng Tàu trước sáp nhập, pipeline có bộ lọc `legacy_hcm_scope`.
- Raw data không bị sửa; dữ liệu chuẩn hóa đi qua `interim/`; dữ liệu sẵn sàng EDA đi vào `processed/`.
- `title` và `description` được giữ ở raw nhưng **không dùng làm feature cho model v1** để giảm nguy cơ target leakage.
- `price_per_m2` chỉ dùng cho EDA/kiểm tra chất lượng, **không dùng làm X** vì suy ra trực tiếp từ target.

## 3. Cấu trúc cố định

```text
DAP_Final_Project/
├── README.md
├── PROJECT_CHARTER.md
├── AI_USAGE.md
├── requirements.txt
├── pyproject.toml
├── config.yaml
├── .gitignore
├── data/
│   ├── raw/
│   ├── external/
│   ├── interim/
│   └── processed/
├── docs/
├── notebooks/
│   ├── 01_data_feasibility.ipynb
│   ├── 02_data_quality.ipynb
│   ├── 03_eda.ipynb
│   ├── 04_feature_engineering.ipynb
│   └── 05_modeling.ipynb
├── src/dap_project/
│   ├── data/
│   ├── features/
│   ├── visualization/
│   ├── models/
│   └── pipelines/
├── scripts/
│   └── run_all.py
├── reports/
├── presentation/
├── models/
├── app/
└── tests/
```

## 4. Bài tập 1

Bài tập 1 đã được hoàn thiện trong:

- `PROJECT_CHARTER.md`
- `docs/BT1_submission.md`
- `docs/data_feasibility.md`
- `docs/source_investigation.md`
- `docs/hcm_legacy_scope.md`

## 5. Bài tập 2

Phần code Bài tập 2 đã được module hóa tại:

- `src/dap_project/data/cafeland_crawler.py`
- `src/dap_project/data/parsers.py`
- `src/dap_project/data/scope.py`
- `src/dap_project/data/organize.py`
- `src/dap_project/pipelines/acquisition.py`
- `notebooks/02_data_quality.ipynb`

### Chạy thử không truy cập web

```bash
python scripts/run_all.py --stage sample
```

### Crawl production

> Trước khi chạy phải đọc `docs/source_investigation.md`, kiểm tra `robots.txt`,
> điều khoản sử dụng và thay địa chỉ liên hệ trong `config.yaml`.

```bash
python scripts/run_all.py --stage acquisition --max-records 6500
```

Pipeline ưu tiên thu thập **search-result cards** trước để giảm tải website. Chỉ bật
detail enrichment khi thật sự cần thêm trường.

```bash
python scripts/run_all.py --stage acquisition --max-records 6500 --enrich-details
```

### Kiểm tra gate của Bài tập 2

```bash
python scripts/run_all.py --stage quality
```

Gate:
- `>= 5,000` dòng hợp lệ sau lọc phạm vi.
- `>= 8` biến.
- Có raw + interim + processed.
- Có Data Dictionary.
- Có missing rate, duplicate rate, inconsistency report.
- Có so sánh CSV/JSON/Parquet.

## 6. Trạng thái production và Bài tập 3

Production mới nhất đã được pipeline xác nhận: **10.000 raw → 6.452 processed**, 22 biến sau tổ chức/kiểm soát chất lượng. Đây là đầu vào chính thức cho EDA; không dùng pilot để thay thế production.

Để repository gọn nhưng vẫn có thể chạy lại BT3/BT4 mà không cần crawl web, GitHub giữ hai snapshot ổn định: `data/processed/hcm_realestate_latest.csv` và `data/processed/hcm_realestate_cleaned_latest.csv`. Raw production, các bản JSON/Parquet và snapshot theo timestamp được tái tạo từ pipeline nên không commit.

Chạy Bài tập 3:

```bash
python scripts/run_all.py --stage eda
```

Stage `eda` thực hiện: phân tích missing, cải thiện `property_type`, kiểm tra ngoại lai robust theo log-scale, lưu cleaned dataset riêng, tạo bộ trực quan hóa report-ready gồm **13 biểu đồ tĩnh + 2 Plotly tương tác** (treemap và scatter), sinh 7 insight và chuẩn bị feature set không leakage cho Bài tập 4.

Kết quả run production hiện tại: **6.086 cleaned rows**, **13 static charts**, **2 interactive charts**, **GATE BT3 = PASS**. Báo cáo tự sinh nằm tại `docs/BT3_submission.md`; hình nằm tại `reports/figures/`; audit và bảng profiling nằm tại `data/interim/` và `reports/eda/`.

Peer review chéo là hoạt động con người: template đã có tại `docs/peer_review.md` và phải được cập nhật bằng phản hồi thật trước khi nộp.

## 7. Bài tập 4 — Feature Engineering & Modeling

Feature set model v1 được khóa từ cleaned production gồm: `area_m2`, `property_type`, `legacy_area`. Các biến suy ra trực tiếp từ target như `price_per_m2`, `price_billion`, `log_price_vnd` và các identifier/text như `listing_id`, `url`, `title`, `description` bị loại khỏi X để tránh leakage.

Chạy feature audit:

```bash
python scripts/run_all.py --stage features
```

Chạy modeling production:

```bash
python scripts/run_all.py --stage modeling
```

Pipeline huấn luyện Dummy Median baseline, Linear Regression, Ridge, Decision Tree và Random Forest; hyperparameter được chọn bằng 5-fold cross-validation trên train. Run production hiện tại dùng 6.086 cleaned rows, split 4.868 train / 1.218 test. Final model được chọn theo CV MAE là **Random Forest**; holdout **MAE 16,58 tỷ VNĐ**, **RMSE 47,71 tỷ VNĐ**, **R² 0,451**. Đây là giá rao CafeLand nên chỉ dùng như ước tính tham khảo, không phải chứng thư thẩm định giá.

Artifacts chính:
- `models/best_price_model.joblib`
- `models/model_metadata.json`
- `reports/modeling/model_comparison.csv`
- `reports/modeling/model_metrics.json`
- `docs/BT4_submission.md`
- `presentation/BT4_slide_outline.md`
- `notebooks/04_feature_engineering.ipynb`
- `notebooks/05_modeling.ipynb`

Demo:

```bash
streamlit run app/app.py
```

Kiểm tra deliverables:

```bash
python scripts/run_all.py --stage report
```

## 8. Cài đặt

Python 3.11+:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## 9. Test

```bash
pytest -q
```

## 10. Lưu ý học thuật

Mọi thành viên phải hiểu và giải thích được code mình phụ trách. Xem `AI_USAGE.md`.
