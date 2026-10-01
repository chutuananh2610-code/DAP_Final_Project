# PROJECT PIPELINE HANDOFF — DAP FINAL PROJECT

> **Single Source of Truth cho việc phát triển tiếp dự án**
>
> File này dùng để bàn giao toàn bộ trạng thái, nguyên tắc kiến trúc và pipeline hiện tại.
> Mọi lần phát triển sau phải đọc file này trước, giữ nguyên pipeline gốc và chỉ mở rộng bên trong cấu trúc đã khóa.

**Cập nhật trạng thái:** 2026-09-30  
**Dự án:** DAP Final Project — BQ01  
**Domain:** Bất động sản Việt Nam  
**Case study chính:** CafeLand / Nhà Đất CafeLand  
**Nhóm:** 4  
**Business Question:** Dự đoán giá rao bán BĐS tại TP.HCM  
**Loại bài toán:** Supervised Learning — Regression  
**Target:** `price_vnd`

---

## 1. NGUYÊN TẮC BẤT BIẾN KHI PHÁT TRIỂN TIẾP

1. **Không tạo một project/pipeline mới song song.**
2. **Không thay cấu trúc top-level đã khóa nếu không thật sự bắt buộc.**
3. Mọi chức năng mới phải được gắn vào đúng stage của pipeline hiện tại.
4. `data/raw` là dữ liệu gốc, không sửa trực tiếp.
5. Dữ liệu chuẩn hóa đi qua `data/interim`; dữ liệu sẵn sàng phân tích/model đi vào `data/processed`.
6. Không dùng dữ liệu giả để đạt gate số dòng.
7. Không dùng feature gây target leakage.
8. Mọi quyết định dữ liệu/model quan trọng phải có tài liệu hóa.
9. Code phải chạy lại được từ entry point của project.
10. Mọi phần AI hỗ trợ phải khai báo minh bạch trong `AI_USAGE.md`.

## 2. CẤU TRÚC PROJECT ĐÃ KHÓA

```text
DAP_Final_Project/
├── README.md
├── PROJECT_CHARTER.md
├── PROJECT_PIPELINE_HANDOFF.md
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
├── scripts/run_all.py
├── reports/
├── presentation/
├── models/
├── app/
└── tests/
```

### Quy tắc đặt code mới

- Thu thập/parser/scope/quality ban đầu → `src/dap_project/data/`
- Orchestration pipeline → `src/dap_project/pipelines/`
- Feature engineering tái sử dụng → `src/dap_project/features/`
- Hàm trực quan hóa tái sử dụng → `src/dap_project/visualization/`
- Train/evaluate/save model → `src/dap_project/models/`
- Entry point CLI → `scripts/run_all.py`
- Phân tích theo từng giai đoạn → `notebooks/01..05`
- Báo cáo/ảnh → `reports/`
- Demo cuối → `app/`
- Unit/integration test → `tests/`

---

## 3. BUSINESS QUESTION VÀ PHẠM VI ĐÃ KHÓA

### Business Question

> Dựa trên vị trí, loại hình và các đặc điểm của bất động sản tại TP.HCM,
> có thể ước tính mức giá rao bán hợp lý của một bất động sản hay không?

### Target

`price_vnd` — giá rao bán chuẩn hóa về VNĐ.

### Transaction

Chỉ lấy **bất động sản bán**.

### Phạm vi địa lý

Phạm vi nghiên cứu là **TP.HCM theo ranh giới trước sáp nhập cấp tỉnh năm 2025**.
Không được chỉ dựa vào nhãn city hiện tại của CafeLand để xác định scope.

### Logic scope

Record được đưa vào processed khi:

- `scope_status == confirmed_by_current_ward`; hoặc
- `scope_status == confirmed_by_legacy_text`;

và đồng thời:

- `price_valid == True`;
- `area_valid == True`.

Nếu scope mâu thuẫn:

`scope_status = conflict`

Nếu không xác định được:

`scope_status = unresolved`

Hai nhóm này **không được tự suy diễn** và không đi vào modeling dataset.

### Leakage policy

Không dùng làm feature model v1:

- `price_text`
- `displayed_price_per_m2`
- `title`
- `description`
- `listing_id`
- `url`

Đặc biệt:

`price_per_m2 = price_vnd / area_m2`

nên tuyệt đối không dùng làm X khi target là `price_vnd`.

## 4. PIPELINE GỐC — PHẢI GIỮ NGUYÊN

```text
Business Question
      ↓
Data Feasibility
      ↓
CafeLand Acquisition
      ↓
RAW
      ↓
Parsing / Normalization
      ↓
Legacy HCMC Scope Validation
      ↓
INTERIM
      ↓
Initial Quality + Validation + Dedup
      ↓
PROCESSED
      ↓
EDA
      ↓
Feature Engineering
      ↓
Modeling
      ↓
Model Evaluation / Comparison
      ↓
Insights
      ↓
Report / Presentation / Demo
```

Không được bỏ qua stage để làm nhanh.
Mỗi stage phải tạo output rõ ràng để stage sau dùng lại.

## 5. PIPELINE THU THẬP DỮ LIỆU HIỆN TẠI

```text
CafeLand search pages
        ↓
pagination /page-N/
        ↓
listing cards
        ↓
checkpoint
        ↓
optional detail enrichment
        ↓
raw CSV/JSON/Parquet
        ↓
Pandas/NumPy normalization
        ↓
legacy HCMC scope filter
        ↓
interim CSV/JSON/Parquet
        ↓
price/area validation
        ↓
dedup listing_id
        ↓
processed CSV/JSON/Parquet
```

### Các module đang chịu trách nhiệm

- `cafeland_crawler.py`: HTTP session, robots, retry/backoff, rate limit, pagination, card/detail acquisition.
- `parsers.py`: parse giá, diện tích, detail HTML, property type.
- `scope.py`: xác định phạm vi TP.HCM cũ.
- `organize.py`: normalize, build processed, quality summary, multi-format I/O, benchmark.
- `pipelines/acquisition.py`: orchestration raw → interim → processed.
- `scripts/run_all.py`: command-line interface.

## 6. CẤU HÌNH THU THẬP CHÍNH

Nguồn cấu hình: `config.yaml`.

Các giá trị quan trọng hiện tại:

```yaml
target: price_vnd
transaction_type: sale
geography_mode: pre_2025_hcm_boundary
target_raw_records: 6500
minimum_valid_records: 5000
max_pages: 500
timeout_seconds: 30
min_delay_seconds: 1.5
max_delay_seconds: 3.0
save_every_pages: 10
respect_robots: true
robots_fail_closed: true
enrich_details_default: false
include_expired: false
```

Không hard-code lại những giá trị đã có trong config ở module khác nếu có thể tránh.

---

## 7. TRẠNG THÁI DATA PRODUCTION ĐÃ XÁC NHẬN

Dataset production mới nhất đã kiểm tra trực tiếp:

`data/raw/cafeland_raw_20260912_163121.csv`

### Quy mô

| Stage | Rows | Ghi chú |
|---|---:|---|
| Raw | 10,000 | dữ liệu crawl từ CafeLand |
| Interim | 10,000 | sau normalize + scope inference |
| Processed | 6,452 | sau scope + price/area validation |
| Processed columns | 22 | vượt yêu cầu ≥ 8 biến |
| Duplicate listing_id | 0 | trong processed mới nhất |

**Gate Bài tập 2 đã PASS thực tế: ≥5.000 dòng và ≥8 biến.**

### Scope distribution trên interim 10.000 rows

| scope_status | Rows |
|---|---:|
| confirmed_by_current_ward | 6,181 |
| confirmed_by_legacy_text | 375 |
| unresolved | 3,241 |
| conflict | 203 |

### Validation

- `price_valid=True`: 9,631
- `price_valid=False`: 369
- `area_valid=True`: 9,870
- `area_valid=False`: 130
- eligible sau scope + price + area: **6,452**
- duplicate bị loại ở run mới nhất: **0**

### Property type trên processed 6.452 rows

| property_type | Rows |
|---|---:|
| house | 3,344 |
| unknown | 1,583 |
| apartment | 690 |
| land | 536 |
| villa | 215 |
| commercial | 84 |

Điểm cần xử lý trước modeling:

`unknown = 1,583 / 6,452 ≈ 24.5%`

Tỷ lệ này khá cao và nên được cải thiện bằng parser/rules hoặc xử lý hợp lý trong EDA/feature engineering.

### Missing đáng chú ý

Trong processed production mới nhất:

- `description`: missing 100%
- `listing_date`: missing 100%
- `location_text`: thiếu 308 rows
- `update_text`: thiếu 466 rows
- `current_ward`: thiếu 365 rows
- `estimated_land_area_from_title`: thiếu 4,523 rows

Nguyên nhân chính: production hiện ưu tiên **search-card crawl**, chưa enrich detail toàn bộ.

## 8. DATA DICTIONARY / FEATURE POLICY HIỆN TẠI

Nhóm biến cốt lõi đã có hoặc đã thiết kế:

- `source`
- `url`
- `listing_id`
- `listing_date`
- `title`
- `description`
- `transaction_type`
- `property_type`
- `current_ward`
- `legacy_area`
- `price_text`
- `price_vnd`
- `area_text`
- `area_m2`
- `bedrooms`
- `bathrooms`
- `floors`
- `legal_status`
- `direction`
- `road_width_m`
- `crawl_page`
- `crawled_at`
- `scope_status`
- `area_definition_risk`

Feature availability thực tế phải được xác nhận bằng production trước khi đưa vào model.

### Model v1 tối thiểu có thể bắt đầu bằng

```text
area_m2
+ property_type
+ legacy_area
```

Có thể mở rộng thêm sau EDA nếu availability đủ:

```text
bedrooms
floors
bathrooms
legal_status
direction
road_width_m
listing_date / time features
```

Không ép đưa feature sparse vào model chỉ vì Data Dictionary đã dự kiến.

---

## 9. CÁC RỦI RO DỮ LIỆU ĐÃ NHẬN DIỆN

1. CafeLand có thể thay đổi HTML.
2. Request có thể gặp 429/mất kết nối.
3. Scope TP.HCM hiện tại khác phạm vi nghiên cứu.
4. Một số listing ghi giá “Thỏa thuận”.
5. `area_m2` không phải lúc nào cũng cùng nghĩa giữa các loại BĐS.
6. House có thể hiển thị tổng diện tích sàn thay vì diện tích đất.
7. Nhiều detail attributes có missing cao.
8. Text có thể chứa trực tiếp giá → nguy cơ leakage.
9. Duplicate phải ưu tiên `listing_id`, fallback URL.
10. Không public raw production nếu chưa xác định quyền sử dụng phù hợp.

## 10. CODE QUALITY HIỆN TẠI

### Đã có

- module hóa crawler/parser/scope/organize/pipeline;
- retry/backoff;
- rate limiting;
- robots.txt fail-closed;
- checkpoint;
- parser fallback;
- multi-format CSV/JSON/Parquet;
- NumPy/Pandas normalization;
- benchmark function;
- unit tests;
- AI disclosure.

### Test hiện tại

Đã chạy sau khi triển khai BT4:

```text
15 passed in 1.42s
```

BT3 đã bổ sung test cho missing-policy, structural non-listing filter, property-type refinement, robust outlier handling và chặn target-derived feature khỏi model v1.

Python environment trên máy hiện tại:

`Python 3.14.7`

Học phần yêu cầu Python 3.11+, nên vẫn phù hợp.

### Test hiện có

- parse giá;
- parse diện tích;
- parse detail HTML fixture;
- scope từ current ward;
- scope từ legacy text.

### Test nên bổ sung tiếp

Tạo integration test cho toàn tuyến:

```text
fixture/raw
→ normalize_dataframe
→ infer_scope
→ build_processed
→ quality gate
```

Ngoài ra nên test:

- negotiable price;
- malformed area;
- scope conflict;
- unresolved scope;
- duplicate listing_id;
- crawler empty pages;
- retry/failure behavior;
- checkpoint/resume khi bổ sung resume logic.

---

## 11. CÁC VẤN ĐỀ CONSISTENCY CẦN SỬA

### 11.1 Pilot file bị thiếu

README và Notebook 01/02 đang tham chiếu:

`data/raw/cafeland_pilot_verified.csv`

nhưng file này hiện **không tồn tại trong data/raw**.

Do đó cần chọn một trong hai:

1. phục hồi đúng pilot file; hoặc
2. sửa notebook/sample pipeline để sử dụng fixture/latest production loader phù hợp.

Không để tài liệu nói một file tồn tại trong khi repo thực tế không có.

### 11.2 Documentation đang chậm hơn production

Các file sau vẫn còn mô tả trạng thái pilot/chưa production:

- `docs/data_quality_initial.md`
- `docs/rubric_traceability.md`
- một số đoạn trong `README.md`
- `docs/BT2_submission.md`

Trong khi production đã có:

```text
10,000 raw
10,000 interim
6,452 processed
22 columns
Gate PASS
```

Cần cập nhật tài liệu trước khi freeze BT2.

### 11.3 Gate logic bị lặp

Hiện gate xuất hiện ở nhiều nơi:

- `acquisition.py`
- `run_all.py`

Nên gom về một hàm duy nhất, ví dụ:

```python
evaluate_quality_gate(df, config)
```

để tránh drift giữa config và hard-code.

### 11.4 Checkpoint chưa phải resume state hoàn chỉnh

Crawler hiện lưu checkpoint định kỳ nhưng chưa có abstraction rõ để:

- load checkpoint;
- nhớ page đã crawl;
- nhớ seen URLs;
- resume đúng vị trí;
- tránh request lại sau crash.

Đây là deepening opportunity tốt cho kiến trúc sau này.

---

## 12. TRẠNG THÁI THEO BÀI TẬP

### Bài tập 1 — HOÀN THÀNH Ở MỨC TỐT/EXCELLENT

Đã có:

- Business Question;
- target;
- Project Charter;
- feasibility;
- risk analysis;
- backup sources;
- roles;
- elevator pitch;
- scope strategy;
- leakage policy.

### Bài tập 2 — ĐÃ CÓ PRODUCTION VÀ PASS GATE

Đã có:

- crawler thật;
- ≥5.000 processed rows;
- ≥8 variables;
- module hóa;
- Pandas/NumPy;
- raw/interim/processed;
- Data Dictionary;
- quality logic;
- multi-format save;
- unit tests.

Còn cần polish docs/production quality report để freeze chính thức.

### Bài tập 3 — ĐÃ TRIỂN KHAI KỸ THUẬT VÀ PASS GATE

Đã triển khai stage `eda` nối trực tiếp sau processed production của Bài tập 2.

Kết quả production 20260912_163121:
1. input processed: 6.452 rows;
2. loại 304 URL hồ sơ môi giới khỏi analytical dataset;
3. cải thiện 1.001 nhãn `property_type`, unknown còn 282 rows trong cleaned;
4. ngoại lai: log-scale + IQR theo `property_type`, chỉ loại khi đạt ≥2/3 cờ robust; loại 62 rows;
5. cleaned dataset: 6.086 rows (94,33% input);
6. 13 biểu đồ tĩnh + 2 Plotly tương tác (treemap + scatter diện tích–giá);
7. 7 insight được tính trực tiếp từ production;
8. feature set sơ bộ không leakage: numeric `area_m2`, `log_area_m2`; categorical `property_type`, `legacy_area`;
9. cleaned CSV/JSON/Parquet, row-level audit, missing-policy và feature-availability report đã được lưu;
10. `notebooks/03_eda.ipynb`, `docs/BT3_submission.md`, `docs/peer_review.md` đã được triển khai.

`price_per_m2`, `price_billion`, `log_price_vnd` chỉ dùng cho EDA/diễn giải và không đi vào X khi target là `price_vnd`.

**GATE BT3 hiện tại: PASS về code/data/EDA.** Peer review chéo thực tế vẫn cần nhóm khác thực hiện và điền vào `docs/peer_review.md` trước khi nộp để hoàn thiện tiêu chí làm việc nhóm.

### Bài tập 4 — ĐÃ TRIỂN KHAI VÀ PASS GATE

Đã triển khai nối tiếp trực tiếp từ cleaned dataset của BT3:

- `notebooks/04_feature_engineering.ipynb` và `05_modeling.ipynb` đã hoàn thiện và execute không lỗi;
- feature model v1: `area_m2`, `property_type`, `legacy_area`;
- preprocessing bằng scikit-learn `Pipeline` + `ColumnTransformer`, fit chỉ trên train;
- baseline Dummy Median + Linear Regression + Ridge + Decision Tree + Random Forest;
- Ridge/Decision Tree/Random Forest được tinh chỉnh bằng cross-validation;
- split production: 4.868 train / 1.218 test;
- đánh giá bằng MAE, RMSE, R², CV MAE và generalization gap;
- final model chọn theo mean CV MAE: **Random Forest**;
- holdout MAE **16,58 tỷ VNĐ**, RMSE **47,71 tỷ VNĐ**, R² **0,451**;
- đã có learning curves, residual analysis, permutation importance và error analysis theo loại hình/khu vực;
- model lưu tại `models/best_price_model.joblib`;
- báo cáo tại `docs/BT4_submission.md`, outline slide tại `presentation/BT4_slide_outline.md`;
- Streamlit demo tại `app/app.py`.

**GATE BT4: PASS.** Metric trên là kết quả chạy production thật, không phải số giả lập.

## 13. HƯỚNG MODELING ĐÃ THỐNG NHẤT

BQ01 là **regression**.

Không dùng Logistic Regression chỉ để đủ số model nếu target vẫn là `price_vnd`.

Nên bắt đầu với:

### Baseline

- Median predictor hoặc simple area-only baseline.

### Model 1 — Linear

- Linear Regression;
- hoặc Ridge/Lasso sau baseline.

### Model 2 — Non-linear

Có thể chọn:

- DecisionTreeRegressor;
- RandomForestRegressor;
- HistGradientBoostingRegressor;

tùy phạm vi kiến thức môn và yêu cầu giảng viên.

### Evaluation

Ít nhất:

- MAE;
- RMSE;
- R².

Có thể thêm MAPE nếu xử lý được tính phù hợp với distribution giá.

### Modeling rules

- preprocessing phải fit chỉ trên train;
- categorical encoding đi trong sklearn Pipeline/ColumnTransformer;
- không fit encoder/scaler trên full dataset;
- không dùng target-derived feature;
- phải kiểm tra overfitting;
- phải so sánh với baseline;
- kết quả phải diễn giải theo nghiệp vụ BĐS.

---

## 14. ƯU TIÊN PHÁT TRIỂN TIẾP

Thứ tự khuyến nghị, không đảo nếu không có lý do rõ:

### P0 — Freeze BT1/BT2

1. cập nhật docs theo production;
2. sửa missing pilot reference;
3. tạo production quality report;
4. lưu benchmark production;
5. centralize quality gate;
6. bổ sung integration test.

### P1 — Chuẩn bị BT3 — HOÀN THÀNH

7. đã cải thiện `property_type=unknown` từ 1.583 xuống 282 dòng trong cleaned;
8. detail enrichment được hoãn vì card production hiện đủ cho feature set v1 tối thiểu; chỉ bật khi cần feature detail;
9. đã phân tích missing và ghi chính sách xử lý;
10. đã định lượng `area_definition_risk`;
11. đã chốt cleaned-dataset policy và lưu riêng trong `data/processed`.

### P2 — EDA — HOÀN THÀNH

12. `03_eda.ipynb` đã triển khai và execute không lỗi;
13. đã tạo 13 charts tĩnh + 2 Plotly tương tác, cùng một visual theme thống nhất;
14. mỗi chart có diễn giải insight trong `docs/BT3_submission.md`;
15. đã tổng hợp 7 insight chính từ production;
16. figures đã lưu tại `reports/figures/`.

### P3 — Feature Engineering — HOÀN THÀNH

17. triển khai `04_feature_engineering.ipynb`;
18. đưa reusable logic vào `src/dap_project/features/build_features.py`;
19. freeze model feature set;
20. ghi rõ excluded/leakage features.

### P4 — Modeling — HOÀN THÀNH

21. baseline;
22. linear model;
23. non-linear model;
24. evaluation;
25. comparison;
26. interpretation;
27. lưu artifact vào `models/`.

### P5 — Deliver

28. final report;
29. slide 10–12 trang;
30. Streamlit demo nếu đủ thời gian;
31. README chạy từ đầu đến cuối;
32. kiểm tra AI disclosure;
33. rehearsal vấn đáp.

## 15. ENTRY POINT VÀ COMMANDS

### Test

```powershell
pytest -q
```

### Crawl production

```powershell
python scripts/run_all.py --stage acquisition --max-records 6500
```

### Detail enrichment

```powershell
python scripts/run_all.py --stage acquisition --max-records 6500 --enrich-details
```

Chỉ chạy detail enrichment sau khi kiểm tra robots/terms/rate-limit và thật sự cần feature detail.

### Quality

```powershell
python scripts/run_all.py --stage quality
```

### EDA / Bài tập 3

```powershell
python scripts/run_all.py --stage eda
```

Stage này tạo cleaned dataset, row-level audit, missing/feature reports, 13 biểu đồ tĩnh, 2 Plotly tương tác và `docs/BT3_submission.md`.

### Feature audit / Bài tập 4

```powershell
python scripts/run_all.py --stage features
```

### Modeling / Bài tập 4

```powershell
python scripts/run_all.py --stage modeling
```

Stage này huấn luyện/tuning các model, đánh giá holdout, tạo learning curves/error analysis, lưu best model, metrics, report và outline slide.

### Verify deliverables

```powershell
python scripts/run_all.py --stage report
```

### Streamlit demo

```powershell
streamlit run app/app.py
```

### Nguyên tắc entry point

Khi thêm EDA/modeling pipeline, ưu tiên mở rộng `run_all.py` bằng stage mới thay vì tạo nhiều script rời không liên kết.
Ví dụ tương lai có thể là:

```text
sample → acquisition → quality → eda → features → modeling → report
```

## 16. RUBRIC GATE CẦN LUÔN GIỮ TRONG ĐẦU

Final Project tối thiểu cần:

- dataset ≥5.000 rows và ≥8 variables;
- EDA ≥8 biểu đồ;
- missing/outlier được xử lý và giải thích;
- ≥2 models;
- ≥2 metrics;
- insight thực tế;
- code sạch/reproducible;
- README;
- AI disclosure.

Mức Excellent cần hướng tới:

- phân tích sâu;
- feature engineering có cơ sở;
- trực quan storytelling;
- model comparison có luận cứ;
- pipeline chống leakage;
- code module hóa;
- repo có thể chạy lại;
- diễn giải nghiệp vụ tốt;
- demo nếu khả thi.

Không đánh đổi reproducibility để lấy thêm điểm hình thức.

---

## 17. CÁCH LÀM VIỆC CHO MỌI LẦN PHÁT TRIỂN SAU

Trước khi sửa code, luôn trả lời 5 câu:

1. Thay đổi này thuộc stage nào của pipeline?
2. Input của stage là file/schema nào?
3. Output phải được lưu ở đâu?
4. Có phá invariant/raw/reproducibility/leakage policy không?
5. Cần update test/docs/config nào đi kèm?

Sau khi sửa:

1. chạy test;
2. chạy stage liên quan trên sample hoặc production phù hợp;
3. kiểm tra output;
4. cập nhật documentation;
5. cập nhật file handoff này nếu có thay đổi kiến trúc/trạng thái quan trọng.

### Quy tắc cho trợ lý AI ở các cuộc chat sau

Khi được yêu cầu tiếp tục dự án:

- đọc `PROJECT_PIPELINE_HANDOFF.md` trước;
- không tự tạo lại kiến trúc mới;
- không thay Business Question/target/scope nếu người dùng chưa yêu cầu;
- phát triển theo pipeline đã định;
- ưu tiên sửa/nâng module hiện có;
- nếu cần đổi invariant, phải nói rõ tác động trước khi thay;
- phân biệt rõ dữ liệu production với sample/pilot;
- không tuyên bố metric/kết quả nếu chưa chạy thật.

---

## 18. SOURCE OF TRUTH HIERARCHY

Khi có mâu thuẫn giữa tài liệu cũ và trạng thái project:

1. **Pipeline/invariant:** file này + `PROJECT_CHARTER.md` + `config.yaml`.
2. **Hành vi code:** source hiện tại trong `src/dap_project/`.
3. **Trạng thái dữ liệu:** output production mới nhất đã kiểm tra.
4. **Rubric:** phiếu chấm chính thức của học phần.
5. Các docs cũ hơn phải được cập nhật nếu lệch với 1–4.

File này không thay thế source code; nó là bản đồ kiến trúc và handoff để mọi lần phát triển sau không đi lệch pipeline.

## 19. SNAPSHOT NGẮN ĐỂ TIẾP TỤC NGAY

```text
BQ01: Predict HCMC real-estate asking price
Target: price_vnd
Source: CafeLand
Scope: pre-2025 HCMC boundary

Production:
10,000 raw
10,000 interim
6,452 processed
22 columns
0 duplicate listing_id
BT2 gate: PASS

Current stage:
BT1 = done
BT2 = production done, docs need freeze/polish
BT3 = technical implementation done, gate PASS; real peer review pending
BT4 = modeling implemented, notebooks executed, gate PASS

BT4 production:
6,086 cleaned rows
4,868 train / 1,218 test
features = area_m2 + property_type + legacy_area
final model = Random Forest
CV MAE = 16.96 tỷ VNĐ
Test MAE = 16.58 tỷ VNĐ
Test RMSE = 47.71 tỷ VNĐ
Test R² = 0.451
tests = 15 passed
Streamlit demo = app/app.py

Immediate next action:
Hoàn tất peer review BT3 bằng phản hồi thật → rà final report/slide
→ rehearsal vấn đáp → đóng gói repository để nộp.
```

---

## 20. QUYẾT ĐỊNH CUỐI CÙNG

**Pipeline hiện tại là gốc của toàn bộ Final Project.**

Từ thời điểm này:

> **Không rebuild project từ đầu. Không tạo pipeline song song. Chỉ phát triển sâu dần từ pipeline hiện tại.**

Mọi phần mới của BT3, BT4, report, presentation và demo phải nối tiếp output của stage trước.

Mục tiêu cuối cùng:

```text
raw thật
→ processed có kiểm soát
→ EDA có insight
→ feature engineering có cơ sở
→ model có baseline + comparison
→ kết quả có thể giải thích
→ pipeline tái lập được
→ report/slide/demo dùng cùng một nguồn dữ liệu và logic
```

Đây là nguyên tắc phát triển chính thức cho toàn bộ phần còn lại của DAP Final Project.

