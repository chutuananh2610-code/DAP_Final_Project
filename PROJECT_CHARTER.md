# PROJECT CHARTER — BQ01

**Tên dự án:** HCMC Real Estate Sale Price Prediction using CafeLand  
**Nhóm:** 4  
**Thành viên:** Chu Tuấn Anh (24650541), Đinh Duy Đức, Dương Trừng Hân

## Vấn đề & Business Question

Thị trường bất động sản có mức giá rao bán biến động mạnh theo vị trí, loại hình và đặc điểm tài sản. Dự án đặt câu hỏi:

> **Dựa trên vị trí, loại hình và các đặc điểm của bất động sản tại TP.HCM, có thể ước tính mức giá rao bán hợp lý của một bất động sản hay không?**

Bài toán được mô hình hóa dưới dạng **regression**, với target chính là `price_vnd`.

## Mục tiêu

1. Thu thập và tổ chức tối thiểu 5.000 tin bán bất động sản, tối thiểu 8 biến.
2. Đánh giá tính khả thi và chất lượng trường dữ liệu thực tế của CafeLand.
3. EDA để xác định yếu tố liên hệ mạnh với giá và quyết định feature engineering.
4. So sánh ít nhất hai mô hình hồi quy ở giai đoạn modeling.
5. Diễn giải kết quả theo góc nhìn người mua/môi giới/nhà đầu tư.

## Câu hỏi nghiên cứu

**RQ chính:** Những đặc điểm nào cho phép ước tính `price_vnd` của tin bán BĐS trong phạm vi nghiên cứu?

**RQ phụ 1:** Quan hệ giữa diện tích và giá có khác theo `property_type` và khu vực hay không?

**RQ phụ 2:** Vị trí và loại hình BĐS cải thiện dự báo giá đến mức nào so với baseline chỉ dùng diện tích?

## Đối tượng & phạm vi dữ liệu

- Nguồn chính: `https://nhadat.cafeland.vn/`
- Giao dịch: bán.
- Không giới hạn ngày đăng; lưu `listing_date`.
- Không gian: **phần lãnh thổ TP.HCM trước sáp nhập cấp tỉnh năm 2025**.
- Vì nhãn TP.HCM hiện tại của CafeLand bao gồm cả khu vực ngoài ranh giới cũ, dữ liệu được lọc bằng whitelist đơn vị cấp xã hình thành từ địa bàn TP.HCM cũ và từ khóa quận/huyện lịch sử.
- Raw giữ nguyên thông tin nguồn; processed chỉ giữ record qua validation.

## Biến mục tiêu

`price_vnd`: giá rao bán, chuẩn hóa về VNĐ.

Không dùng `price_per_m2` làm feature đầu vào vì `price_per_m2 = price_vnd / area_m2`, gây target leakage.

## Rủi ro chính & kiểm soát

- **Thay đổi HTML:** parser theo label + regex, có fallback và unit tests.
- **429/mất kết nối:** retry/backoff, rate limit, checkpoint.
- **Robots/điều khoản:** crawler kiểm tra robots, chỉ thu trường phục vụ học thuật, không lấy ảnh/thông tin liên hệ.
- **Nhầm phạm vi địa lý sau sáp nhập:** whitelist ranh giới cũ + `scope_status`.
- **Giá “Thỏa thuận”:** giữ raw, loại khỏi modeling target.
- **Area không đồng nhất:** một số nhà riêng hiển thị tổng diện tích sàn thay vì diện tích đất; giữ raw và gắn quality flag để xử lý ở Bài 3.
- **Duplicate:** khóa ưu tiên `listing_id`, fallback canonical URL.
- **Leakage từ text:** title/description không dùng trong model v1.

## Phân công

- **Chu Tuấn Anh:** Team Lead; crawler, integration, reproducibility.
- **Đinh Duy Đức:** Pandas/NumPy, chuẩn hóa dữ liệu, Data Dictionary, quality checks.
- **Dương Trừng Hân:** khảo sát nguồn, xác thực sample, kiểm thử, tài liệu & peer review.

**Kế hoạch Bài 2:** Pilot → kiểm tra schema → crawl production → quality gate → freeze schema → chuyển Bài 3.
