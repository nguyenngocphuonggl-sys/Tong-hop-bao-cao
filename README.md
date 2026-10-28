# Tổng Hợp Báo Cáo Thu Qua Ngân Hàng

Ứng dụng quản trị và tổng hợp phân tích báo cáo thu qua ngân hàng / tổ chức trung gian thanh toán (TCTG).

## Cấu trúc dự án
- `server.py`: Máy chủ web Flask phục vụ giao diện và API phân tích.
- `data_engine.py`: Xử lý nạp dữ liệu từ Excel (`Ngan hang 2026.xlsm`) và quản lý bộ nhớ cache (`data_cache.json`).
- `analytics_engine.py`: Tính toán các chỉ số thống kê, biến động, phân loại ngân hàng theo từng đơn vị và từng tháng.
- `export_engine.py`: Xuất báo cáo ra định dạng Excel (`.xlsx`) và Word (`.docx`).
- `import_engine.py`: Bộ phân tích và trích xuất dữ liệu thô SQL CMIS.
- `static/`: Giao diện Dashboard trực quan (HTML, CSS, JS, biểu đồ Chart.js).
- `Khoi_Dong_Bao_Cao.bat`: File chạy nhanh ứng dụng chỉ bằng 1 cú nhấp đúp chuột.

## Hướng dẫn sử dụng
1. Nhấp đúp vào tệp `Khoi_Dong_Bao_Cao.bat` để khởi động chương trình.
2. Mở trình duyệt và truy cập: `http://localhost:5000`
