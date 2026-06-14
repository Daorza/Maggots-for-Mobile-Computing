import sqlite3
import hashlib
import os
from datetime import datetime
import streamlit as st
from config import AUTH_DB_FILE


# ─────────────────────────────────────────────────────────────────────────────
# DB helpers (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(AUTH_DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def hash_password(password, salt):
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def verify_user(email, password):
    conn = sqlite3.connect(AUTH_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, salt, password_hash FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    if user:
        user_id, name, user_email, salt, password_hash = user
        if password_hash == hash_password(password, salt):
            return {"id": user_id, "name": name, "email": user_email}
    return None


def register_user(name, email, password):
    conn = sqlite3.connect(AUTH_DB_FILE)
    c = conn.cursor()
    try:
        salt = os.urandom(16).hex()
        pwd_hash = hash_password(password, salt)
        created_at = datetime.now().isoformat(timespec="seconds")
        c.execute(
            "INSERT INTO users (name, email, salt, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, email, salt, pwd_hash, created_at),
        )
        conn.commit()
        return True, "Akun berhasil dibuat. Silakan login."
    except sqlite3.IntegrityError:
        return False, "Email sudah terdaftar."
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Auth UI — redesigned
# ─────────────────────────────────────────────────────────────────────────────
def render_auth():
    init_db()

    # Full-page centered layout
    st.markdown(
        """
        <style>
        .stApp { background: #f1f5f9 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _left, center, _right = st.columns([1, 1.1, 1])
    with center:
        with st.container(border=True):
            # ── Brand ────────────────────────────────────────────────────
            st.markdown(
                """
                <div style="text-align:center;padding:8px 0 4px;">
                  <div style="font-size:36px;margin-bottom:8px;">🌿</div>
                  <div style="font-size:24px;font-weight:700;color:#0f172a;
                               letter-spacing:-0.02em;line-height:1.2;">
                    Smart Maggot Farming
                  </div>
                  <div style="font-size:13px;color:#64748b;margin-top:6px;margin-bottom:24px;">
                    Platform monitoring BSF berbasis IoT & AI
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ── Tabs ──────────────────────────────────────────────────────
            login_tab, register_tab = st.tabs(["🔑  Login", "✨  Register"])

            # ── Login ──────────────────────────────────────────────────────
            with login_tab:
                st.markdown("<br>", unsafe_allow_html=True)
                with st.form("login_form"):
                    email    = st.text_input("Email", placeholder="nama@email.com")
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    submitted = st.form_submit_button(
                        "Masuk ke Dashboard", use_container_width=True
                    )
                if submitted:
                    email = email.strip().lower()
                    user = verify_user(email, password)
                    if user:
                        st.session_state["logged_in"] = True
                        st.session_state["user"]      = user
                        st.session_state["page"]      = "Dashboard"
                        st.rerun()
                    else:
                        st.error("Email atau password salah. Coba lagi.")

            # ── Register ───────────────────────────────────────────────────
            with register_tab:
                st.markdown("<br>", unsafe_allow_html=True)
                with st.form("register_form"):
                    name         = st.text_input("Nama Lengkap", placeholder="John Doe")
                    reg_email    = st.text_input("Email", placeholder="nama@email.com")
                    reg_password = st.text_input("Password", type="password",
                                                 placeholder="Min. 8 karakter")
                    confirm      = st.text_input("Konfirmasi Password", type="password",
                                                 placeholder="Ulangi password")
                    registered   = st.form_submit_button(
                        "Buat Akun", use_container_width=True
                    )
                if registered:
                    reg_email = reg_email.strip().lower()
                    if not name or not reg_email or not reg_password:
                        st.error("Semua kolom wajib diisi.")
                    elif len(reg_password) < 8:
                        st.error("Password minimal 8 karakter.")
                    elif reg_password != confirm:
                        st.error("Konfirmasi password tidak cocok.")
                    else:
                        success, msg = register_user(name, reg_email, reg_password)
                        if success:
                            st.success(f"✅ {msg}")
                        else:
                            st.error(msg)

            # ── Footer ─────────────────────────────────────────────────────
            st.markdown(
                '<div style="text-align:center;font-size:11px;color:#94a3b8;'
                'padding-top:16px;border-top:1px solid #e2e8f0;margin-top:8px;">'
                'Smart Maggot Farming © 2025</div>',
                unsafe_allow_html=True,
            )
