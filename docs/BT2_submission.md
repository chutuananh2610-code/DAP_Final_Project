# BÀI TẬP 2 — Thu thập & Tổ chức Dữ liệu

## 1. Kiến trúc thu thập

```text
CafeLand search pages
        ↓
pagination /page-N/
        ↓
listing cards
        ↓
checkpoint raw CSV
        ↓
optional detail enrichment
        ↓
raw CSV/JSON
        ↓
NumPy/Pandas normalization
        ↓
legacy HCMC scope filter
        ↓
interim
        ↓
initial validation + dedup
        ↓
processed
```

## 2. Module hóa

- `cafeland_crawler.py`: session, retry, robots, rate-limit, pagination, card/detail acquisition.
- `parsers.py`: giá, diện tích, bedrooms, property type, detail labels.
- `scope.py`: TP.HCM cũ.
- `organize.py`: Pandas/NumPy, data quality, CSV/JSON/Parquet, benchmark.
- `pipelines/acquisition.py`: orchestration.
- `scripts/run_all.py`: command-line entry point.

## 3. Pilot đã kiểm tra

Gói hiện chứa **13 record pilot đã đối chiếu công khai**, dùng để kiểm thử schema.
Không có dữ liệu giả.

## 4. Lệnh production

```bash
python scripts/run_all.py --stage acquisition --max-records 6500
python scripts/run_all.py --stage quality
```

Khuyến nghị crawl search cards trước. Chỉ bật `--enrich-details` sau khi kiểm tra rate-limit/robots/điều khoản.

## 5. Pandas + NumPy

Notebook 02:
- `.isna().mean()`
- duplicate checks
- vectorized `np.divide`
- CSV/JSON/Parquet
- benchmark size/read time

## 6. Data Dictionary & quality

- `docs/data_dictionary.md`
- `docs/data_quality_initial.md`
- `docs/data_feasibility.md`

## 7. Gate chính thức

Bài tập 2 chỉ được đánh dấu **hoàn thành về quy mô** khi production processed:
- `>= 5,000` rows
- `>= 8` variables

Môi trường tạo ZIP không có network trực tiếp tới CafeLand nên production crawl chưa thể chạy tại đây.
Pipeline đã được chuẩn bị để nhóm chạy tại máy cá nhân mà không thay đổi kiến trúc project.
