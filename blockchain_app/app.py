from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from .blockchain import Blockchain
import qrcode
import io
import base64
from datetime import datetime

app = Flask(__name__)
app.secret_key = "blockchain_doAn_2026_secret"

# ── Khởi tạo blockchain (kết nối MongoDB) ───────────────────────
bc = Blockchain()

# ── Tài khoản hardcode ────────────────────────────────────────────
USERS = {
    "producer_01": {"password": "prod123",  "role": "producer"},
    "consumer":    {"password": "cons123",  "role": "consumer"},
    "admin":       {"password": "admin123", "role": "admin"},
}

# ── 5 giai đoạn chuỗi cung ứng ───────────────────────────────────
STAGES = [
    "Trồng & Thu hoạch",
    "Đóng gói & Kiểm định",
    "Vận chuyển",
    "Phân phối",
    "Bán lẻ / Điểm bán",
]

CATEGORIES = ["Rau củ", "Trái cây", "Thịt sạch", "Thủy sản", "Khác"]

# ── Phân quyền giai đoạn theo sub-role ───────────────────────────
# sub_role chỉ áp dụng cho tài khoản role="producer"
# consumer và admin không có sub_role
ROLE_STAGES = {
    "producer":    ["Trồng & Thu hoạch", "Đóng gói & Kiểm định"],
    "transporter": ["Vận chuyển"],
    "retailer":    ["Phân phối", "Bán lẻ"],
}

ROLE_LABELS = {
    "producer":    "Nhà sản xuất",
    "transporter": "Vận chuyển",
    "retailer":    "Đại lý / Bán lẻ",
}

# ── Helper: tạo QR base64 từ product_id ──────────────────────────
def make_qr_base64(product_id: str) -> str:
    """
    Tạo mã QR chứa URL đầy đủ để truy cập từ mạng nội bộ.
    Ví dụ: http://192.168.1.10:5000/trace/SP20260413-001
    """
    # Lấy địa chỉ IP của request để tạo URL động
    # Điều này giúp mã QR luôn đúng dù IP của bạn thay đổi
    base_url = request.host_url.replace("127.0.0.1", request.host.split(':')[0])
    url = f"{base_url}trace?product_id={product_id}"
    
    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

# ── Decorator phân quyền ──────────────────────────────────────────
def login_required(role=None):
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user" not in session:
                flash("Vui lòng đăng nhập.", "warning")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Bạn không có quyền truy cập trang này.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ════════════════════════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════════════════════════
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", user=session.get("user"), role=session.get("role"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        sub_role = request.form.get("sub_role", "").strip()  # chỉ dành cho producer
        user = USERS.get(username)
        if user and user["password"] == password:
            session["user"] = username
            session["role"] = user["role"]
            # Gán sub_role: chỉ producer mới chọn, các role khác không có
            if user["role"] == "producer":
                if sub_role not in ROLE_STAGES:
                    flash("Vui lòng chọn vai trò hợp lệ.", "danger")
                    return render_template("login.html", role_labels=ROLE_LABELS)
                session["sub_role"] = sub_role
            else:
                session["sub_role"] = None
            flash(f"Đăng nhập thành công! Xin chào {username}.", "success")
            role = user["role"]
            if role == "producer":
                return redirect(url_for("producer"))
            elif role == "admin":
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("trace"))
        flash("Sai tài khoản hoặc mật khẩu.", "danger")
    return render_template("login.html", role_labels=ROLE_LABELS)


@app.route("/logout")
def logout():
    session.clear()
    flash("Đã đăng xuất.", "info")
    return redirect(url_for("login"))


# ════════════════════════════════════════════════════════════════
#  PRODUCER — Thêm sự kiện
# ════════════════════════════════════════════════════════════════
@app.route("/producer", methods=["GET", "POST"])
@login_required(role="producer")
def producer():
    sub_role = session.get("sub_role", "producer")
    allowed_stages = ROLE_STAGES.get(sub_role, [])
    role_label = ROLE_LABELS.get(sub_role, "Nhà sản xuất")

    # ── Lấy danh sách sản phẩm do user này tạo để hiển thị ────────
    user_products = []
    if sub_role == "producer": # Chỉ "Nhà sản xuất" mới có danh sách sản phẩm
        # Lấy tất cả các block "Trồng & Thu hoạch" do user này tạo
        genesis_blocks = bc.get_blocks_by_event_and_actor("Trồng & Thu hoạch", session["user"])
        for block in genesis_blocks:
            product_id = block.data.get("product_id")
            if product_id:
                user_products.append({
                    "product_id": product_id,
                    "product_name": block.data.get("product_name", "N/A"),
                    "qr_code": make_qr_base64(product_id)
                })

    # ── Lấy thông tin sản phẩm có sẵn để điền form ───────────────
    product_info = {}
    if 'product_id' in request.args:
        product_id = request.args.get('product_id', '').strip().upper()
        trace = bc.get_trace(product_id)
        if trace:
            # Tổng hợp thông tin từ các block trước đó
            for block in trace:
                product_info.update(block.data)

    if request.method == "POST":
        submitted_event = request.form.get("event", "")

        # ── Backend validation: kiểm tra giai đoạn có được phép không ──
        if submitted_event not in allowed_stages:
            flash(f"❌ Vai trò '{role_label}' không được phép thêm giai đoạn: '{submitted_event}'.", "danger")
            return redirect(url_for('producer'))

        # ── Xây dựng dict `data` một cách linh động ────────────────
        data = {
            "event": submitted_event,
            "actor": session["user"],
        }

        # Lấy product_id từ form hoặc tự sinh
        product_id = request.form.get("product_id", "").strip().upper()
        if submitted_event == "Trồng & Thu hoạch" and not product_id:
            date_str = datetime.now().strftime("%Y%m%d")
            # Sửa logic đếm để đảm bảo ID là duy nhất
            count = len(bc.get_blocks_by_event("Trồng & Thu hoạch"))
            product_id = f"SP{date_str}-{count+1:03d}"

        data["product_id"] = product_id

        # ── Chỉ lấy những trường có trong request form ─────────────
        # Lấy tất cả các key còn lại từ form và thêm vào data nếu có giá trị
        for key, value in request.form.items():
            if key not in ["event", "product_id"] and value:
                data[key] = value.strip()

        # ── Validate cơ bản ────────────────────────────────────────
        if not data.get("product_id"):
            flash("Vui lòng điền Product ID.", "danger")
            return render_template("producer.html", stages=allowed_stages, categories=CATEGORIES, form=data, role_label=role_label, sub_role=sub_role, product_info=product_info, user_products=user_products)

        try:
            block = bc.add_block(data)
            flash(f"✅ Đã thêm block #{block.index} cho sản phẩm {block.product_id}.", "success")
            # Redirect để làm mới form và hiển thị thông tin mới
            return redirect(url_for('producer', product_id=block.product_id))
        except ValueError as e:
            flash(f"❌ Lỗi: {e}", "danger")
            return render_template("producer.html", stages=allowed_stages, categories=CATEGORIES, form=data, role_label=role_label, sub_role=sub_role, product_info=product_info, user_products=user_products)

    return render_template("producer.html",
                           stages=allowed_stages, categories=CATEGORIES,
                           form={}, role_label=role_label, sub_role=sub_role,
                           product_info=product_info, user_products=user_products)


# ════════════════════════════════════════════════════════════════
#  CONSUMER — Tra cứu sản phẩm
# ════════════════════════════════════════════════════════════════
@app.route("/trace", methods=["GET"])
def trace():
    product_id = request.args.get("product_id", "").strip().upper()
    blocks = []
    product_info = {}
    qr_b64 = None
    not_found = False

    if product_id:
        found_blocks = bc.get_trace(product_id)
        if found_blocks:
            blocks = found_blocks
            qr_b64 = make_qr_base64(product_id)
            # Tổng hợp thông tin từ tất cả các block vào một dict duy nhất
            for block in blocks:
                product_info.update(block.data)
        else:
            not_found = True

    return render_template("trace.html",
                           product_id=product_id,
                           blocks=blocks,
                           product_info=product_info,
                           qr_b64=qr_b64,
                           not_found=not_found,
                           stages=STAGES)


# ════════════════════════════════════════════════════════════════
#  ADMIN — Dashboard, Validate, Tamper
# ════════════════════════════════════════════════════════════════
@app.route("/admin")
@login_required(role="admin")
def admin():
    all_blocks = [b.to_dict() for b in bc.get_all_blocks()]
    return render_template("admin.html", blocks=all_blocks)


@app.route("/admin/validate")
@login_required(role="admin")
def validate():
    valid, message = bc.is_valid()
    return jsonify({"valid": valid, "message": message})


@app.route("/admin/tamper", methods=["POST"])
@login_required(role="admin")
def tamper():
    """
    ═══════════════════════════════════════════════════════════════
    Demo tamper: sửa location của block được chọn thành '[TAMPERED]'
    Sau đó is_valid() sẽ trả về False.
    ═══════════════════════════════════════════════════════════════
    """
    index = int(request.form.get("index", 1))
    try:
        bc.tamper_block(index, "location", f"[TAMPERED] - Dữ liệu bị sửa lúc {datetime.now().strftime('%H:%M:%S')}")
        flash(f"⚠️ Đã tamper block #{index}. Chạy Validate để kiểm tra.", "warning")
    except ValueError as e:
        flash(f"Lỗi tamper: {e}", "danger")
    return redirect(url_for("admin"))


@app.route("/admin/reset_chain", methods=["POST"])
@login_required(role="admin")
def reset_chain():
    """Xóa chain trong database và tạo lại genesis block — dùng khi muốn demo từ đầu."""
    global bc
    try:
        # Gọi hàm reset mới trong lớp Blockchain để xóa collection trong DB
        bc.reset_chain_in_db()

        # Khởi tạo lại đối tượng blockchain để nạp lại genesis block mới vào bộ nhớ
        bc = Blockchain()

        flash("✅ Đã reset chain trong database về genesis block.", "success")
    except Exception as e:
        flash(f"❌ Có lỗi xảy ra khi reset chain: {e}", "danger")
    return redirect(url_for("admin"))


# ════════════════════════════════════════════════════════════════
#  QR SCAN — Để sau
# ════════════════════════════════════════════════════════════════
@app.route("/scan")
@login_required(role="consumer")
def scan():
    """
    ███████████████████████████████████████████████████████████████
    ██                                                           ██
    ██   TÍNH NĂNG QUÉT MÃ QR — CHƯA TRIỂN KHAI                  ██
    ██                                                           ██
    ██   Cần HTTPS để trình duyệt cho phép truy cập camera.      ██
    ██   Bước tiếp theo sau khi deploy lên Render.com:           ██
    ██                                                           ██
    ██   1. Thêm html5-qrcode vào templates/scan.html            ██
    ██   2. Dùng Html5QrcodeScanner để scan QR                   ██
    ██   3. Khi scan xong, redirect đến /trace?product_id=xxx    ██
    ██   4. Đổi make_qr_base64() để encode URL thay vì text      ██
    ██                                                           ██
    ███████████████████████████████████████████████████████████████
    """
    return render_template("scan_todo.html")


# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)