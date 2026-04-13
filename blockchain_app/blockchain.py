import hashlib
import json
import threading
from datetime import datetime

# ─── Lock toàn cục để tránh ghi đè khi nhiều request đồng thời ───
_lock = threading.Lock()


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
    CHAIN_FILE = "chain.json"

    def __init__(self):
        self.chain = []
        self._load_chain()
        if not self.chain:
            self._create_genesis_block()

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
        self._save_chain()

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

        # Nếu không phải giai đoạn 1, sản phẩm phải tồn tại
        if not is_first_stage:
            if not self.get_trace(product_id):
                raise ValueError(f"Product ID '{product_id}' chưa tồn tại trong chain.")
        # Nếu là giai đoạn 1, sản phẩm không được tồn tại
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
        self._save_chain()
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
        Sửa thẳng 1 field của block mà KHÔNG tính lại hash.
        → is_valid() sẽ trả về False ngay sau đó.
        Chỉ dùng cho mục đích demo tính bất biến.
        """
        if index <= 0 or index >= len(self.chain):
            raise ValueError("Index không hợp lệ để tamper.")
        if hasattr(self.chain[index], field):
            setattr(self.chain[index], field, value)
            self._save_chain()
        else:
            raise ValueError(f"Field '{field}' không tồn tại trong Block.")

    # ── Reset tamper: load lại từ file ────────────────────────────
    def reset(self):
        self._load_chain()

    # ── Lấy tất cả blocks ────────────────────────────────────────
    def get_all_blocks(self):
        return self.chain

    # ── Lưu / Load chain.json ─────────────────────────────────────
    def _save_chain(self):
        with _lock:
            with open(self.CHAIN_FILE, "w", encoding="utf-8") as f:
                json.dump([b.to_dict() for b in self.chain], f,
                          ensure_ascii=False, indent=2)

    def _load_chain(self):
        try:
            with open(self.CHAIN_FILE, "r", encoding="utf-8") as f:
                chain_data = json.load(f)
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
        except (FileNotFoundError, json.JSONDecodeError):
            self.chain = []