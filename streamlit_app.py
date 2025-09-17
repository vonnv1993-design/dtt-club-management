# app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib
import plotly.express as px

DB_PATH = "club.db"

# ---------------------------
# Helpers: DB init & utils
# ---------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # users: status = pending / approved / rejected ; role = admin / member
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        password_hash TEXT,
        role TEXT,
        status TEXT,
        wins INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)
    # events for voting
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_date TEXT,
        title TEXT,
        created_by INTEGER,
        created_at TEXT
    )
    """)
    # votes
    cur.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        user_id INTEGER,
        vote TEXT,
        voted_at TEXT
    )
    """)
    # contributions: member contributions to club fund
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contributions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        note TEXT,
        date TEXT
    )
    """)
    # expenses per event (cost for a match)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        amount REAL,
        note TEXT,
        date TEXT
    )
    """)
    conn.commit()
    # ensure admin account exists
    cur.execute("SELECT * FROM users WHERE email = ?", ("admin@local",))
    if cur.fetchone() is None:
        admin_pw_hash = hash_password("Admin@123")
        cur.execute("""
        INSERT INTO users (name, email, phone, password_hash, role, status, wins, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Admin", "admin@local", "", admin_pw_hash, "admin", "approved", 0, datetime.utcnow().isoformat()))
        conn.commit()
    conn.close()

def hash_password(password: str):
    # simple sha256 hashing with salt
    salt = "pickleball_salt_v1"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def verify_password(password: str, password_hash: str):
    return hash_password(password) == password_hash

# ---------------------------
# Data access helpers
# ---------------------------
def create_user(name, email, phone, password):
    conn = get_conn()
    cur = conn.cursor()
    pw = hash_password(password)
    try:
        cur.execute("""
        INSERT INTO users (name, email, phone, password_hash, role, status, wins, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, pw, "member", "pending", 0, datetime.utcnow().isoformat()))
        conn.commit()
        res = True
    except sqlite3.IntegrityError:
        res = False
    conn.close()
    return res

def get_user_by_email(email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    r = cur.fetchone()
    conn.close()
    return r

def get_user_by_id(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (uid,))
    r = cur.fetchone()
    conn.close()
    return r

def list_users(status_filter=None):
    conn = get_conn()
    cur = conn.cursor()
    if status_filter:
        cur.execute("SELECT * FROM users WHERE status = ? ORDER BY created_at DESC", (status_filter,))
    else:
        cur.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def approve_user(user_id, approve=True):
    conn = get_conn()
    cur = conn.cursor()
    new_status = "approved" if approve else "rejected"
    cur.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    conn.commit()
    conn.close()

def add_win(user_id, wins_to_add=1):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET wins = wins + ? WHERE id = ?", (wins_to_add, user_id))
    conn.commit()
    conn.close()

def create_event(event_date, title, created_by):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO events (event_date, title, created_by, created_at) VALUES (?, ?, ?, ?)",
                (event_date, title, created_by, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def list_events():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events ORDER BY event_date DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def vote_event(event_id, user_id, vote_value):
    conn = get_conn()
    cur = conn.cursor()
    # upsert: if user already voted on event, update
    cur.execute("SELECT * FROM votes WHERE event_id=? AND user_id=?", (event_id, user_id))
    existing = cur.fetchone()
    if existing:
        cur.execute("UPDATE votes SET vote=?, voted_at=? WHERE id=?", (vote_value, datetime.utcnow().isoformat(), existing["id"]))
    else:
        cur.execute("INSERT INTO votes (event_id, user_id, vote, voted_at) VALUES (?, ?, ?, ?)",
                    (event_id, user_id, vote_value, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def votes_count_for_event(event_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT vote, COUNT(*) as cnt FROM votes WHERE event_id=? GROUP BY vote", (event_id,))
    rows = cur.fetchall()
    conn.close()
    return {r["vote"]: r["cnt"] for r in rows}

def get_yes_voters(event_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT u.id, u.name, u.email FROM votes v
    JOIN users u ON u.id = v.user_id
    WHERE v.event_id = ? AND v.vote = 'Yes' AND u.status = 'approved'
    """, (event_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_contribution(user_id, amount, note=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO contributions (user_id, amount, note, date) VALUES (?, ?, ?, ?)",
                (user_id, amount, note, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def add_expense(event_id, amount, note=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO expenses (event_id, amount, note, date) VALUES (?, ?, ?, ?)",
                (event_id, amount, note, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_contributions_df():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT c.id, c.user_id, u.name as user_name, c.amount, c.note, c.date
    FROM contributions c JOIN users u ON u.id = c.user_id
    ORDER BY c.date DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["id","user_id","user_name","amount","note","date"])

def get_expenses_df():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT e.id, e.event_id, ev.title as event_title, e.amount, e.note, e.date
    FROM expenses e LEFT JOIN events ev ON ev.id = e.event_id
    ORDER BY e.date DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["id","event_id","event_title","amount","note","date"])

def compute_balances():
    # balance = total_contributions - total_owed (sum shares of expenses for events user voted yes)
    conn = get_conn()
    cur = conn.cursor()
    # get all approved users
    cur.execute("SELECT id, name FROM users WHERE status='approved'")
    users = cur.fetchall()
    balances = []
    for u in users:
        uid = u["id"]
        name = u["name"]
        cur.execute("SELECT IFNULL(SUM(amount),0) as s FROM contributions WHERE user_id=?", (uid,))
        srow = cur.fetchone()
        contrib = srow["s"] if srow else 0.0
        # compute owed
        cur.execute("SELECT id FROM events")
        events = cur.fetchall()
        owed = 0.0
        for ev in events:
            ev_id = ev["id"]
            # expense amount for that event (may be multiple expense rows; sum)
            cur.execute("SELECT IFNULL(SUM(amount),0) as total FROM expenses WHERE event_id=?", (ev_id,))
            total_exp_row = cur.fetchone()
            total_exp = total_exp_row["total"] if total_exp_row else 0.0
            if total_exp <= 0:
                continue
            # number of yes voters
            cur.execute("SELECT COUNT(*) as cnt FROM votes v JOIN users u ON u.id=v.user_id WHERE v.event_id=? AND v.vote='Yes' AND u.status='approved'", (ev_id,))
            cnt_row = cur.fetchone()
            cnt = cnt_row["cnt"] if cnt_row else 0
            if cnt == 0:
                continue
            # did this user vote yes?
            cur.execute("SELECT * FROM votes WHERE event_id=? AND user_id=? AND vote='Yes'", (ev_id, uid))
            myvote = cur.fetchone()
            if myvote:
                owed += total_exp / cnt
        balance = contrib - owed
        balances.append({"user_id": uid, "name": name, "contributions": contrib, "owed": owed, "balance": balance})
    conn.close()
    return pd.DataFrame(balances)

# ---------------------------
# Streamlit App UI
# ---------------------------
st.set_page_config(page_title="Pickleball Club Management", layout="wide")
init_db()

# session management (simple)
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None  # store user dict-like from DB

st.title("🏓 Pickleball - CLB Ban CĐSCN")

# --- Authentication (sidebar) ---
with st.sidebar:
    st.header("Tài khoản")
    if st.session_state.auth_user is None:
        mode = st.selectbox("Bạn muốn", ["Đăng nhập", "Đăng ký"], index=0)
        if mode == "Đăng nhập":
            email = st.text_input("Email")
            password = st.text_input("Mật khẩu", type="password")
            if st.button("Đăng nhập"):
                user = get_user_by_email(email)
                if user and user["status"] == "approved" and verify_password(password, user["password_hash"]):
                    st.session_state.auth_user = dict(user)
                    st.success(f"Chào {user['name']} ({user['role']})")
                    st.experimental_rerun()
                elif user and user["status"] == "pending":
                    st.warning("Tài khoản của bạn đang chờ phê duyệt bởi quản trị viên.")
                else:
                    st.error("Email hoặc mật khẩu không đúng, hoặc tài khoản chưa được phê duyệt.")
        else:
            st.subheader("Form đăng ký thành viên")
            r_name = st.text_input("Họ tên")
            r_email = st.text_input("Email")
            r_phone = st.text_input("Số điện thoại")
            r_password = st.text_input("Mật khẩu", type="password")
            if st.button("Đăng ký"):
                if not (r_name and r_email and r_password):
                    st.warning("Vui lòng điền tên, email và mật khẩu.")
                else:
                    ok = create_user(r_name, r_email, r_phone, r_password)
                    if ok:
                        st.success("Đăng ký thành công. Tài khoản đang chờ phê duyệt bởi quản trị viên.")
                    else:
                        st.error("Email đã tồn tại. Vui lòng dùng email khác.")
    else:
        st.write(f"👤 {st.session_state.auth_user['name']}")
        st.write(f"📧 {st.session_state.auth_user['email']}")
        st.write(f"🔑 Role: {st.session_state.auth_user['role']}")
        if st.button("Đăng xuất"):
            st.session_state.auth_user = None
            st.experimental_rerun()

# If not logged in, show minimal info and return
if st.session_state.auth_user is None:
    st.info("Vui lòng đăng nhập hoặc đăng ký để sử dụng ứng dụng.")
    st.stop()

# load fresh user info from DB
auth_user = get_user_by_id(st.session_state.auth_user["id"])
st.session_state.auth_user = dict(auth_user)

# Top-level tabs
tabs = st.tabs(["Home", "Members", "Ranking", "Voting", "Finance", "Admin"])

# ---------------- Home ----------------
with tabs[0]:
    st.header("🏠 Home - Thống kê nhanh")
    # top ranking by wins
    users_df = pd.DataFrame(list_users(status_filter="approved"))
    if users_df.empty:
        st.info("Chưa có thành viên nào được phê duyệt.")
    else:
        users_df = users_df[['id','name','email','phone','wins']]
        users_df.columns = ['id','name','email','phone','wins']
        # TOP Ranking
        st.subheader("Top Ranking (số trận thắng)")
        top_rank = users_df.sort_values(by="wins", ascending=False).head(10)
        fig1 = px.bar(top_rank, x="name", y="wins", title="Top players by wins")
        st.plotly_chart(fig1, use_container_width=True)

        # balances
        st.subheader("Thành viên có tiền nhiều nhất (tính theo đóng góp - chi phí đã chia)")
        balances_df = compute_balances().sort_values(by="balance", ascending=False)
        if not balances_df.empty:
            fig2 = px.bar(balances_df.head(10), x="name", y="balance", title="Top balances (VNĐ)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.write("Chưa có dữ liệu tài chính.")

        # votes count per member (total yes votes)
        st.subheader("Số lần vote tham gia (tổng cộng)")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
        SELECT u.name, COUNT(*) as cnt
        FROM votes v JOIN users u ON u.id=v.user_id
        WHERE v.vote='Yes' AND u.status='approved'
        GROUP BY u.name
        ORDER BY cnt DESC
        """)
        rows = cur.fetchall()
        conn.close()
        if rows:
            vc = pd.DataFrame(rows)
            fig3 = px.bar(vc, x="name", y="cnt", title="Số lần vote Yes")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.write("Chưa có ai tham gia vote.")

# ---------------- Members ----------------
with tabs[1]:
    st.header("👥 Danh sách thành viên")
    st.subheader("Thành viên được phê duyệt")
    approved = list_users(status_filter="approved")
    if approved:
        df_approved = pd.DataFrame(approved)
        df_approved = df_approved[['id','name','email','phone','wins','created_at']]
        df_approved.columns = ['ID','Name','Email','Phone','Wins','Joined']
        st.dataframe(df_approved)
    else:
        st.write("Chưa có thành viên được phê duyệt.")

    st.subheader("Đăng ký mới (pending)")
    pending = list_users(status_filter="pending")
    if pending:
        df_pending = pd.DataFrame(pending)
        df_pending = df_pending[['id','name','email','phone','created_at']]
        df_pending.columns = ['ID','Name','Email','Phone','Requested At']
        st.dataframe(df_pending)
    else:
        st.write("Không có yêu cầu đăng ký mới.")

# ---------------- Ranking ----------------
with tabs[2]:
    st.header("🏆 Quản lý xếp hạng (Ranking)")
    st.write("Admin có thể cập nhật số trận thắng của thành viên.")
    if st.session_state.auth_user["role"] != "admin":
        st.info("Chỉ quản trị viên mới có quyền cập nhật số trận thắng.")
    members = list_users(status_filter="approved")
    if members:
        sel = {row["id"]: f"{row['name']} (wins={row['wins']})" for row in members}
        col1, col2 = st.columns([3,1])
        with col1:
            sel_id = st.selectbox("Chọn VĐV để cộng thắng", options=list(sel.keys()), format_func=lambda x: sel[x])
            add_w = st.number_input("Số trận thắng thêm", min_value=1, step=1, value=1)
            if st.button("Cộng thắng"):
                if st.session_state.auth_user["role"] == "admin":
                    add_win(sel_id, add_w)
                    st.success("Đã cập nhật số trận thắng.")
                    st.experimental_rerun()
                else:
                    st.error("Bạn không có quyền.")
        with col2:
            # show ranking table
            df_rank = pd.DataFrame(members)
            df_rank = df_rank[['id','name','wins']]
            df_rank.columns = ['ID','Name','Wins']
            df_rank = df_rank.sort_values(by="Wins", ascending=False)
            st.dataframe(df_rank)
    else:
        st.write("Chưa có thành viên được phê duyệt.")

# ---------------- Voting ----------------
with tabs[3]:
    st.header("🗳️ Vote tham gia chơi")
    st.subheader("Sự kiện hiện có")
    events = list_events()
    if events:
        ev_df = pd.DataFrame(events)
        ev_df = ev_df[['id','event_date','title','created_at']]
        ev_df.columns = ['ID','Event Date','Title','Created At']
        st.dataframe(ev_df)
    else:
        st.write("Chưa có sự kiện nào.")

    # Admin tạo event
    if st.session_state.auth_user["role"] == "admin":
        st.subheader("Tạo bình chọn mới (Admin)")
        with st.form("create_event"):
            ev_title = st.text_input("Tiêu đề (ví dụ: Tập tối thứ 7)")
            ev_date = st.date_input("Ngày sự kiện", value=date.today())
            submitted = st.form_submit_button("Tạo bình chọn")
            if submitted and ev_title:
                create_event(ev_date.isoformat(), ev_title, st.session_state.auth_user["id"])
                st.success("Đã tạo sự kiện.")
                st.experimental_rerun()

    # Member vote
    st.subheader("Tham gia bình chọn")
    events = list_events()
    if events:
        ev_map = {e["id"]: f"{e['title']} - {e['event_date']}" for e in events}
        chosen_event = st.selectbox("Chọn event để vote", options=list(ev_map.keys()), format_func=lambda x: ev_map[x])
        # show counts
        counts = votes_count_for_event(chosen_event)
        yes_cnt = counts.get("Yes", 0)
        no_cnt = counts.get("No", 0)
        st.write(f"✅ Yes: {yes_cnt}    ❌ No: {no_cnt}")
        my_vote = st.radio("Bạn có tham gia?", options=["Yes","No"])
        if st.button("Gửi vote"):
            vote_event(chosen_event, st.session_state.auth_user["id"], my_vote)
            st.success("Đã ghi nhận vote của bạn.")
            st.experimental_rerun()
    else:
        st.info("Chưa có sự kiện cho bạn vote.")

    # show voters for selected event
    if events:
        st.subheader("Danh sách người đã vote YES cho event")
        yes_voters = get_yes_voters(chosen_event)
        if yes_voters:
            dfv = pd.DataFrame(yes_voters)
            dfv = dfv[['id','name','email']]
            dfv.columns = ['ID','Name','Email']
            st.dataframe(dfv)
        else:
            st.write("Chưa có ai vote Yes.")

# ---------------- Finance ----------------
with tabs[4]:
    st.header("💰 Quản lý tài chính (VNĐ)")
    st.subheader("Ghi nhận đóng góp (Admin)")
    if st.session_state.auth_user["role"] == "admin":
        members = list_users(status_filter="approved")
        member_opts = {m["id"]: m["name"] for m in members} if members else {}
        if member_opts:
            col1, col2 = st.columns(2)
            with col1:
                sel_member = st.selectbox("Chọn thành viên", options=list(member_opts.keys()), format_func=lambda x: member_opts[x])
                amount = st.number_input("Số tiền đóng (VNĐ)", min_value=0.0, step=1000.0)
            with col2:
                note = st.text_input("Ghi chú")
                if st.button("Ghi nhận đóng góp"):
                    add_contribution(sel_member, float(amount), note)
                    st.success("Đã ghi nhận đóng góp.")
                    st.experimental_rerun()
        else:
            st.write("Chưa có thành viên để ghi nhận đóng góp.")

    st.subheader("Ghi nhận chi phí cho 1 buổi tập (Admin)")
    if st.session_state.auth_user["role"] == "admin":
        evs = list_events()
        if evs:
            ev_map = {e["id"]: f"{e['title']} - {e['event_date']}" for e in evs}
            selected_ev = st.selectbox("Chọn event để ghi chi phí", options=list(ev_map.keys()), format_func=lambda x: ev_map[x])
            expense_amt = st.number_input("Tổng chi phí (VNĐ)", min_value=0.0, step=1000.0)
            expense_note = st.text_input("Ghi chú chi phí")
            if st.button("Chia và Ghi chi phí cho event"):
                # get yes voters
                voters = get_yes_voters(selected_ev)
                if not voters:
                    st.warning("Không có ai vote Yes cho event này. Không thể chia chi phí.")
                else:
                    add_expense(selected_ev, float(expense_amt), expense_note)
                    # record: splitting will be computed in balance, contributions remain as-is
                    st.success("Đã lưu chi phí. Hệ thống sẽ tự động tính phần chia khi xem số dư.")
                    st.experimental_rerun()
        else:
            st.write("Chưa có event để ghi chi phí.")

    st.subheader("Bảng đóng góp")
    df_contrib = get_contributions_df()
    st.dataframe(df_contrib)

    st.subheader("Bảng chi phí")
    df_exp = get_expenses_df()
    st.dataframe(df_exp)

    st.subheader("Sổ cái - Số dư thành viên")
    balances = compute_balances()
    if not balances.empty:
        st.dataframe(balances)
    else:
        st.write("Chưa có dữ liệu tài chính.")

# ---------------- Admin ----------------
with tabs[5]:
    st.header("⚙️ Admin - Phê duyệt & Quản trị")
    if st.session_state.auth_user["role"] != "admin":
        st.warning("Chỉ quản trị viên mới truy cập tab này.")
    else:
        st.subheader("Phê duyệt đăng ký")
        pending = list_users(status_filter="pending")
        if pending:
            for p in pending:
                st.write(f"ID: {p['id']} | {p['name']} | {p['email']} | {p['phone']} | Đăng ký: {p['created_at']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Phê duyệt_{p['id']}"):
                        approve_user(p['id'], approve=True)
                        st.success("Đã phê duyệt.")
                        st.experimental_rerun()
                with col2:
                    if st.button(f"Từ chối_{p['id']}"):
                        approve_user(p['id'], approve=False)
                        st.info("Đã từ chối.")
                        st.experimental_rerun()
        else:
            st.write("Không có yêu cầu đăng ký mới.")

        st.subheader("Thông tin hệ thống")
        st.write("Danh sách thành viên (all):")
        df_all = pd.DataFrame(list_users())
        if not df_all.empty:
            st.dataframe(df_all[['id','name','email','phone','role','status','wins','created_at']])
        else:
            st.write("Chưa có thành viên.")

st.caption("Ứng dụng mẫu: Pickleball Club Management - Ban CĐSCN")
