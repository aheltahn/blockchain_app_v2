# Hệ thống Truy xuất Nguồn gốc Nông sản bằng Blockchain

Đây là một hệ thống minh họa việc sử dụng công nghệ Blockchain để xây dựng một hệ thống truy xuất nguồn gốc cho chuỗi cung ứng nông sản. Ứng dụng cho phép ghi lại và xác minh thông tin sản phẩm qua từng giai đoạn, đảm bảo tính minh bạch và bất biến của dữ liệu.

---

## Tính năng chính

- **Truy xuất Toàn diện**: Người tiêu dùng có thể dễ dàng tra cứu toàn bộ lịch sử của một sản phẩm từ trang trại đến tay người tiêu dùng chỉ bằng ID sản phẩm.
- **Phân quyền Đa vai trò**: Hệ thống hỗ trợ 3 vai trò chính với các quyền hạn khác nhau:
    - **`Producer` (Nhà sản xuất/Vận chuyển/Bán lẻ)**: Chịu trách nhiệm ghi lại thông tin ở các giai đoạn khác nhau của chuỗi cung ứng (ví dụ: trồng trọt, đóng gói, vận chuyển).
    - **`Consumer` (Người tiêu dùng)**: Có quyền tra cứu thông tin, xác thực nguồn gốc sản phẩm.
    - **`Admin` (Quản trị viên)**: Quản lý toàn bộ hệ thống, có khả năng kiểm tra tính toàn vẹn của chuỗi Blockchain và reset dữ liệu để demo.
- **Ghi nhận Bất biến**: Mỗi thông tin (sự kiện) được thêm vào chuỗi cung ứng sẽ được tạo thành một "Block" và liên kết mã hóa với block trước đó, đảm bảo dữ liệu không thể bị thay đổi hoặc giả mạo.
- **Minh họa Tính toàn vẹn**: Chức năng "Tamper" dành cho Admin cho phép cố ý thay đổi dữ liệu của một block để minh họa cách hệ thống phát hiện sự can thiệp và đảm bảo tính toàn vẹn của chuỗi.
- **Tạo QR Code**: Tự động tạo mã QR cho mỗi sản phẩm để tiện cho việc tra cứu.

## Công nghệ sử dụng

- **Backend**: Python, Flask
- **Blockchain**: Logic Blockchain được tự triển khai bằng Python (SHA-256 hashing).
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Database**: Dữ liệu blockchain được lưu trữ dưới dạng tệp `chain.json` (mô phỏng một sổ cái phân tán).
- **Dependencies**: Xem chi tiết trong `requirements.txt`.

## Cài đặt và Chạy thử

1.  **Clone repository (nếu cần)**

2.  **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **(Tùy chọn) Tạo dữ liệu mẫu:**
    Chạy script này để tạo sẵn 2 sản phẩm mẫu với đầy đủ 5 giai đoạn trong chuỗi cung ứng.
    ```bash
    python seed_data.py
    ```

4.  **Khởi động ứng dụng:**
    ```bash
    python app.py
    ```
    Sau đó, truy cập vào [http://localhost:5000](http://localhost:5000) trên trình duyệt của bạn.

## Quy trình làm việc chuẩn với venv:

1. **python -m venv venv** - Tạo môi trường ảo tên là venv.
2. **.\venv\Scripts\activate** - (Trên Windows) Kích hoạt môi trường ảo. Dấu nhắc lệnh của bạn sẽ có thêm (venv) ở đầu.
3. **pip install -r requirements.txt** - Cài đặt tất cả các thư viện cần thiết vào môi trường ảo này.
4. **python app.py** - Chạy ứng dụng của bạn. hoặc **python -m flask run**
5. **deactivate** - Khi làm việc xong, gõ lệnh này để thoát khỏi môi trường ảo.
## Tài khoản Demo

| Vai trò | Tên đăng nhập | Mật khẩu |
| :--- | :--- | :--- |
| Nhà sản xuất | `producer_01` | `prod123` |
| Người tiêu dùng | `consumer` | `cons123` |
| Quản trị viên | `admin` | `admin123` |

## Kịch bản Demo

1.  **Chuẩn bị**: Chạy `python seed_data.py` để có sẵn dữ liệu của 2 sản phẩm.
2.  **Người tiêu dùng tra cứu**:
    - Đăng nhập với tài khoản `consumer`.
    - Nhập ID sản phẩm `SP20260406-001` vào ô tra cứu và nhấn "Trace".
    - Xem toàn bộ dòng thời gian và thông tin chi tiết của sản phẩm "Cà chua sạch Đà Lạt".
3.  **Admin kiểm tra và minh họa**:
    - Đăng nhập với tài khoản `admin`.
    - Nhấn nút "Validate Chain". Hệ thống sẽ báo chuỗi "Chain hợp lệ".
    - Chọn một block bất kỳ (ví dụ: block #3) và nhấn nút "Tamper".
    - Nhấn "Validate Chain" một lần nữa. Hệ thống sẽ báo lỗi, cho thấy dữ liệu đã bị can thiệp và chuỗi không còn toàn vẹn.
4.  **Nhà sản xuất thêm dữ liệu**:
    - Đăng nhập với tài khoản `producer_01` và chọn một vai trò (ví dụ: Nhà sản xuất).
    - Tạo một sản phẩm mới hoặc thêm một giai đoạn mới cho sản phẩm đã có.
    - Sau khi thêm, dữ liệu sẽ được ghi vào blockchain.

## Cấu trúc dự án

```
blockchain_app/
├── app.py              # Logic chính và các route của Flask
├── blockchain.py       # Định nghĩa class Block và Blockchain
├── seed_data.py        # Script tạo dữ liệu demo
├── chain.json          # Tệp lưu trữ dữ liệu blockchain (tự tạo khi chạy)
├── requirements.txt    # Các thư viện Python cần thiết
└── templates/          # Chứa các file HTML cho giao diện
    ├── admin.html
    ├── base.html
    ├── index.html
    ├── login.html
    ├── producer.html
    ├── scan_todo.html
    └── trace.html
```

## Hướng phát triển tiếp theo

- [ ] **Hoàn thiện tính năng Quét QR**:
    - Triển khai ứng dụng lên một nền tảng hỗ trợ HTTPS (như Render, Heroku) để trình duyệt cho phép sử dụng camera.
    - Tích hợp thư viện JavaScript (ví dụ: `html5-qrcode`) để xử lý việc quét mã QR từ camera.
    - Cập nhật logic tạo QR để mã hóa URL tra cứu trực tiếp thay vì chỉ ID sản phẩm.
- [ ] **Giao diện người dùng (UI/UX)**: Cải thiện giao diện để thân thiện và chuyên nghiệp hơn.
- [ ] **Mở rộng mô hình dữ liệu**: Thêm các trường thông tin chi tiết hơn cho sản phẩm và các giai đoạn (ví dụ: chứng nhận, hình ảnh, video).