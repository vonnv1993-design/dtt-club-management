import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO

# --------------------------
# Database utilities
# --------------------------
DB_FILE = "club.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            password TEXT,
            role TEXT,
            approved INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0
        )
    """)
    # Matches (ranking wins)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            result TEXT,
            created_at TEXT
        )
    """)
    # Votes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_play TEXT,
            user_id INTEGER,
            voted INTEGER,
            created_at TEXT
        )
    """)
    # Finance
    cur.execute("""
        CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            type TEXT,
            note TEXT,
            created_at TEXT
        )
    """)
    conn.commit()

    # --- Migration: đảm bảo cột 'wins' tồn tại cho DB cũ ---
    cur.execute("PRAGMA table_info(users)")
    cols_info = cur.fetchall()
    cols = [row[1] for row in cols_info]
    if "wins" not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN wins INTEGER DEFAULT 0")
            conn.commit()
            print("✅ Added 'wins' column to users table")
        except Exception as e:
            print("⚠️ Could not add 'wins' column:", e)

    conn.close()


def add_user(name, email, phone, password, role="member"):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (name, email, phone, password, role, approved, wins)
        VALUES (?,?,?,?,?,?,?)
    """, (name, email, phone, password, role, 0, 0))
    conn.commit()
    conn.close()

def authenticate(email, password):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    row = cur.fetchone()
    conn.close()
    return row

def list_users(status_filter=None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    if status_filter == "approved":
        cur.execute("SELECT * FROM users WHERE approved=1")
    elif status_filter == "pending":
        cur.execute("SELECT * FROM users WHERE approved=0")
    else:
        cur.execute("SELECT * FROM users")
    rows = cur.fetchall()
    conn.close()
    return rows

def approve_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE users SET approved=1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def record_win(user_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE users SET wins = wins + 1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def record_vote(date_play, user_id, voted):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO votes (date_play, user_id, voted, created_at)
        VALUES (?,?,?,?)
    """, (date_play, user_id, voted, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def record_finance(user_id, amount, type_, note=""):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO finance (user_id, amount, type, note, created_at)
        VALUES (?,?,?,?,?)
    """, (user_id, amount, type_, note, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# --------------------------
# Streamlit App
# --------------------------
init_db()
st.set_page_config(page_title="Pickleball Club Management", layout="wide")

if "user" not in st.session_state:
    st.session_state["user"] = None

# --- Login / Register ---
if st.session_state["user"] is None:
    st.title("🏓 Pickleball Club Management")

    tab_login, tab_register = st.tabs(["Đăng nhập", "Đăng ký thành viên"])

    with tab_login:
        email = st.text_input("Email")
        password = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập"):
            # Admin mặc định
            if email == "admin" and password == "Admin@123":
                st.session_state["user"] = {"id": 0, "name": "Admin", "role": "admin"}
                st.experimental_rerun()
            else:
                row = authenticate(email, password)
                if row:
                    user = {
                        "id": row[0], "name": row[1], "email": row[2],
                        "phone": row[3], "password": row[4],
                        "role": row[5], "approved": row[6], "wins": row[7]
                    }
                    if user["approved"] == 1:
                        st.session_state["user"] = user
                        st.experimental_rerun()
                    else:
                        st.error("Tài khoản chưa được phê duyệt.")
                else:
                    st.error("Email hoặc mật khẩu không đúng.")

    with tab_register:
        name = st.text_input("Tên")
        email = st.text_input("Email (unique)")
        phone = st.text_input("Số điện thoại")
        password = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng ký"):
            try:
                add_user(name, email, phone, password)
                st.success("Đăng ký thành công! Vui lòng chờ quản trị viên phê duyệt.")
            except Exception as e:
                st.error(f"Lỗi: {e}")

else:
    user = st.session_state["user"]
    st.sidebar.write(f"Xin chào, **{user['name']}**")
    if st.sidebar.button("Đăng xuất"):
        st.session_state["user"] = None
        st.experimental_rerun()

    # --- Tabs ---
    tabs = ["Home", "Thành viên", "Ranking", "Vote", "Tài chính"]
    choice = st.sidebar.radio("Menu", tabs)

    # --- HOME ---
    if choice == "Home":
        st.header("📊 Dashboard")
        # Ranking chart
        conn = sqlite3.connect(DB_FILE)
        df_users = pd.read_sql_query("SELECT name, wins FROM users WHERE approved=1", conn)
        conn.close()
        if not df_users.empty:
            top_ranking = df_users.sort_values("wins", ascending=False).head(5)
            fig, ax = plt.subplots()
            ax.bar(top_ranking["name"], top_ranking["wins"])
            ax.set_title("Top Ranking")
            st.pyplot(fig)
        else:
            st.info("Chưa có dữ liệu xếp hạng.")

    # --- MEMBERS ---
    elif choice == "Thành viên":
        st.header("👥 Quản lý thành viên")
        if user["role"] == "admin":
            pending = list_users(status_filter="pending")
            if pending:
                st.subheader("Chờ phê duyệt")
                for row in pending:
                    st.write(row)
                    if st.button(f"Phê duyệt {row[1]}", key=f"approve{row[0]}"):
                        approve_user(row[0])
                        st.experimental_rerun()
            else:
                st.info("Không có thành viên chờ phê duyệt.")
        approved = list_users(status_filter="approved")
        st.subheader("Danh sách thành viên")
        if approved:
            users_df = pd.DataFrame(approved)
            users_df.columns = ["id","name","email","phone","password","role","approved","wins"]
            display_df = users_df[["id","name","email","phone","wins"]]
            st.dataframe(display_df)
        else:
            st.info("Chưa có thành viên được phê duyệt.")

    # --- RANKING ---
    elif choice == "Ranking":
        st.header("🏆 Xếp hạng thành viên")
        if user["role"] == "admin":
            all_users = list_users(status_filter="approved")
            for row in all_users:
                if st.button(f"Thêm trận thắng cho {row[1]}", key=f"win{row[0]}"):
                    record_win(row[0])
                    st.experimental_rerun()
        # Hiển thị ranking
        users_rows = list_users(status_filter="approved")
        if users_rows:
            users_df = pd.DataFrame(users_rows)
            users_df.columns = ["id","name","email","phone","password","role","approved","wins"]
            display_df = users_df[["id","name","email","phone","wins"]].sort_values("wins", ascending=False)
            st.dataframe(display_df)
        else:
            st.info("Chưa có thành viên được phê duyệt.")

    # --- VOTE ---
    elif choice == "Vote":
        st.header("🗳️ Vote tham gia chơi")
        if user["role"] == "admin":
            date_play = st.date_input("Ngày tổ chức")
            if st.button("Tạo bình chọn"):
                st.success(f"Đã tạo bình chọn cho {date_play}")
        # Thành viên vote
        date_vote = st.date_input("Ngày bạn muốn vote")
        if st.button("Vote tham gia"):
            record_vote(date_vote.isoformat(), user["id"], 1)
            st.success("Đã vote tham gia.")

    # --- FINANCE ---
    elif choice == "Tài chính":
        st.header("💰 Quản lý tài chính")
        if user["role"] == "admin":
            st.subheader("Ghi nhận đóng góp")
            member_id = st.number_input("User ID", min_value=1, step=1)
            amount = st.number_input("Số tiền", min_value=0, step=1000)
            if st.button("Ghi nhận"):
                record_finance(member_id, amount, "contribute", "Đóng góp")
                st.success("Đã ghi nhận.")
        st.subheader("Lịch sử giao dịch")
        conn = sqlite3.connect(DB_FILE)
        df_fin = pd.read_sql_query("SELECT * FROM finance", conn)
        conn.close()
        st.dataframe(df_fin)