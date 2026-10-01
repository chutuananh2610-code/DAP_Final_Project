# BT4 — RUBRIC TRACEABILITY

## 1. Chuẩn bị dữ liệu cho mô hình — 4 điểm

- Cleaned production: `data/processed/hcm_realestate_cleaned_20260912_163121.parquet`.
- Feature audit: `reports/modeling/MODELING_DATA_AUDIT.csv`.
- Feature policy: `reports/modeling/feature_selection_report.csv`.
- Preprocessing: `Pipeline` + `ColumnTransformer`; imputer/scaler/encoder fit trên train.
- Leakage guard: `src/dap_project/features/build_features.py`.
- Correlation/VIF: `reports/modeling/numeric_correlation.csv`, `vif.csv`.
- Split: 80/20, random_state=42.

## 2. Xây dựng và tinh chỉnh ≥2 mô hình — 8 điểm

- Dummy Median baseline.
- Linear Regression.
- Ridge với GridSearchCV.
- Decision Tree với GridSearchCV.
- Random Forest với RandomizedSearchCV.
- 5-fold CV trên train, test set không dùng để chọn hyperparameter.
- Code: `src/dap_project/models/train.py`.

## 3. Đánh giá & so sánh bằng ≥2 chỉ số — 6 điểm

- MAE, RMSE, R² + CV MAE mean/std + train/test generalization gap.
- Bảng: `reports/modeling/model_comparison.csv`.
- Bias–variance: Ridge + nonlinear learning curves.
- Final model chọn theo mean CV MAE, không chọn trước khi chạy.
- Production final: Random Forest; Test MAE 16,58 tỷ, RMSE 47,71 tỷ, R² 0,451.

## 4. Diễn giải nghiệp vụ — 4 điểm

- Permutation importance: `reports/modeling/permutation_importance.csv`.
- Error analysis theo property type, legacy area, price band và top lỗi lớn.
- Báo cáo: `docs/BT4_submission.md`.
- Nêu rõ giá rao ≠ giá giao dịch và predictive importance ≠ causal effect.

## 5. Demo khuyến khích — 3 điểm

- `app/app.py` cho phép nhập feature mà final model thực sự sử dụng.
- Chạy: `streamlit run app/app.py`.
- Có disclaimer: chỉ là ước tính từ giá rao CafeLand, không phải chứng thư thẩm định giá.

## 6. Reproducibility

- `python scripts/run_all.py --stage features`
- `python scripts/run_all.py --stage modeling`
- `python scripts/run_all.py --stage report`
- `pytest -q`
- Notebook 04 và 05 đã execute không lỗi.
