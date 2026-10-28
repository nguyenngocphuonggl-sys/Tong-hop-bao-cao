# Tổng Hợp Báo Cáo Thu Qua Ngân Hàng

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/nguyenngocphuonggl-sys/Tong-hop-bao-cao)

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

### 1. Chạy trên máy tính cá nhân (Offline / Local)
- Nhấp đúp vào tệp `Khoi_Dong_Bao_Cao.bat` để khởi động chương trình.
- Trình duyệt sẽ tự động mở trang: `http://localhost:5678`

### 2. Chạy trực tiếp trên Web (GitHub Codespaces)
- Trên kho lưu trữ GitHub, nhấn nút `<> Code` -> chuyển sang tab **Codespaces** -> chọn **Create codespace on main**.
- Mở Terminal và gõ:
  ```bash
  python server.py
  ```
- Codespaces sẽ tự động bật cửa sổ xem trước ứng dụng web với đầy đủ chức năng.

### 3. Triển khai 24/7 Miễn phí lên Render.com
- Đăng nhập vào [Render.com](https://render.com) bằng tài khoản GitHub.
- Nhấn **New +** -> **Web Service** -> Chọn kho lưu trữ `Tong-hop-bao-cao`.
- Render sẽ tự động nhận diện `render.yaml` và triển khai ứng dụng lên đường link online miễn phí 24/7.

