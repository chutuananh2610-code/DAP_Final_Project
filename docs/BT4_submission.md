# BÀI TẬP 4 — MÔ HÌNH HÓA & SO SÁNH KẾT QUẢ

## 1. Business Question và dữ liệu đầu vào

BQ01: Ước tính giá rao bán BĐS tại TP.HCM từ vị trí, loại hình và đặc điểm tin đăng CafeLand.
Input cleaned: `hcm_realestate_cleaned_20260912_163121.parquet` — 6,086 dòng.
Target: `price_vnd`. Feature model v1: area_m2, property_type, legacy_area.

## 2. Kiểm soát leakage và tiền xử lý

- Chỉ fit imputer/scaler/encoder trên train thông qua scikit-learn Pipeline + ColumnTransformer.
- Không dùng price_text, price_per_m2, price_billion, log_price_vnd, title, description, listing_id, url làm X.
- OneHotEncoder dùng `handle_unknown='ignore'`; numeric dùng median imputation + StandardScaler.
- Split 80/20 với random_state cố định; hyperparameter chỉ chọn bằng cross-validation trên train.

## 3. Mô hình và đánh giá

| Model | CV MAE (tỷ) | Test MAE (tỷ) | Test RMSE (tỷ) | Test R² |
|---|---:|---:|---:|---:|
| Random Forest | 16.96 | 16.58 | 47.71 | 0.451 |
| Decision Tree | 17.18 | 18.04 | 51.67 | 0.356 |
| Dummy Median | 22.58 | 23.78 | 67.22 | -0.090 |
| Ridge | 24.81 | 25.91 | 59.37 | 0.149 |
| Linear Regression | 25.18 | 26.29 | 59.36 | 0.150 |

Final model: **Random Forest**, được chọn theo CV MAE thấp nhất trong các model không phải baseline.
Holdout MAE = **16.58 tỷ VNĐ**, RMSE = **47.71 tỷ VNĐ**, R² = **0.451**.
So với Dummy Median, Test MAE giảm **30.3%**.
Best params: `{'model__n_estimators': 160, 'model__min_samples_leaf': 8, 'model__max_features': 0.7, 'model__max_depth': None}`.

## 4. Bias–variance / overfitting

Train MAE của final model = 15.04 tỷ; Test MAE = 16.58 tỷ. Generalization gap = 1.54 tỷ VNĐ.
Learning curves được lưu riêng cho Ridge và mô hình phi tuyến để xem train/validation error khi tăng dữ liệu.

## 5. Model interpretation và error analysis

Permutation importance trên holdout cho thấy các feature nổi bật: **area_m2, legacy_area, property_type**.
Nhóm property_type có MAE cao nhất: **villa (MAE 46.95 tỷ VNĐ)**.
Khu vực có MAE cao nhất trong holdout: **Quận 1 (MAE 48.04 tỷ VNĐ)**.
Các kết quả này phản ánh khả năng dự báo/association, không phải quan hệ nhân quả.

## 6. Giá trị nghiệp vụ

Mô hình có thể dùng như lớp tham khảo định giá nhanh từ dữ liệu giá rao CafeLand, hỗ trợ sàng lọc và so sánh ban đầu.
Sai số phải được đọc theo đơn vị tỷ VNĐ và không có benchmark thẩm định độc lập trong bộ dữ liệu hiện tại, vì vậy không nên diễn giải là độ chính xác đủ cho quyết định giao dịch.

## 7. Hạn chế

- Target là giá rao, không phải giá giao dịch thực tế.
- Feature vị trí hiện ở mức legacy_area; chưa có tọa độ/tiện ích chi tiết.
- Card-only crawl làm thiếu các thuộc tính chi tiết như listing_date, bedrooms, legal_status.
- area_m2 có area-definition risk ở một số nhà phố; cần theo dõi khi mở rộng model.
- CafeLand có selection bias; kết quả không đại diện toàn bộ thị trường TP.HCM.
- Không suy luận causal effect từ coefficient/feature importance.

## 8. Artifacts

- actual_vs_predicted: `C:/Users/LEGION/Downloads/DAP_Final_Project_BT1_BT2/DAP_Final_Project/reports/figures/15_model_actual_vs_predicted.png`
- residual_distribution: `C:/Users/LEGION/Downloads/DAP_Final_Project_BT1_BT2/DAP_Final_Project/reports/figures/16_model_residual_distribution.png`
- residual_vs_predicted: `C:/Users/LEGION/Downloads/DAP_Final_Project_BT1_BT2/DAP_Final_Project/reports/figures/17_model_residual_vs_predicted.png`
- model_comparison: `C:/Users/LEGION/Downloads/DAP_Final_Project_BT1_BT2/DAP_Final_Project/reports/figures/18_model_comparison.png`
- ridge_learning_curve: `C:/Users/LEGION/Downloads/DAP_Final_Project_BT1_BT2/DAP_Final_Project/reports/figures/19_ridge_learning_curve.png`
- nonlinear_learning_curve: `C:/Users/LEGION/Downloads/DAP_Final_Project_BT1_BT2/DAP_Final_Project/reports/figures/20_nonlinear_learning_curve.png`
- permutation_importance: `C:/Users/LEGION/Downloads/DAP_Final_Project_BT1_BT2/DAP_Final_Project/reports/figures/21_permutation_importance.png`
- error_by_property_type: `C:/Users/LEGION/Downloads/DAP_Final_Project_BT1_BT2/DAP_Final_Project/reports/figures/22_error_by_property_type.png`

Model artifact: `models/best_price_model.joblib`.
Metrics/table: `reports/modeling/`.
Demo: `streamlit run app/app.py`.
