# data/raw

Thư mục chứa dữ liệu gốc thu thập từ CafeLand.

Các file production và checkpoint trong thư mục này không được commit lên GitHub để tránh làm repository nặng và để tôn trọng nguyên tắc không phát hành lại raw data khi chưa xác định quyền sử dụng phù hợp.

Có thể tái tạo dữ liệu bằng:

```bash
python scripts/run_all.py --stage acquisition --max-records 6500
```

Sau khi crawl, pipeline sẽ tiếp tục tạo dữ liệu interim và processed theo cấu trúc dự án.
