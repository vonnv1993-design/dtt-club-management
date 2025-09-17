# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date

st.set_page_config(page_title="Pickleball Club Manager", layout="wide")

# ---------------------------
# Helpers
# ---------------------------
def init_state():
    """Initialize session state dataframes and default admin."""
    if "users" not in st.session_state:
        # fields: id, name, email, phone, password, role, approved, joined_on, wins, contributions, balance
        st.session_state.users = pd.DataFrame(columns=[
            "id", "name", "email", "phone", "password", "role", "approved", "joined_on", "wins", "contributions", "balance"
        ])
        # create default admin
        admin = {
            "id": 1,
            "name": "Administrator",
            "email": "admin@example.com",
            "phone": "",
            "password": "Admin@123",
            "role": "admin",
            "approved": True,
            "joined_on": str(date.today()),
            "wins": 0,
            "contributions": 0.0,
            "balance": 0.0
        }
        st.session_state.users = pd.concat([st.session_state.users, pd.DataFrame([admin])], ignore_index=True)

    if "next_user_id" not in st.session_state:
        st.session_state.next_user_id = int(st.session_state.users["id"].max()) + 1 if not st.session_state.users.empty else 2

    if "polls" not in st.session_state:
        # polls: id, title, date, created_by
        st.session_state.polls = pd.DataFrame(columns=["id", "title", "date", "created_by"])

    if "votes" not in st.session_state:
        # votes: poll_id, user_id, vote (Yes/No), timestamp
        st.session_state.votes = pd.DataFrame(columns=["poll_id", "user_id", "vote", "timestamp"])

    if "finance" not in st.session_state:
        # finance: id, date, description, amount, type (contrib/expense), member_id (for contrib), split_for_poll (poll_id or "")
        st.session_state.finance = pd.DataFrame(columns=["id", "date", "description", "amount", "type", "member_id", "poll_id"])

    if "next_fin_id" not in st.session_state:
        st.session_state.next_fin_id = 1

    if "current_user" not in st.session_state:
        st.session_state.current_user = None  # will hold user_id when logged in

def add_user(name, email, phone, password):
    uid = st.session_state.next_user_id
    new = {
        "id": uid,
        "name": name,
        "email": email,
        "phone": phone,
        "password": password,
        "role": "member",
        "approved": False,  # requires admin approval
        "joined_on": str(date.today()),
        "wins": 0,
        "contributions": 0.0,
        "balance": 0.0
    }
    st.session_state.users = pd.concat([st.session_state.users, pd.DataFrame([new])], ignore_index=True)
    st.session_state.next_user_id += 1
    return uid

def authenticate(username_email, password):
    """Return user row (as dict) if credentials OK and approved; else None (or if not approved return 'pending')."""
    users = st.session_state.users
    # allow login by name or email
    match = users[(users["name"] == username_email) | (users["email"] == username_email)]
    if match.empty:
        return None
    row = match.iloc[0]
    if str(row["password"]) != str(password):
        return None
    if not row["approved"]:
        return "pending"
    return row.to_dict()

def get_user_by_id(uid):
    m = st.session_state.users[st.session_state.users["id"] == uid]
    if m.empty:
        return None
    return m.iloc[0].to_dict()

def require_login():
    if st.session_state.current_user is None:
        st.warning("Vui lòng đăng nhập hoặc đăng ký để sử dụng ứng dụng.")
        st.stop()

def create_poll(title, poll_date, created_by):
    pid = 1 if st.session_state.polls.empty else int(st.session_state.polls["id"].max()) + 1
    row = {"id": pid, "title": title, "date": str(poll_date), "created_by": created_by}
    st.session_state.polls = pd.concat([st.session_state.polls, pd.DataFrame([row])], ignore_index=True)
    return pid

def record_vote(poll_id, user_id, vote):
    ts = datetime.now().isoformat()
    st.session_state.votes = pd.concat([st.session_state.votes, pd.DataFrame([{"poll_id": poll_id, "user_id": user_id, "vote": vote, "timestamp": ts}])], ignore_index=True)

def add_contribution(member_id, amount, desc):
    fid = st.session_state.next_fin_id
    row = {"id": fid, "date": str(date.today()), "description": desc, "amount": float(amount), "type": "contrib", "member_id": member_id, "poll_id": ""}
    st.session_state.finance = pd.concat([st.session_state.finance, pd.DataFrame([row])], ignore_index=True)
    # update member contributions and balance
    idx = st.state_index_by_user_id(member_id)
    if idx is not None:
        st.session_state.users.at[idx, "contributions"] = float(st.session_state.users.at[idx, "contributions"]) + float(amount)
        st.session_state.users.at[idx, "balance"] = float(st.session_state.users.at[idx, "balance"]) + float(amount)
    st.session_state.next_fin_id += 1

def add_expense(amount, desc, poll_id, charged_member_ids):
    """Add an expense record and subtract shares from participants' balances (and record as finance rows)."""
    fid = st.session_state.next_fin_id
    row = {"id": fid, "date": str(date.today()), "description": desc, "amount": float(amount), "type": "expense", "member_id": "", "poll_id": poll_id}
    st.session_state.finance = pd.concat([st.session_state.finance, pd.DataFrame([row])], ignore_index=True)
    share = float(amount) / len(charged_member_ids) if charged_member_ids else 0.0
    for mid in charged_member_ids:
        idx = st.state_index_by_user_id(mid)
        if idx is not None:
            st.session_state.users.at[idx, "balance"] = float(st.session_state.users.at[idx, "balance"]) - share
            # also record separate finance row per member for auditing
            fid2 = st.session_state.next_fin_id + 1
            row2 = {"id": fid2, "date": str(date.today()), "description": f"{desc} (share)", "amount": -share, "type": "expense_share", "member_id": mid, "poll_id": poll_id}
            st.session_state.finance = pd.concat([st.session_state.finance, pd.DataFrame([row2])], ignore_index=True)
            st.session_state.next_fin_id += 1
    st.session_state.next_fin_id += 1

# Utility to get dataframe index of user by id
def _state_index_by_user_id(uid):
    idxs = st.session_state.users[st.session_state.users["id"] == uid].index
    return int(idxs[0]) if not idxs.empty else None

# attach helper to st.session_state for closure usage
st.state_index_by_user_id = _state_index_by_user_id

# ---------------------------
# Initialize
# ---------------------------
init_state()

# ---------------------------
# Authentication UI (Login / Register)
# ---------------------------

st.sidebar.title("🔐 Đăng nhập / Đăng ký")
auth_mode = st.sidebar.selectbox("Chọn", ["Login", "Register", "Logout"])

if auth_mode == "Register":
    st.sidebar.subheader("Đăng ký thành viên mới")
    with st.sidebar.form("reg_form", clear_on_submit=True):
        r_name = st.text_input("Họ & tên")
        r_email = st.text_input("Email")
        r_phone = st.text_input("Số điện thoại")
        r_pass = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng ký")
        if submitted:
            if not r_name or not r_email or not r_pass:
                st.sidebar.error("Vui lòng điền ít nhất tên, email và mật khẩu.")
            else:
                add_user(r_name, r_email, r_phone, r_pass)
                st.sidebar.success("Đăng ký thành công. Chờ quản trị viên phê duyệt.")

elif auth_mode == "Login":
    st.sidebar.subheader("Đăng nhập")
    with st.sidebar.form("login_form", clear_on_submit=False):
        l_user = st.text_input("Tên hoặc Email")
        l_pass = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            auth = authenticate(l_user, l_pass)
            if auth is None:
                st.sidebar.error("Sai tên/email hoặc mật khẩu.")
            elif auth == "pending":
                st.sidebar.info("Tài khoản của bạn đang chờ phê duyệt bởi quản trị viên.")
            else:
                st.session_state.current_user = int(auth["id"])
                st.sidebar.success(f"Đã đăng nhập: {auth['name']} ({auth['role']})")

elif auth_mode == "Logout":
    if st.session_state.current_user is not None:
        st.session_state.current_user = None
        st.sidebar.success("Đã đăng xuất.")
    else:
        st.sidebar.info("Bạn chưa đăng nhập.")

# If not logged in, show main minimal home and stop further tabs? We'll still show tabs but user must log in for actions
st.title("🏓 Pickleball Club - Ban CĐSCN")

# ---------------------------
# Main Tabs
# ---------------------------
tabs = st.tabs(["Home", "Members", "Ranking", "Voting", "Finance", "Admin"])

# ----- HOME tab -----
with tabs[0]:
    st.header("🏠 Home - Thống kê nhanh")
    # require at least public view allowed
    users_df = st.session_state.users.copy()
    votes_df = st.session_state.votes.copy()
    finance_df = st.session_state.finance.copy()

    # Top Ranking by wins
    if not users_df.empty:
        top_r = users_df.sort_values(by="wins", ascending=False).head(10)
        fig1 = px.bar(top_r, x="name", y="wins", title="Top Ranking (số trận thắng)", text="wins")
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu thành viên.")

    # Top balance (most money)
    if not users_df.empty:
        rich = users_df.sort_values(by="balance", ascending=False).head(10)
        fig2 = px.bar(rich, x="name", y="balance", title="Top tiền còn nhiều nhất (VND)", text="balance")
        st.plotly_chart(fig2, use_container_width=True)

    # Vote counts per member
    if not votes_df.empty:
        vc = votes_df[votes_df["vote"] == "Yes"].groupby("user_id").size().reset_index(name="yes_count")
        vc["name"] = vc["user_id"].apply(lambda uid: get_user_by_id(int(uid))["name"] if get_user_by_id(int(uid)) else str(uid))
        fig3 = px.bar(vc.sort_values("yes_count", ascending=False), x="name", y="yes_count", title="Số lần vote tham gia (Yes)")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu vote.")

# ----- MEMBERS tab -----
with tabs[1]:
    st.header("👥 Thành viên CLB")
    st.write("Danh sách thành viên (chờ phê duyệt sẽ đánh dấu).")

    users = st.session_state.users.copy()
    # Show table
    st.dataframe(users[["id", "name", "email", "phone", "role", "approved", "joined_on", "wins", "contributions", "balance"]])

    # Admin can approve/reject members
    cur = get_user_by_id(st.session_state.current_user) if st.session_state.current_user else None
    if cur and cur["role"] == "admin":
        st.subheader("Quản lý phê duyệt thành viên")
        pending = users[users["approved"] == False]
        if pending.empty:
            st.info("Không có thành viên chờ phê duyệt.")
        else:
            for _, row in pending.iterrows():
                st.write(f"**{row['name']}** — {row['email']} — {row['phone']}")
                col1, col2 = st.columns([1,1])
                if col1.button("Phê duyệt", key=f"approve_{row['id']}"):
                    idx = st.state_index_by_user_id(row["id"])
                    st.session_state.users.at[idx, "approved"] = True
                    st.success(f"Đã phê duyệt {row['name']}")
                    st.experimental_rerun()
                if col2.button("Từ chối", key=f"reject_{row['id']}"):
                    # remove user
                    idx = st.state_index_by_user_id(row["id"])
                    st.session_state.users = st.session_state.users.drop(index=idx).reset_index(drop=True)
                    st.success(f"Đã từ chối {row['name']}")

# ----- RANKING tab -----
with tabs[2]:
    st.header("🏆 Ranking - Quản lý trận thắng")
    cur = get_user_by_id(st.session_state.current_user) if st.session_state.current_user else None
    users_options = st.session_state.users[st.session_state.users["approved"] == True][["id", "name"]]
    if users_options.empty:
        st.info("Chưa có thành viên được phê duyệt.")
    else:
        st.dataframe(st.session_state.users[["name", "wins"]].sort_values("wins", ascending=False))

        if cur and cur["role"] == "admin":
            st.subheader("Nhập trận thắng (Admin)")
            sel = st.selectbox("Chọn thành viên", options=users_options["id"].tolist(), format_func=lambda x: users_options[users_options["id"]==x]["name"].values[0])
            inc = st.number_input("Số trận thắng cộng thêm", min_value=1, value=1)
            if st.button("Cập nhật thắng"):
                idx = st.state_index_by_user_id(sel)
                if idx is not None:
                    st.session_state.users.at[idx, "wins"] = int(st.session_state.users.at[idx, "wins"]) + int(inc)
                    st.success("Đã cập nhật số trận thắng.")
                    st.experimental_rerun()
        else:
            st.info("Chỉ quản trị viên mới được nhập trận thắng.")

# ----- VOTING tab -----
with tabs[3]:
    st.header("🗳️ Bình chọn tham gia trận")
    cur = get_user_by_id(st.session_state.current_user) if st.session_state.current_user else None

    # List existing polls
    if st.session_state.polls.empty:
        st.info("Chưa có bình chọn nào.")
    else:
        st.subheader("Các bình chọn hiện có")
        st.dataframe(st.session_state.polls)

    # Admin creates poll
    if cur and cur["role"] == "admin":
        st.subheader("Tạo bình chọn mới (Admin)")
        with st.form("create_poll"):
            t_title = st.text_input("Tiêu đề (ví dụ: Tập chiều Thứ 7)")
            t_date = st.date_input("Ngày tham gia", date.today())
            submit_poll = st.form_submit_button("Tạo bình chọn")
            if submit_poll:
                create_poll(t_title, t_date, cur["id"])
                st.success("Đã tạo bình chọn.")
                st.experimental_rerun()
    # Members vote
    if cur and cur["approved"]:
        st.subheader("Bình chọn (Thành viên)")
        # show polls and allow vote
        polls = st.session_state.polls.copy()
        if not polls.empty:
            for _, p in polls.iterrows():
                st.write(f"**{p['title']}** — Ngày: {p['date']} — ID: {p['id']}")
                # Check if this user already voted for this poll
                already = st.session_state.votes[(st.session_state.votes["poll_id"]==p["id"]) & (st.session_state.votes["user_id"]==cur["id"])]
                if not already.empty:
                    st.caption(f"Bạn đã vote: {already.iloc[0]['vote']}")
                else:
                    col1, col2 = st.columns([1,1])
                    if col1.button("Vote Yes", key=f"yes_{p['id']}"):
                        record_vote(p["id"], cur["id"], "Yes")
                        st.success("Bạn đã vote Yes.")
                        st.experimental_rerun()
                    if col2.button("Vote No", key=f"no_{p['id']}"):
                        record_vote(p["id"], cur["id"], "No")
                        st.info("Bạn đã vote No.")
                        st.experimental_rerun()
        else:
            st.info("Chưa có bình chọn để vote.")
    else:
        st.info("Vui lòng đăng nhập và được phê duyệt để vote.")

    # Show statistics per poll
    if not st.session_state.polls.empty:
        st.subheader("Thống kê bình chọn")
        poll_stats = []
        for _, p in st.session_state.polls.iterrows():
            dfv = st.session_state.votes[st.session_state.votes["poll_id"]==p["id"]]
            yes = dfv[dfv["vote"]=="Yes"].shape[0]
            no = dfv[dfv["vote"]=="No"].shape[0]
            poll_stats.append({"id": p["id"], "title": p["title"], "yes": yes, "no": no})
        st.table(pd.DataFrame(poll_stats))

# ----- FINANCE tab -----
with tabs[4]:
    st.header("💰 Quản lý tài chính (VND)")
    cur = get_user_by_id(st.session_state.current_user) if st.session_state.current_user else None

    # Show finance ledger
    st.subheader("Sổ thu chi")
    st.dataframe(st.session_state.finance)

    # Admin: enter contributions
    if cur and cur["role"] == "admin":
        st.subheader("Nhập đóng góp (Admin)")
        with st.form("contrib_form"):
            m_opt = st.session_state.users[st.session_state.users["approved"]==True][["id","name"]]
            if m_opt.empty:
                st.write("Chưa có thành viên được phê duyệt.")
            else:
                sel_m = st.selectbox("Chọn thành viên", options=m_opt["id"].tolist(), format_func=lambda x: m_opt[m_opt["id"]==x]["name"].values[0])
                amount = st.number_input("Số tiền (VND)", min_value=0.0, value=0.0)
                desc = st.text_input("Ghi chú")
                sub = st.form_submit_button("Ghi đóng góp")
                if sub:
                    # add finance row
                    fid = st.session_state.next_fin_id
                    row = {"id": fid, "date": str(date.today()), "description": desc or "Contribution", "amount": float(amount), "type": "contrib", "member_id": sel_m, "poll_id": ""}
                    st.session_state.finance = pd.concat([st.session_state.finance, pd.DataFrame([row])], ignore_index=True)
                    idx = st.state_index_by_user_id(sel_m)
                    if idx is not None:
                        st.session_state.users.at[idx, "contributions"] = float(st.session_state.users.at[idx, "contributions"]) + float(amount)
                        st.session_state.users.at[idx, "balance"] = float(st.session_state.users.at[idx, "balance"]) + float(amount)
                    st.session_state.next_fin_id += 1
                    st.success("Đã ghi đóng góp.")
                    st.experimental_rerun()

        st.subheader("Nhập chi phí buổi tập và chia đều cho người vote Yes (Admin)")
        with st.form("expense_form"):
            if st.session_state.polls.empty:
                st.write("Chưa có bình chọn nào. Tạo bình chọn ở tab Voting trước.")
            else:
                pol = st.selectbox("Chọn Poll để tính chi phí", options=st.session_state.polls["id"].tolist(), format_func=lambda x: st.session_state.polls[st.session_state.polls["id"]==x]["title"].values[0])
                expense_amt = st.number_input("Tổng chi phí (VND)", min_value=0.0, value=0.0)
                desc_e = st.text_input("Ghi chú (mô tả chi phí)")
                submit_e = st.form_submit_button("Chia chi phí")
                if submit_e:
                    # find yes voters for poll
                    yes_voters = st.session_state.votes[(st.session_state.votes["poll_id"]==pol) & (st.session_state.votes["vote"]=="Yes")]["user_id"].tolist()
                    if not yes_voters:
                        st.error("Không có ai vote Yes cho poll này. Không thể chia chi phí.")
                    else:
                        share = float(expense_amt) / len(yes_voters)
                        # add expense record
                        fid = st.session_state.next_fin_id
                        row = {"id": fid, "date": str(date.today()), "description": desc_e or "Expense", "amount": float(expense_amt), "type": "expense", "member_id": "", "poll_id": pol}
                        st.session_state.finance = pd.concat([st.session_state.finance, pd.DataFrame([row])], ignore_index=True)
                        st.session_state.next_fin_id += 1
                        # subtract share from each participant balance and add expense_share record
                        for mid in yes_voters:
                            idx = st.state_index_by_user_id(mid)
                            if idx is not None:
                                st.session_state.users.at[idx, "balance"] = float(st.session_state.users.at[idx, "balance"]) - share
                                # record per-member expense share
                                fid2 = st.session_state.next_fin_id
                                row2 = {"id": fid2, "date": str(date.today()), "description": f"{desc_e} (share)", "amount": -share, "type": "expense_share", "member_id": mid, "poll_id": pol}
                                st.session_state.finance = pd.concat([st.session_state.finance, pd.DataFrame([row2])], ignore_index=True)
                                st.session_state.next_fin_id += 1
                        st.success(f"Đã chia chi phí: mỗi người trả {share:.0f} VND")
                        st.experimental_rerun()
    else:
        st.info("Chỉ quản trị viên mới có quyền quản lý tài chính (ghi đóng góp, chia chi phí).")

# ----- ADMIN tab -----
with tabs[5]:
    st.header("⚙️ Admin Panel")
    cur = get_user_by_id(st.session_state.current_user) if st.session_state.current_user else None
    if cur and cur["role"] == "admin":
        st.subheader("Tài khoản admin hiện tại")
        st.write(f"Name: {cur['name']} — Email: {cur['email']}")
        st.write("Bạn có thể đổi mật khẩu admin (demo).")
        with st.form("admin_change_pw"):
            old = st.text_input("Mật khẩu hiện tại", type="password")
            new = st.text_input("Mật khẩu mới", type="password")
            sub = st.form_submit_button("Đổi mật khẩu")
            if sub:
                # verify and change
                if old != cur["password"]:
                    st.error("Mật khẩu hiện tại sai.")
                elif not new:
                    st.error("Mật khẩu mới không được để trống.")
                else:
                    idx = st.state_index_by_user_id(cur["id"])
                    st.session_state.users.at[idx, "password"] = new
                    st.success("Đã đổi mật khẩu admin.")
                    st.experimental_rerun()

        st.subheader("Xuất danh sách / báo cáo")
        if st.button("Xuất danh sách thành viên (CSV)"):
            csv = st.session_state.users.to_csv(index=False).encode("utf-8")
            st.download_button("Tải CSV", data=csv, file_name="members.csv", mime="text/csv")
    else:
        st.error("Bạn cần đăng nhập bằng tài khoản quản trị viên để vào Admin Panel.")
