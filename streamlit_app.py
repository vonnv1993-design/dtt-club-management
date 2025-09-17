# app.py
import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import BytesIO

st.set_page_config(page_title="Pickleball Club Manager", layout="wide")

# --------------------
# Helper: init data
# --------------------
def init_state():
    if "users" not in st.session_state:
        # columns: Name, Email, Role, Approved (bool), Joined (date), Wins (int)
        st.session_state.users = pd.DataFrame(columns=["Name", "Email", "Role", "Approved", "Joined", "Wins"])
        # create demo admin
        st.session_state.users.loc[0] = ["Admin", "admin@pickleball.club", "Admin", True, str(date.today()), 0]

    if "pending" not in st.session_state:
        # pending registrations: Name, Email, RequestedAt
        st.session_state.pending = pd.DataFrame(columns=["Name", "Email", "RequestedAt"])

    if "votes" not in st.session_state:
        # votes: PollID, Date, MemberEmail, Vote(Yes/No)
        st.session_state.votes = pd.DataFrame(columns=["PollID", "Date", "MemberEmail", "Vote"])

    if "polls" not in st.session_state:
        # polls: PollID, Date, CreatedAt, Title
        st.session_state.polls = pd.DataFrame(columns=["PollID", "Date", "CreatedAt", "Title"])

    if "finance" not in st.session_state:
        # finance: Date, Type(Contribution/Expense), Description, Amount, MemberEmail (for contributions/assigned expense)
        st.session_state.finance = pd.DataFrame(columns=["Date", "Type", "Description", "Amount", "MemberEmail"])

init_state()

# --------------------
# Simple auth (demo)
# --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None  # store Email

def login_ui():
    st.header("🔐 Đăng nhập / Đăng ký")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Đăng nhập (demo)")
        email = st.text_input("Email", key="login_email")
        btn_login = st.button("Đăng nhập", key="login_btn")
        if btn_login:
            if email and not st.session_state.users.empty and email in st.session_state.users["Email"].values:
                user = st.session_state.users[st.session_state.users["Email"] == email].iloc[0]
                if user["Approved"] is True:
                    st.session_state.logged_in = True
                    st.session_state.current_user = email
                    st.success(f"Đăng nhập thành công: {user['Name']} ({user['Role']})")
                else:
                    st.warning("Tài khoản chưa được phê duyệt bởi quản trị viên.")
            else:
                st.error("Email chưa đăng ký hoặc không tồn tại.")

    with col2:
        st.subheader("Đăng ký thành viên")
        with st.form("register_form", clear_on_submit=True):
            name = st.text_input("Họ tên", key="reg_name")
            email_r = st.text_input("Email", key="reg_email")
            submitted = st.form_submit_button("Gửi đăng ký")
            if submitted:
                if not name or not email_r:
                    st.warning("Vui lòng nhập đầy đủ Họ tên và Email.")
                elif email_r in st.session_state.users["Email"].values or email_r in st.session_state.pending["Email"].values:
                    st.warning("Email đã đăng ký hoặc đang chờ phê duyệt.")
                else:
                    st.session_state.pending.loc[len(st.session_state.pending)] = [name, email_r, str(datetime.now())]
                    st.success("Đăng ký đã gửi — đang chờ quản trị viên phê duyệt.")

# --------------------
# Permissions
# --------------------
def get_current_user_record():
    if st.session_state.logged_in and st.session_state.current_user:
        return st.session_state.users[st.session_state.users["Email"] == st.session_state.current_user].iloc[0]
    return None

def is_admin():
    rec = get_current_user_record()
    return (rec is not None) and (rec["Role"] == "Admin")

# --------------------
# Main UI with tabs
# --------------------
tabs = st.tabs(["Home","Thành viên","Ranking","Vote","Tài chính","Logout"])
home, tab_members, tab_ranking, tab_vote, tab_finance, tab_logout = tabs

# --- HOME ---
with home:
    st.title("🏓 Pickleball Club - Ban CĐSCN")
    st.write("Ứng dụng quản lý: đăng ký, phê duyệt thành viên, xếp hạng, vote tham gia, quản lý tài chính.")
    if not st.session_state.logged_in:
        login_ui()
    else:
        user = get_current_user_record()
        st.success(f"Xin chào **{user['Name']}** — Vai trò: **{user['Role']}**")
        st.write(f"Ngày tham gia: {user['Joined']} — Trận thắng: {user['Wins']}")

# --- MEMBERS (Admin approve + list) ---
with tab_members:
    st.header("👥 Quản lý Thành viên")
    if is_admin():
        st.subheader("Các đơn đăng ký đang chờ phê duyệt")
        if st.session_state.pending.empty:
            st.info("Không có đơn chờ phê duyệt.")
        else:
            for idx, row in st.session_state.pending.iterrows():
                colA, colB = st.columns([3,1])
                with colA:
                    st.write(f"**{row['Name']}** — {row['Email']} — Đăng ký lúc: {row['RequestedAt']}")
                with colB:
                    if st.button("Phê duyệt", key=f"approve_{idx}"):
                        st.session_state.users.loc[len(st.session_state.users)] = [row['Name'], row['Email'], "Member", True, str(date.today()), 0]
                        st.session_state.pending = st.session_state.pending.drop(idx).reset_index(drop=True)
                        st.experimental_rerun()
                    if st.button("Từ chối", key=f"reject_{idx}"):
                        st.session_state.pending = st.session_state.pending.drop(idx).reset_index(drop=True)
                        st.experimental_rerun()
        st.markdown("---")

    st.subheader("Danh sách Thành viên")
    # show users (only approved)
    approved = st.session_state.users[st.session_state.users["Approved"]==True].copy()
    if approved.empty:
        st.info("Chưa có thành viên được phê duyệt.")
    else:
        st.dataframe(approved[["Name","Email","Role","Joined","Wins"]].reset_index(drop=True), use_container_width=True)

    # Admin: edit role / remove
    if is_admin():
        st.markdown("**Quản trị (Sửa/Xóa)**")
        sel = st.selectbox("Chọn thành viên để điều chỉnh", approved["Email"].tolist() if not approved.empty else [])
        if sel:
            selrec = st.session_state.users[st.session_state.users["Email"]==sel].iloc[0]
            new_role = st.selectbox("Chọn Role", ["Member","Admin"], index=0 if selrec["Role"]=="Member" else 1)
            if st.button("Cập nhật role"):
                st.session_state.users.loc[st.session_state.users["Email"]==sel,"Role"] = new_role
                st.success("Đã cập nhật role.")
            if st.button("Xóa thành viên"):
                st.session_state.users = st.session_state.users[st.session_state.users["Email"]!=sel].reset_index(drop=True)
                # remove votes and finance records from this email optionally
                st.success("Đã xóa thành viên.")
                st.experimental_rerun()

# --- RANKING ---
with tab_ranking:
    st.header("🏆 Xếp hạng thành viên")
    st.write("Quản trị viên nhập trận thắng cho thành viên; hệ thống cập nhật Wins và sắp xếp.")
    if is_admin():
        # admin inputs
        approved = st.session_state.users[st.session_state.users["Approved"]==True]
        sel_email = st.selectbox("Chọn thành viên ghi nhận thắng", approved["Email"].tolist())
        add_win = st.number_input("Số trận thắng thêm", min_value=1, value=1, step=1)
        if st.button("Ghi nhận thắng"):
            st.session_state.users.loc[st.session_state.users["Email"]==sel_email,"Wins"] = st.session_state.users.loc[st.session_state.users["Email"]==sel_email,"Wins"].astype(int) + int(add_win)
            st.success("Đã cập nhật thắng.")
    else:
        st.info("Chỉ quản trị viên được cập nhật trận thắng.")

    # ranking display
    ranking = st.session_state.users[st.session_state.users["Approved"]==True].copy()
    if not ranking.empty:
        ranking = ranking.sort_values(by="Wins", ascending=False).reset_index(drop=True)
        ranking.index = ranking.index + 1
        st.dataframe(ranking[["Name","Email","Wins"]], use_container_width=True)
    else:
        st.info("Chưa có thành viên.")

# --- VOTE ---
with tab_vote:
    st.header("🗳 Vote tham gia chơi")
    st.write("Quản trị viên tạo poll (ngày chơi). Thành viên vote Yes/No để tham gia.")
    # create poll (admin)
    if is_admin():
        with st.form("create_poll", clear_on_submit=True):
            title = st.text_input("Tiêu đề poll (ví dụ: Buổi tập 20/09/2025)")
            poll_date = st.date_input("Ngày chơi", date.today())
            create = st.form_submit_button("Tạo poll")
            if create and title:
                pid = f"poll_{len(st.session_state.polls)+1}"
                st.session_state.polls.loc[len(st.session_state.polls)] = [pid, str(poll_date), str(datetime.now()), title]
                st.success("Đã tạo poll.")
    st.markdown("---")
    # show polls and let members vote
    if st.session_state.polls.empty:
        st.info("Chưa có poll nào.")
    else:
        for idx, poll in st.session_state.polls.iterrows():
            st.markdown(f"**{poll['Title']}** — Ngày: {poll['Date']} — ID: {poll['PollID']}")
            col1, col2, col3 = st.columns([3,2,2])
            # show counts
            cnt_yes = st.session_state.votes[(st.session_state.votes["PollID"]==poll["PollID"]) & (st.session_state.votes["Vote"]=="Yes")].shape[0]
            cnt_no = st.session_state.votes[(st.session_state.votes["PollID"]==poll["PollID"]) & (st.session_state.votes["Vote"]=="No")].shape[0]
            with col1:
                st.write(f"✅ Yes: {cnt_yes}  |  ❌ No: {cnt_no}")
            with col2:
                if st.session_state.logged_in:
                    user_email = st.session_state.current_user
                    prev = st.session_state.votes[(st.session_state.votes["PollID"]==poll["PollID"]) & (st.session_state.votes["MemberEmail"]==user_email)]
                    default_vote = "Yes" if (not prev.empty and prev.iloc[-1]["Vote"]=="Yes") else "No"
                    vote_choice = st.selectbox("Bạn có tham gia?", ["Yes","No"], index=0 if default_vote=="Yes" else 1, key=f"vote_{poll['PollID']}")
                    if st.button("Gửi vote", key=f"submit_vote_{poll['PollID']}"):
                        # upsert vote
                        # remove previous vote by this member in this poll
                        st.session_state.votes = st.session_state.votes[~((st.session_state.votes["PollID"]==poll["PollID"]) & (st.session_state.votes["MemberEmail"]==user_email))]
                        st.session_state.votes.loc[len(st.session_state.votes)] = [poll["PollID"], poll["Date"], user_email, vote_choice]
                        st.success("Đã ghi nhận lựa chọn của bạn.")
                else:
                    st.info("Vui lòng đăng nhập để vote.")
            with col3:
                # Admin can close poll / delete
                if is_admin():
                    if st.button("Xóa poll", key=f"delpoll_{poll['PollID']}"):
                        st.session_state.polls = st.session_state.polls[st.session_state.polls["PollID"]!=poll["PollID"]].reset_index(drop=True)
                        st.session_state.votes = st.session_state.votes[st.session_state.votes["PollID"]!=poll["PollID"]].reset_index(drop=True)
                        st.success("Đã xóa poll.")
                        st.experimental_rerun()
            st.markdown("---")

# --- FINANCE ---
with tab_finance:
    st.header("💰 Quản lý Tài chính")
    st.write("Ghi nhận đóng góp (mỗi thành viên đóng) và nhập chi phí buổi tập (Admin nhập) → chia đều cho những người đã vote Yes cho poll tương ứng.")
    cols = st.columns(2)
    with cols[0]:
        st.subheader("📥 Ghi nhận đóng góp (Admin)")
        if is_admin():
            with st.form("contrib_form", clear_on_submit=True):
                mems = st.session_state.users[st.session_state.users["Approved"]==True]["Email"].tolist()
                mem_sel = st.selectbox("Chọn thành viên", mems, key="contrib_mem")
                amount = st.number_input("Số tiền (VND)", min_value=0.0, value=0.0, step=1000.0, key="contrib_amt")
                desc = st.text_input("Ghi chú", "Đóng góp")
                if st.form_submit_button("Ghi nhận đóng góp"):
                    st.session_state.finance.loc[len(st.session_state.finance)] = [str(date.today()), "Contribution", desc, float(amount), mem_sel]
                    st.success("Đã ghi nhận đóng góp.")
        else:
            st.info("Chỉ Admin mới ghi nhận đóng góp (để quản lý tập trung).")

    with cols[1]:
        st.subheader("📤 Nhập chi phí buổi tập và chia đều")
        if is_admin():
            if st.session_state.polls.empty:
                st.info("Không có poll để phân chia chi phí.")
            else:
                poll_map = {row["PollID"]: row["Title"] + " ("+row["Date"]+")" for _,row in st.session_state.polls.iterrows()}
                sel_poll = st.selectbox("Chọn poll để chia phí", list(poll_map.keys()))
                total_cost = st.number_input("Tổng chi phí (VND)", min_value=0.0, value=0.0, step=1000.0, key="cost_amt")
                cost_desc = st.text_input("Mô tả chi phí", "Chi phí buổi tập")
                if st.button("Chia chi phí cho người đã vote Yes"):
                    players = st.session_state.votes[(st.session_state.votes["PollID"]==sel_poll) & (st.session_state.votes["Vote"]=="Yes")]["MemberEmail"].tolist()
                    if len(players)==0:
                        st.warning("Không có ai vote Yes để chia chi phí.")
                    else:
                        per_head = float(total_cost) / len(players)
                        for p in players:
                            st.session_state.finance.loc[len(st.session_state.finance)] = [str(date.today()), "Expense", f"{cost_desc} ({sel_poll})", per_head, p]
                        st.success(f"Đã chia {int(per_head)} VND cho {len(players)} người.")
        else:
            st.info("Chỉ Admin mới nhập chi phí và chia đều.")

    st.markdown("---")
    st.subheader("Bản ghi Tài chính")
    if st.session_state.finance.empty:
        st.info("Chưa có bản ghi tài chính.")
    else:
        st.dataframe(st.session_state.finance.sort_values(by="Date", ascending=False).reset_index(drop=True), use_container_width=True)

    # show balance per member (contrib - expenses)
    st.subheader("Số dư theo thành viên")
    df = st.session_state.finance.copy()
    if not df.empty:
        df["AmountSigned"] = df.apply(lambda r: float(r["Amount"]) if r["Type"]=="Contribution" else -float(r["Amount"]), axis=1)
        balance = df.groupby("MemberEmail")["AmountSigned"].sum().reset_index().rename(columns={"AmountSigned":"Balance"})
        users = st.session_state.users[["Name","Email"]]
        bal = users.merge(balance, left_on="Email", right_on="MemberEmail", how="left").fillna(0)
        st.dataframe(bal[["Name","Email","Balance"]], use_container_width=True)
    else:
        st.info("Chưa có dữ liệu tính số dư.")

# --- LOGOUT tab ---
with tab_logout:
    st.header("🔁 Logout")
    if st.session_state.logged_in:
        if st.button("Đăng xuất"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.success("Đã đăng xuất.")
    else:
        st.info("Bạn chưa đăng nhập.")
