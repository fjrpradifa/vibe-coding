import os
import sqlite3
from pathlib import Path
from datetime import datetime
from flask import Flask, request, redirect, url_for, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "radif-finance-secret-key-tro-undip"

# Konfigurasi path database (Gunakan /tmp saat di-deploy ke Vercel)
if os.environ.get("VERCEL"):
    DB = Path("/tmp/radif_finance.db")
else:
    DB = Path(__file__).resolve().parent.parent / "radif_finance.db"

KATEGORI_PEMASUKAN = [
    "Uang Saku / Bulanan",
    "Gaji / Proyek",
    "Beasiswa",
    "Hadiah / Bonus",
    "Lain-lain"
]

KATEGORI_PENGELUARAN = [
    "Makan & Minum",
    "Transport & Bensin",
    "Kuliah & Alat Lab",
    "Kost & Tagihan",
    "Paket Data & Pulsa",
    "Hiburan",
    "Lain-lain"
]

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # 1. Tabel Pengguna (Multi-User)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            anggaran_bulanan INTEGER DEFAULT 0
        )
    """)
    # 2. Tabel Transaksi Keuangan
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tanggal TEXT NOT NULL,
            jenis TEXT NOT NULL,
            kategori TEXT NOT NULL,
            nominal INTEGER NOT NULL,
            keterangan TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    # 3. Tabel Target Tabungan
    cur.execute("""
        CREATE TABLE IF NOT EXISTS saving_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nama TEXT NOT NULL,
            target INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def format_rupiah(nominal):
    return f"Rp {nominal:,.0f}".replace(",", ".")

# --- STYLING MODERN (UI / UX) ---
CSS_STYLE = """
<style>
    :root {
        --primary: #0284c7;
        --primary-light: #e0f2fe;
        --primary-dark: #0369a1;
        --bg: #f8fafc;
        --surface: #ffffff;
        --text: #0f172a;
        --text-muted: #64748b;
        --border: #e2e8f0;
        --danger: #ef4444;
        --success: #10b981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
    body { background-color: var(--bg); color: var(--text); display: flex; min-height: 100vh; }
    aside { width: 250px; background: var(--surface); border-right: 1px solid var(--border); padding: 24px 20px; display: flex; flex-direction: column; gap: 20px; position: fixed; height: 100vh; }
    .brand { text-decoration: none; color: var(--primary); font-weight: 800; font-size: 20px; }
    .brand small { display: block; font-size: 11px; color: var(--text-muted); font-weight: normal; margin-top: 2px; }
    .nav-links { display: flex; flex-direction: column; gap: 6px; }
    .nav-links a { text-decoration: none; color: var(--text); padding: 10px 12px; border-radius: 8px; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    .nav-links a:hover, .nav-links a.active { background: var(--primary-light); color: var(--primary); }
    .user-box { margin-top: auto; padding-top: 14px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
    .logout-btn { color: var(--danger); text-decoration: none; font-size: 12px; font-weight: 600; }
    
    main { margin-left: 250px; flex: 1; padding: 32px 40px; max-width: 1040px; }
    .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
    .stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
    .stat-card .label { font-size: 12px; color: var(--text-muted); font-weight: 600; }
    .stat-card strong { display: block; font-size: 20px; margin-top: 6px; }
    
    .content-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 20px; margin-bottom: 20px; }
    .card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th { text-align: left; padding: 10px; color: var(--text-muted); border-bottom: 1px solid var(--border); }
    td { padding: 12px 10px; border-bottom: 1px solid var(--border); }
    
    .badge { font-size: 10px; padding: 4px 8px; border-radius: 6px; font-weight: 700; }
    .badge.PEMASUKAN { background: #dcfce7; color: #15803d; }
    .badge.PENGELUARAN { background: #fee2e2; color: #b91c1c; }
    .badge.MUTASI_SIMPAN, .badge.MUTASI_TARIK { background: #e0f2fe; color: #0369a1; }
    
    .btn { background: var(--primary); color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; text-decoration: none; font-size: 13px; display: inline-block; }
    .form-group { margin-bottom: 14px; }
    .form-group label { display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px; }
    .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; }
    .progress-bar { background: #e2e8f0; height: 8px; border-radius: 10px; overflow: hidden; margin: 10px 0; }
    .progress-fill { height: 100%; background: var(--primary); }
</style>
"""

# --- TEMPLATE HALAMAN AUTENTIKASI ---
AUTH_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>{{ title }} - RADIF FINANCE</title>
    {{ css|safe }}
</head>
<body style="align-items: center; justify-content: center;">
    <div style="background: white; border: 1px solid var(--border); border-radius: 16px; padding: 32px; width: 100%; max-width: 360px;">
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="font-size: 24px; font-weight: 800; color: var(--primary);">RADIF FINANCE</div>
            <div style="font-size: 12px; color: var(--text-muted);">Smart Student Cashflow Manager</div>
        </div>
        <h2 style="font-size: 18px; margin-bottom: 16px;">{{ heading }}</h2>
        {% if error %}
            <div style="background: #fee2e2; color: #dc2626; font-size: 12px; padding: 8px; border-radius: 6px; margin-bottom: 12px;">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>Username / NIM</label>
                <input type="text" name="username" placeholder="Masukkan username" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" placeholder="Masukkan password" required>
            </div>
            <button class="btn" style="width: 100%;" type="submit">{{ btn_text }}</button>
        </form>
        <div style="text-align: center; margin-top: 18px; font-size: 12px;">
            {% if title == 'Login' %}
                Belum punya akun? <a href="/register" style="color: var(--primary); font-weight: 600;">Daftar di sini</a>
            {% else %}
                Sudah punya akun? <a href="/login" style="color: var(--primary); font-weight: 600;">Masuk di sini</a>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# --- ROUTES AUTENTIKASI ---
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username and password:
            try:
                conn = get_db()
                conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                             (username, generate_password_hash(password)))
                conn.commit()
                conn.close()
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                error = "Username sudah dipakai, pilih username lain!"
    return render_template_string(AUTH_TEMPLATE, title="Register", heading="Buat Akun Baru 💳", btn_text="Daftar", error=error, css=CSS_STYLE)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        error = "Username atau password salah!"
    return render_template_string(AUTH_TEMPLATE, title="Login", heading="Masuk ke Akun 📊", btn_text="Masuk", error=error, css=CSS_STYLE)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- LOGIKA DASHBOARD & HITUNGAN FINANSIAL ---
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    txs = conn.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    goals = conn.execute("SELECT * FROM saving_goals WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()

    # Hitung Saldo & Cashflow
    saldo_operasional = 0
    saldo_tabungan = 0
    total_in = 0
    total_out = 0
    bulan_kini = datetime.now().strftime("%Y-%m")

    for t in txs:
        nom = t["nominal"]
        if t["jenis"] == "PEMASUKAN":
            saldo_operasional += nom
            if t["tanggal"].startswith(bulan_kini):
                total_in += nom
        elif t["jenis"] == "PENGELUARAN":
            saldo_operasional -= nom
            if t["tanggal"].startswith(bulan_kini):
                total_out += nom
        elif t["jenis"] == "MUTASI_SIMPAN":
            saldo_operasional -= nom
            saldo_tabungan += nom
        elif t["jenis"] == "MUTASI_TARIK":
            saldo_tabungan -= nom
            saldo_operasional += nom

    kekayaan_bersih = saldo_operasional + saldo_tabungan
    anggaran = user["anggaran_bulanan"] if user else 0
    sisa_anggaran = anggaran - total_out
    persen_anggaran = int((total_out / anggaran * 100)) if anggaran > 0 else 0

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard - RADIF FINANCE</title>
        {CSS_STYLE}
    </head>
    <body>
        <aside>
            <a href="/" class="brand">
                RADIF FINANCE
                <small>TRO UNDIP Project</small>
            </a>
            <div class="nav-links">
                <a href="/" class="active">📊 Dashboard</a>
                <a href="/add_tx">＋ Catat Transaksi</a>
                <a href="/savings">💰 Kelola Tabungan</a>
                <a href="/budget">🎯 Atur Anggaran</a>
            </div>
            <div class="user-box">
                <span>👤 <b>{session.get('username')}</b></span>
                <a href="/logout" class="logout-btn">Keluar</a>
            </div>
        </aside>

        <main>
            <div class="header-bar">
                <div>
                    <h2>Halo, {session.get('username')} 👋</h2>
                    <p style="font-size: 13px; color: var(--text-muted);">Pantau kondisi keuangan dan tabunganmu secara real-time.</p>
                </div>
                <a href="/add_tx" class="btn">＋ Transaksi Baru</a>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="label">Saldo Siap Pakai</div>
                    <strong style="color: var(--primary);">{format_rupiah(saldo_operasional)}</strong>
                </div>
                <div class="stat-card">
                    <div class="label">Tabungan Terkunci</div>
                    <strong style="color: var(--success);">{format_rupiah(saldo_tabungan)}</strong>
                </div>
                <div class="stat-card">
                    <div class="label">Pemasukan (Bulan Ini)</div>
                    <strong>{format_rupiah(total_in)}</strong>
                </div>
                <div class="stat-card">
                    <div class="label">Pengeluaran (Bulan Ini)</div>
                    <strong style="color: var(--danger);">{format_rupiah(total_out)}</strong>
                </div>
            </div>

            <div class="content-grid">
                <div>
                    <div class="card">
                        <div class="card-head">
                            <h3>Riwayat Transaksi Terakhir</h3>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Tanggal</th>
                                    <th>Kategori</th>
                                    <th>Tipe</th>
                                    <th>Nominal</th>
                                </tr>
                            </thead>
                            <tbody>
                                {"".join([f'''
                                <tr>
                                    <td>{t['tanggal']}</td>
                                    <td><b>{t['kategori']}</b><br><small style="color:var(--text-muted);">{t['keterangan']}</small></td>
                                    <td><span class="badge {t['jenis']}">{t['jenis']}</span></td>
                                    <td style="font-weight:700;">{format_rupiah(t['nominal'])}</td>
                                </tr>
                                ''' for t in txs[:6]]) if txs else '<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:20px;">Belum ada riwayat transaksi.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div>
                    <div class="card">
                        <h3>Status Anggaran</h3>
                        <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Batas bulanan: {format_rupiah(anggaran)}</p>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {min(persen_anggaran, 100)}%; background: {'var(--danger)' if persen_anggaran >= 80 else 'var(--primary)'};"></div>
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:12px;">
                            <span>Terpakai: {persen_anggaran}%</span>
                            <span>Sisa: {format_rupiah(sisa_anggaran)}</span>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Target Tabungan</h3>
                        {"".join([f'''
                        <div style="margin-top: 12px; font-size: 13px;">
                            <div style="display:flex; justify-content:space-between;">
                                <b>{g['nama']}</b>
                                <span>{format_rupiah(g['target'])}</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {min(int((saldo_tabungan / g['target']) * 100), 100) if g['target'] > 0 else 0}%;"></div>
                            </div>
                        </div>
                        ''' for g in goals]) if goals else '<p style="font-size:12px; color:var(--text-muted); margin-top:8px;">Belum ada target tabungan.</p>'}
                    </div>
                </div>
            </div>
        </main>
    </body>
    </html>
    """)

# --- ROUTE CATAT TRANSAKSI ---
@app.route("/add_tx", methods=["GET", "POST"])
def add_tx():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    error = None

    if request.method == "POST":
        jenis = request.form.get("jenis")
        kategori = request.form.get("kategori")
        nominal = int(request.form.get("nominal", 0))
        keterangan = request.form.get("keterangan", "")
        tanggal = request.form.get("tanggal", datetime.now().strftime("%Y-%m-%d"))

        # Validasi Saldo jika Pengeluaran
        if jenis == "PENGELUARAN":
            conn = get_db()
            txs = conn.execute("SELECT jenis, nominal FROM transactions WHERE user_id = ?", (user_id,)).fetchall()
            conn.close()
            saldo = sum(t["nominal"] if t["jenis"] in ["PEMASUKAN", "MUTASI_TARIK"] else -t["nominal"] for t in txs)
            if nominal > saldo:
                error = f"Saldo operasional tidak cukup! (Sisa saldo: {format_rupiah(saldo)})"

        if not error and nominal > 0:
            conn = get_db()
            conn.execute(
                "INSERT INTO transactions (user_id, tanggal, jenis, kategori, nominal, keterangan) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, tanggal, jenis, kategori, nominal, keterangan)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("index"))

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="id">
    <head><meta charset="UTF-8"><title>Catat Transaksi</title>{CSS_STYLE}</head>
    <body style="align-items:center; justify-content:center;">
        <div class="card" style="width: 100%; max-width: 440px;">
            <h2 style="font-size: 18px; margin-bottom: 14px;">＋ Catat Transaksi Baru</h2>
            {"<div style='background:#fee2e2; color:#dc2626; font-size:12px; padding:8px; border-radius:6px; margin-bottom:12px;'>"+error+"</div>" if error else ""}
            <form method="POST">
                <div class="form-group">
                    <label>Jenis Transaksi</label>
                    <select name="jenis" onchange="updateKategori(this.value)">
                        <option value="PENGELUARAN">PENGELUARAN (Belanja/Bayar)</option>
                        <option value="PEMASUKAN">PEMASUKAN (Uang Masuk)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Kategori</label>
                    <select name="kategori" id="kategori-select">
                        {"".join([f'<option value="{k}">{k}</option>' for k in KATEGORI_PENGELUARAN])}
                    </select>
                </div>
                <div class="form-group">
                    <label>Nominal (Rp)</label>
                    <input type="number" name="nominal" min="1" placeholder="Contoh: 50000" required>
                </div>
                <div class="form-group">
                    <label>Tanggal</label>
                    <input type="date" name="tanggal" value="{datetime.now().strftime('%Y-%m-%d')}" required>
                </div>
                <div class="form-group">
                    <label>Keterangan</label>
                    <input type="text" name="keterangan" placeholder="Contoh: Makan siang warteg">
                </div>
                <button type="submit" class="btn" style="width:100%;">Simpan Transaksi</button>
                <div style="text-align:center; margin-top:12px;"><a href="/" style="font-size:12px; color:var(--text-muted); text-decoration:none;">Batal</a></div>
            </form>
        </div>
        <script>
            const katMasuk = {KATEGORI_PEMASUKAN};
            const katKeluar = {KATEGORI_PENGELUARAN};
            function updateKategori(val) {{
                const sel = document.getElementById("kategori-select");
                sel.innerHTML = "";
                const list = val === "PEMASUKAN" ? katMasuk : katKeluar;
                list.forEach(k => {{
                    const opt = document.createElement("option");
                    opt.value = k; opt.innerText = k;
                    sel.appendChild(opt);
                }});
            }}
        </script>
    </body>
    </html>
    """)

# --- ROUTE MUTASI TABUNGAN ---
@app.route("/savings", methods=["GET", "POST"])
def savings():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    error = None

    if request.method == "POST":
        aksi = request.form.get("aksi")
        nominal = int(request.form.get("nominal", 0))
        tgl = datetime.now().strftime("%Y-%m-%d")

        conn = get_db()
        txs = conn.execute("SELECT jenis, nominal FROM transactions WHERE user_id = ?", (user_id,)).fetchall()
        op = sum(t["nominal"] if t["jenis"] in ["PEMASUKAN", "MUTASI_TARIK"] else -t["nominal"] for t in txs)
        tab = sum(t["nominal"] if t["jenis"] == "MUTASI_SIMPAN" else (-t["nominal"] if t["jenis"] == "MUTASI_TARIK" else 0) for t in txs)

        if aksi == "SIMPAN":
            if nominal > op:
                error = "Saldo operasional tidak cukup untuk ditabung!"
            else:
                conn.execute("INSERT INTO transactions (user_id, tanggal, jenis, kategori, nominal, keterangan) VALUES (?, ?, 'MUTASI_SIMPAN', 'Tabungan', ?, 'Alokasi Tabungan')", (user_id, tgl, nominal))
                conn.commit()
        elif aksi == "TARIK":
            if nominal > tab:
                error = "Saldo tabungan tidak mencukupi untuk ditarik!"
            else:
                conn.execute("INSERT INTO transactions (user_id, tanggal, jenis, kategori, nominal, keterangan) VALUES (?, ?, 'MUTASI_TARIK', 'Tabungan', ?, 'Penarikan Tabungan')", (user_id, tgl, nominal))
                conn.commit()
        conn.close()
        if not error:
            return redirect(url_for("index"))

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="id">
    <head><meta charset="UTF-8"><title>Tabungan</title>{CSS_STYLE}</head>
    <body style="align-items:center; justify-content:center;">
        <div class="card" style="width: 100%; max-width: 440px;">
            <h2 style="font-size: 18px; margin-bottom: 14px;">💰 Kelola Dana Tabungan</h2>
            {"<div style='background:#fee2e2; color:#dc2626; font-size:12px; padding:8px; border-radius:6px; margin-bottom:12px;'>"+error+"</div>" if error else ""}
            <form method="POST">
                <div class="form-group">
                    <label>Aksi Mutasi</label>
                    <select name="aksi">
                        <option value="SIMPAN">Simpan ke Tabungan (Kunci Dana)</option>
                        <option value="TARIK">Tarik Tabungan ke Operasional</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Nominal (Rp)</label>
                    <input type="number" name="nominal" min="1" placeholder="Masukkan nominal" required>
                </div>
                <button type="submit" class="btn" style="width:100%;">Proses Mutasi</button>
                <div style="text-align:center; margin-top:12px;"><a href="/" style="font-size:12px; color:var(--text-muted); text-decoration:none;">Kembali ke Dashboard</a></div>
            </form>
        </div>
    </body>
    </html>
    """)

# --- ROUTE ATUR ANGGARAN & TARGET TABUNGAN ---
@app.route("/budget", methods=["GET", "POST"])
def budget():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]

    if request.method == "POST":
        if "anggaran" in request.form:
            anggaran_baru = int(request.form.get("anggaran", 0))
            conn = get_db()
            conn.execute("UPDATE users SET anggaran_bulanan = ? WHERE id = ?", (anggaran_baru, user_id))
            conn.commit()
            conn.close()
        elif "nama_target" in request.form:
            nama = request.form.get("nama_target")
            target = int(request.form.get("target_nominal", 0))
            conn = get_db()
            conn.execute("INSERT INTO saving_goals (user_id, nama, target) VALUES (?, ?, ?)", (user_id, nama, target))
            conn.commit()
            conn.close()
        return redirect(url_for("index"))

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="id">
    <head><meta charset="UTF-8"><title>Atur Anggaran</title>{CSS_STYLE}</head>
    <body style="align-items:center; justify-content:center;">
        <div class="card" style="width: 100%; max-width: 440px;">
            <h2 style="font-size: 18px; margin-bottom: 14px;">🎯 Anggaran & Target Finansial</h2>
            <form method="POST" style="margin-bottom: 24px;">
                <div class="form-group">
                    <label>Batas Anggaran Pengeluaran Bulanan (Rp)</label>
                    <input type="number" name="anggaran" placeholder="Contoh: 1500000" required>
                </div>
                <button type="submit" class="btn" style="width:100%;">Simpan Batas Anggaran</button>
            </form>
            <hr style="border:0; border-top:1px solid var(--border); margin:18px 0;">
            <form method="POST">
                <div class="form-group">
                    <label>Buat Target Tabungan Baru</label>
                    <input type="text" name="nama_target" placeholder="Contoh: Beli Multimeter Digital" required>
                </div>
                <div class="form-group">
                    <label>Nominal Target (Rp)</label>
                    <input type="number" name="target_nominal" placeholder="Contoh: 350000" required>
                </div>
                <button type="submit" class="btn" style="width:100%; background:var(--success);">＋ Tambah Target</button>
                <div style="text-align:center; margin-top:12px;"><a href="/" style="font-size:12px; color:var(--text-muted); text-decoration:none;">Selesai & Kembali</a></div>
            </form>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(debug=True)