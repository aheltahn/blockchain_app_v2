import hashlib
import json
from datetime import datetime
from pymongo import MongoClient, ASCENDING
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Cấu hình MongoDB ---
# !!! QUAN TRỌNG: Hãy dán chuỗi kết nối HOÀN CHỈNH của bạn vào đây
# Thay thế mycluster.xxxxx.mongodb.net bằng cụm cluster của bạn từ trang web MongoDB Atlas
MONGO_URI = "mongodb+srv://tranthimyhoa3125_db_user:Admin123@mycluster.22hhxtr.mongodb.net/?appName=MyCluster"
DB_NAME = "blockchain_db"
COLLECTION_NAME = "chain"
# -------------------------


class Block:
    def __init__(self, index, timestamp, data, previous_hash, nonce=0):
        self.index         = index
        self.timestamp     = timestamp
        self.data          = data  # Dữ liệu linh động, chứa mọi thứ
        self.nonce         = nonce
        self.previous_hash = previous_hash
        self.hash          = self.calculate_hash()

    @property
    def product_id(self):
        """Helper để truy cập nhanh product_id từ trong data."""
        return self.data.get("product_id")

    def calculate_hash(self):
        """
        Hash = SHA256 của các field cố định + toàn bộ dict data.
        sort_keys=True đảm bảo cùng dữ liệu → cùng hash.
        """
        block_content = {
            "index":         self.index,
            "timestamp":     self.timestamp,
            "data":          self.data,
            "nonce":         self.nonce,
            "previous_hash": self.previous_hash,
        }
        # Dumps với sort_keys=True để đảm bảo hash nhất quán
        block_string = json.dumps(block_content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(block_string.encode("utf-8")).hexdigest()

    def to_dict(self):
        """Lưu block với cấu trúc lồng nhau, nhất quán với calculate_hash."""
        return {
            "index":         self.index,
            "timestamp":     self.timestamp,
            "data":          self.data,
            "nonce":         self.nonce,
            "previous_hash": self.previous_hash,
            "hash":          self.hash,
        }



class Blockchain:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.chain = []
        self._init_db_connection()
        self._load_chain_from_db()
        if not self.chain:
            self._create_genesis_block()

    def _init_db_connection(self):
        """Khởi tạo kết nối đến MongoDB và lấy collection."""
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[DB_NAME]
            self.collection = self.db[COLLECTION_NAME]
            self.collection.create_index([("index", ASCENDING)], unique=True)
            print("✅ Kết nối MongoDB thành công.")
        except Exception as e:
            print(f"❌ Lỗi kết nối MongoDB: {e}")
            raise

    def _write_to_google_sheet(self, block):
        try:
            print("📝 Đang ghi vào Google Sheet...")
            scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
                     "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
            
            creds_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            
            client = gspread.authorize(creds)
            sheet = client.open("Blockchain Log").sheet1

            # Chuẩn bị dữ liệu để ghi
            # Chuyển đổi dữ liệu data của block thành chuỗi JSON để dễ đọc trong sheet
            data_str = json.dumps(block.data, ensure_ascii=False)
            
            row = [block.index, block.timestamp, data_str, block.previous_hash, block.hash, block.nonce]
            sheet.append_row(row)
            print("✅ Ghi vào Google Sheet thành công.")
        except Exception as e:
            print(f"❌ Lỗi khi ghi vào Google Sheet: {e}")

    def _load_chain_from_db(self):
        """Tải toàn bộ chain từ database và sắp xếp theo index."""
        try:
            chain_data = list(self.collection.find().sort("index", ASCENDING))
            self.chain = [
                Block(
                    index=b["index"],
                    timestamp=b["timestamp"],
                    data=b["data"],
                    previous_hash=b["previous_hash"],
                    nonce=b.get("nonce", 0),
                )
                for b in chain_data
            ]
            print(f"📚 Đã tải {len(self.chain)} block từ database.")
        except Exception as e:
            print(f"❌ Lỗi khi tải chain từ DB: {e}")
            self.chain = []

    # ── Genesis block ─────────────────────────────────────────────
    def _create_genesis_block(self):
        genesis_data = {
            "product_id": "GENESIS",
            "event": "Genesis",
            "actor": "system",
            "product_name": "Genesis Block",
        }
        genesis = Block(
            index=0,
            timestamp="2026-01-01 00:00:00",
            data=genesis_data,
            previous_hash="0" * 64,
        )
        self.chain.append(genesis)
        self.collection.insert_one(genesis.to_dict())

    # ── Thêm block mới ────────────────────────────────────────────
    def add_block(self, data: dict):
        """
        Thêm block mới vào chain với dữ liệu linh động.
        - Giai đoạn 1: kiểm tra product_id không được trùng.
        - Giai đoạn 2-5: kiểm tra product_id phải tồn tại.
        """
        product_id = data.get("product_id")
        event = data.get("event")
        is_first_stage = (event == "Trồng & Thu hoạch")

        if not product_id:
            raise ValueError("Product ID là bắt buộc.")

        if not is_first_stage:
            if not self.get_trace(product_id):
                raise ValueError(f"Product ID '{product_id}' chưa tồn tại trong chain.")
        else:
            if self.get_trace(product_id):
                raise ValueError(f"Product ID '{product_id}' đã tồn tại.")

        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data=data,
            previous_hash=self.chain[-1].hash,
        )
        self.chain.append(new_block)
        self.collection.insert_one(new_block.to_dict())
        self._write_to_google_sheet(new_block)
        return new_block

    # ── Tra cứu theo product_id, event, actor ───────────────────
    def get_blocks_by_event(self, event: str) -> list['Block']:
        """Lấy tất cả các block có một sự kiện (event) cụ thể."""
        return [b for b in self.chain if b.data.get("event") == event]

    def get_blocks_by_event_and_actor(self, event: str, actor: str) -> list['Block']:
        """Lấy tất cả các block có sự kiện và người tạo (actor) cụ thể."""
        return [b for b in self.chain if b.data.get("event") == event and b.data.get("actor") == actor]

    def get_trace(self, product_id: str) -> list['Block']:
        """Lấy tất cả các block liên quan đến một product_id, sắp xếp theo thời gian."""
        return sorted(
            [b for b in self.chain if b.data.get("product_id") == product_id],
            key=lambda b: b.timestamp
        )

    # ── Validate toàn bộ chain ────────────────────────────────────
    def is_valid(self):
        """
        Trả về (bool, message).
        Kiểm tra 2 điều kiện mỗi block:
          1. Hash lưu trong block == hash tính lại từ dữ liệu
          2. previous_hash == hash của block trước
        """
        for i in range(1, len(self.chain)):
            cur  = self.chain[i]
            prev = self.chain[i - 1]

            if cur.hash != cur.calculate_hash():
                return False, f"Block {i} (index={cur.index}): hash bị thay đổi!"

            if cur.previous_hash != prev.hash:
                return False, f"Block {i} (index={cur.index}): liên kết previous_hash bị đứt!"

        return True, "Chain hợp lệ — tất cả block toàn vẹn."

    # ── Tamper (chỉ dùng để demo) ─────────────────────────────────
    def tamper_block(self, index: int, field: str, value: str):
        """
        Sửa thẳng 1 field của block trong DB mà KHÔNG tính lại hash.
        → is_valid() sẽ trả về False ngay sau đó.
        Chỉ dùng cho mục đích demo tính bất biến.
        """
        if index <= 0:
            raise ValueError("Index không hợp lệ để tamper.")

        if field in ["index", "timestamp", "data", "nonce", "previous_hash"]:
            result = self.collection.update_one({"index": index}, {"$set": {field: value}})
            if result.matched_count == 0:
                raise ValueError(f"Block với index {index} không tồn tại.")
            self._load_chain_from_db()
        else:
            raise ValueError(f"Field '{field}' không tồn tại trong Block.")

    # ── Reset tamper: load lại từ DB ────────────────────────────
    def reset(self):
        """Tải lại chain từ DB để hoàn tác các thay đổi trong bộ nhớ."""
        self._load_chain_from_db()

    # ── Lấy tất cả blocks ────────────────────────────────────────
    def get_all_blocks(self):
        return self.chain

    # ── Reset toàn bộ DB ────────────────────────────────────────
    def reset_chain_in_db(self):
        """Xóa tất cả các block trong DB và tạo lại genesis block."""
        print("🔥 Đang xóa tất cả block trong database...")
        self.collection.delete_many({})
        self.chain = []
        self._create_genesis_block()