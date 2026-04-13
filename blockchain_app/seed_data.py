"""
seed_data.py
────────────
Chạy script này để tạo sẵn data demo trước khi bảo vệ.
Tạo 2 sản phẩm, mỗi sản phẩm đủ 5 giai đoạn.

Cách dùng:
    python seed_data.py

Sau khi chạy xong, mở app.py và đăng nhập Consumer để trace thử.
"""

import os, json
from blockchain import Blockchain

# Xóa chain cũ nếu có
if os.path.exists("chain.json"):
    os.remove("chain.json")

bc = Blockchain()

# ── Sản phẩm 1: Cà chua sạch Đà Lạt ──────────────────────────
product_1 = [
    {
        "product_id":       "SP20260406-001",
        "product_name":     "Cà chua sạch Đà Lạt",
        "product_category": "Rau củ",
        "event":            "Trồng & Thu hoạch",
        "location":         "Trang trại Phúc Lâm, Đà Lạt",
        "actor":            "producer_01",
        "temperature":      "22°C",
        "humidity":         "80%",
        "quality_note":     "Đạt chuẩn VietGAP, không thuốc trừ sâu",
    },
    {
        "product_id":       "SP20260406-001",
        "product_name":     "Cà chua sạch Đà Lạt",
        "product_category": "Rau củ",
        "event":            "Đóng gói & Kiểm định",
        "location":         "Kho đóng gói Đà Lạt",
        "actor":            "producer_01",
        "temperature":      "18°C",
        "humidity":         "70%",
        "quality_note":     "Kiểm định GlobalGAP, đạt tiêu chuẩn xuất khẩu",
    },
    {
        "product_id":       "SP20260406-001",
        "product_name":     "Cà chua sạch Đà Lạt",
        "product_category": "Rau củ",
        "event":            "Vận chuyển",
        "location":         "Đà Lạt → TP.HCM (xe lạnh)",
        "actor":            "producer_01",
        "temperature":      "8°C",
        "humidity":         "65%",
        "quality_note":     "Xe lạnh đạt chuẩn, thời gian vận chuyển 6 giờ",
    },
    {
        "product_id":       "SP20260406-001",
        "product_name":     "Cà chua sạch Đà Lạt",
        "product_category": "Rau củ",
        "event":            "Đến đại lý / Siêu thị",
        "location":         "Siêu thị VinMart Quận 1, TP.HCM",
        "actor":            "producer_01",
        "temperature":      "12°C",
        "humidity":         "68%",
        "quality_note":     "Kiểm tra thực tế tại kho siêu thị, đạt yêu cầu",
    },
    {
        "product_id":       "SP20260406-001",
        "product_name":     "Cà chua sạch Đà Lạt",
        "product_category": "Rau củ",
        "event":            "Bán lẻ / Điểm bán",
        "location":         "Quầy rau củ — VinMart Quận 1, TP.HCM",
        "actor":            "producer_01",
        "temperature":      "15°C",
        "humidity":         "70%",
        "quality_note":     "Lên kệ ngày 06/04/2026, hạn sử dụng 5 ngày",
    },
]

# ── Sản phẩm 2: Xoài cát Hòa Lộc ─────────────────────────────
product_2 = [
    {
        "product_id":       "SP20260406-002",
        "product_name":     "Xoài cát Hòa Lộc",
        "product_category": "Trái cây",
        "event":            "Trồng & Thu hoạch",
        "location":         "Vườn xoài Hòa Lộc, Tiền Giang",
        "actor":            "producer_01",
        "temperature":      "30°C",
        "humidity":         "85%",
        "quality_note":     "Thu hoạch đúng độ chín, không chất kích thích",
    },
    {
        "product_id":       "SP20260406-002",
        "product_name":     "Xoài cát Hòa Lộc",
        "product_category": "Trái cây",
        "event":            "Đóng gói & Kiểm định",
        "location":         "Cơ sở đóng gói Tiền Giang",
        "actor":            "producer_01",
        "temperature":      "25°C",
        "humidity":         "75%",
        "quality_note":     "Đạt tiêu chuẩn VietGAP, trọng lượng 300-400g/quả",
    },
    {
        "product_id":       "SP20260406-002",
        "product_name":     "Xoài cát Hòa Lộc",
        "product_category": "Trái cây",
        "event":            "Vận chuyển",
        "location":         "Tiền Giang → TP.HCM",
        "actor":            "producer_01",
        "temperature":      "15°C",
        "humidity":         "70%",
        "quality_note":     "Vận chuyển xe lạnh, đảm bảo không dập",
    },
    {
        "product_id":       "SP20260406-002",
        "product_name":     "Xoài cát Hòa Lộc",
        "product_category": "Trái cây",
        "event":            "Đến đại lý / Siêu thị",
        "location":         "Siêu thị Co.opMart Quận 3, TP.HCM",
        "actor":            "producer_01",
        "temperature":      "18°C",
        "humidity":         "72%",
        "quality_note":     "Nhập kho, kiểm tra số lượng và chất lượng đạt",
    },
    {
        "product_id":       "SP20260406-002",
        "product_name":     "Xoài cát Hòa Lộc",
        "product_category": "Trái cây",
        "event":            "Bán lẻ / Điểm bán",
        "location":         "Quầy trái cây — Co.opMart Quận 3, TP.HCM",
        "actor":            "producer_01",
        "temperature":      "20°C",
        "humidity":         "68%",
        "quality_note":     "Lên kệ ngày 06/04/2026, hạn 7 ngày",
    },
]

for data in product_1 + product_2:
    block = bc.add_block(data)
    print(f"  ✅  Block #{block.index:02d} | {block.product_id} | {block.event}")

# Kiểm tra chain hợp lệ
valid, msg = bc.is_valid()
print(f"\n{'✅' if valid else '❌'}  is_valid(): {msg}")
print(f"📦  Tổng {len(bc.get_all_blocks())} blocks trong chain.json")
print("\nData seed xong! Chạy: python app.py")
