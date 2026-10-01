# RUBRIC TRACEABILITY — FINAL PROJECT

## Bài tập 1 — 10 điểm

| Tiêu chí | Evidence | Trạng thái |
|---|---|---|
| Business Question & target | `PROJECT_CHARTER.md`, `docs/BT1_submission.md` | Hoàn thành |
| Project Charter | `PROJECT_CHARTER.md` | Hoàn thành |
| Khả thi & nguồn dự phòng | `docs/source_investigation.md`, `docs/data_feasibility.md` | Hoàn thành |
| Elevator pitch & vai trò | `docs/BT1_submission.md` | Hoàn thành |

## Bài tập 2 — 20 điểm

| Tiêu chí | Evidence | Trạng thái |
|---|---|---|
| ≥5.000 dòng, ≥8 biến | 10.000 raw → 6.452 processed, 22 cột | PASS |
| Hàm hóa/module hóa | `src/dap_project/data/*`, `pipelines/acquisition.py` | PASS |
| Pandas/NumPy, đa định dạng | `organize.py`, CSV/JSON/Parquet | PASS |
| Data Dictionary & quality | `docs/data_dictionary.md`, quality outputs | PASS |

## Bài tập 3 — 25 điểm

| Tiêu chí | Evidence | Trạng thái |
|---|---|---|
| Missing & outlier | `eda_cleaning.py`, `BT3_submission.md`, cleaned/audit outputs | PASS kỹ thuật |
| ≥8 biểu đồ chuyên nghiệp | 13 PNG + 2 Plotly HTML trong `reports/figures/`; có dashboard, phân phối, boxplot, heatmap, market-positioning, treemap và scatter tương tác | PASS |
| 5–7 insight | 7 insight sinh từ production trong `BT3_submission.md` | PASS |
| Feature engineering sơ bộ | `features/build_features.py`, feature availability | PASS |
| Peer review | `docs/peer_review.md` | Chờ phản hồi thật |

## Điểm hướng tới mức Excellent

- Missing được phân loại theo bản chất thay vì điền máy móc.
- Outlier dùng log-scale + IQR theo loại hình và quy tắc ≥2/3 cờ.
- Hai trực quan Plotly tương tác (treemap + scatter diện tích–giá) hỗ trợ drill-down và storytelling.
- `property_type` được cải thiện nhưng giữ `unknown` khi không đủ bằng chứng.
- Feature policy chặn biến target-derived để tránh leakage.
- Toàn bộ stage chạy lại qua `python scripts/run_all.py --stage eda`.
- AI usage được khai báo trong `AI_USAGE.md`.

**Lưu ý:** Không đánh dấu tiêu chí peer review là hoàn tất cho đến khi có phản hồi chéo nhóm thực tế.
