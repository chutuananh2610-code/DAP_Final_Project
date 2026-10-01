# AI USAGE DISCLOSURE

Dự án có sử dụng ChatGPT như công cụ hỗ trợ theo chính sách của học phần.

## Các phần được AI hỗ trợ

- Gợi ý cấu trúc repository giữ đúng pipeline `DAP_Final_Project`.
- Gợi ý kiến trúc crawler, retry/backoff, checkpoint và parser.
- Gợi ý regex chuẩn hóa giá/diện tích.
- Gợi ý cách tổ chức Pandas/NumPy, Data Dictionary và quality report.
- Gợi ý test cases, README và Project Charter.
- Hỗ trợ rà soát nguy cơ data leakage.
- Hỗ trợ khảo sát sự thay đổi phạm vi hành chính và thiết kế logic lọc “TP.HCM cũ”.

## Các phần AI không được dùng để thay thế dữ liệu thật

- Không sinh dữ liệu giả để đạt mốc 5.000 dòng.
- Không tự bịa kết quả missing rate/duplicate rate của dataset production.
- Pilot đi kèm chỉ chứa các record đã được đối chiếu với trang CafeLand công khai.
- Chỉ số production chỉ được ghi nhận sau khi crawler chạy thật.

## Trách nhiệm của nhóm

Mỗi thành viên phải:
1. đọc và hiểu phần code mình phụ trách;
2. có thể giải thích thuật toán, regex và quyết định xử lý dữ liệu;
3. tự chạy lại pipeline;
4. sửa code khi website thay đổi;
5. minh bạch mọi thay đổi do AI gợi ý.

AI được dùng như trợ lý tra cứu/gợi ý, không thay thế trách nhiệm học thuật của sinh viên.

## Bài tập 3 — EDA & trực quan hóa

AI hỗ trợ nhóm rà soát kiến trúc stage EDA, gợi ý chiến lược phân tích missing/outlier, tổ chức hàm trực quan hóa, sinh báo cáo tái lập và viết test chống target leakage.

Các quyết định cuối cùng vẫn dựa trên production thật. Mọi số liệu 6.452 input, 6.086 cleaned, số outlier, missing rate, biểu đồ và insight đều được tính bằng code chạy trên dataset của nhóm, không do AI bịa ra.

AI không thay thế peer review chéo. Phản hồi trong `docs/peer_review.md` chỉ được điền sau khi nhóm khác thực sự review.

Nhóm chịu trách nhiệm hiểu và giải thích được: log-scale, IQR theo nhóm, quy tắc 2/3 cờ ngoại lai, lý do không impute missing cấu trúc, và lý do loại các feature target-derived khỏi model v1.

## Bài tập 4 — Feature engineering, modeling và demo

AI hỗ trợ gợi ý kiến trúc `Pipeline/ColumnTransformer`, leakage guard, baseline, cross-validation, tuning Ridge/Decision Tree/Random Forest, error analysis, learning curve, model interpretation, test cases và khung Streamlit.

AI không tự tạo hoặc bịa metric. Các kết quả BT4 được ghi vào báo cáo chỉ sau khi chạy thật trên cleaned production 6.086 dòng. Run hiện tại chọn Random Forest theo CV MAE; holdout MAE 16,58 tỷ VNĐ, RMSE 47,71 tỷ VNĐ và R² 0,451 là output do code tính trên test set 1.218 dòng.

Nhóm chịu trách nhiệm hiểu và giải thích được: train/test split, lý do preprocessing chỉ fit trên train, OneHotEncoder, StandardScaler, cross-validation, regularization Ridge, tuning cây/Random Forest, MAE/RMSE/R², generalization gap, learning curve, permutation importance và giới hạn của việc dùng giá rao làm target.

Streamlit chỉ là demo ước tính từ dữ liệu giá rao CafeLand; không được diễn giải là chứng thư thẩm định giá hoặc giá giao dịch chắc chắn.
