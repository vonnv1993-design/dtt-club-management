import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
import json
import os

# --- Hàm băm mật khẩu ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Hàm đọc/ghi JSON ---
def load_json(filename, default_data):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        return default_data

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_all():
    save_json(USERS_FILE, st.session_state.users)
    save_json(VOTES_FILE, st.session_state.votes)
    save_json(EXPENSES_FILE, st.session_state.expenses)

# --- Đường dẫn file dữ liệu ---
USERS_FILE = "users.json"
VOTES_FILE = "votes.json"
EXPENSES_FILE = "expenses.json"

# --- Dữ liệu mặc định admin ---
default_users = {
    "admin@local": {
        "name": "Admin",
        "phone": "",
        "password_hash": hash_password("Admin@123"),
        "role": "admin",
        "approved": True,
        "wins": 0,
        "balance": 0,
        "votes": []
    }
}

# --- Khởi tạo dữ liệu từ file JSON ---
if 'users' not in st.session_state:
    st.session_state.users = load_json(USERS_FILE, default_users)

if 'pending_users' not in st.session_state:
    pending = {email: u for email, u in st.session_state.users.items() if not u.get('approved', False)}
    st.session_state.pending_users = pending

if 'votes' not in st.session_state:
    st.session_state.votes = load_json(VOTES_FILE, [])

if 'expenses' not in st.session_state:
    st.session_state.expenses = load_json(EXPENSES_FILE, [])

# --- Hàm đăng nhập ---
def login():
    st.title("🔐 Đăng nhập Câu lạc bộ Pickleball Ban CĐSCN")
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("📧 Email")
        password = st.text_input("🔑 Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập")
        if submitted:
            if email in st.session_state.users:
                user = st.session_state.users[email]
                if user['password_hash'] == hash_password(password):
                    if user['approved']:
                        st.session_state['login'] = True
                        st.session_state['user_email'] = email
                        st.session_state['user_role'] = user['role']
                        st.success(f"Chào mừng {user['name']}!")
                        st.rerun()
                    else:
                        st.error("⚠️ Tài khoản chưa được phê duyệt. Vui lòng chờ quản trị viên.")
                else:
                    st.error("❌ Mật khẩu không đúng.")
            else:
                st.error("❌ Email không tồn tại.")

# --- Hàm đăng ký thành viên ---
def register():
    st.title("📝 Đăng ký thành viên mới")
    with st.form("register_form"):
        name = st.text_input("Họ và tên")
        email = st.text_input("Email")
        phone = st.text_input("Số điện thoại")
        password = st.text_input("Mật khẩu", type="password")
        password2 = st.text_input("Nhập lại mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng ký")
        if submitted:
            if not (name and email and phone and password and password2):
                st.error("Vui lòng điền đầy đủ thông tin.")
                return
            if password != password2:
                st.error("Mật khẩu nhập lại không khớp.")
                return
            if email in st.session_state.users or email in st.session_state.pending_users:
                st.error("Email đã được đăng ký.")
                return
            new_user = {
                'name': name,
                'phone': phone,
                'password_hash': hash_password(password),
                'role': 'member',
                'approved': False,
                'wins': 0,
                'balance': 0,
                'votes': []
            }
            st.session_state.pending_users[email] = new_user
            st.session_state.users[email] = new_user
            save_all()
            st.success("Đăng ký thành công! Vui lòng chờ quản trị viên phê duyệt.")

# --- Tab phê duyệt thành viên (admin) ---
def admin_approve_users():
    st.header("🛠️ Phê duyệt thành viên mới")
    pending = st.session_state.pending_users
    if not pending:
        st.info("Không có thành viên chờ phê duyệt.")
        return
    for email, info in list(pending.items()):
        with st.expander(f"{info['name']} - {email} - {info['phone']}"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Phê duyệt {email}", key=f"approve_{email}"):
                    info['approved'] = True
                    st.session_state.users[email] = info
                    del st.session_state.pending_users[email]
                    save_all()
                    st.success(f"Đã phê duyệt {email}")
                    st.rerun()
            with col2:
                if st.button(f"❌ Từ chối {email}", key=f"reject_{email}"):
                    if email in st.session_state.users:
                        del st.session_state.users[email]
                    if email in st.session_state.pending_users:
                        del st.session_state.pending_users[email]
                    save_all()
                    st.warning(f"Đã từ chối {email}")
                    st.rerun()

# --- Tab danh sách thành viên ---
def tab_members():
    st.header("👥 Danh sách thành viên")
    users = st.session_state.users
    members = [u for u in users.values() if u['role'] == 'member' and u['approved']]
    if not members:
        st.info("Chưa có thành viên nào được phê duyệt.")
        return
    df = pd.DataFrame(members)
    df_display = df[['name', 'phone', 'wins', 'balance']]
    df_display.columns = ['Tên', 'Số điện thoại', 'Số trận thắng', 'Số tiền còn lại (VNĐ)']
    st.dataframe(df_display.style.format({"Số tiền còn lại (VNĐ)": "{:,.0f}"}))

# --- Tab Ranking ---
def tab_ranking():
    st.header("🏆 Xếp hạng thành viên theo số trận thắng")
    users = st.session_state.users
    members = [u for u in users.values() if u['role'] == 'member' and u['approved']]
    if not members:
        st.info("Chưa có thành viên nào được phê duyệt.")
        return
    df = pd.DataFrame(members)
    df = df[['name', 'wins']]
    df = df.sort_values(by='wins', ascending=False)
    df.columns = ['Tên', 'Số trận thắng']
    st.dataframe(df.style.bar(subset=['Số trận thắng'], color='#4CAF50'))

    if st.session_state.user_role == 'admin':
        st.subheader("Nhập trận thắng cho thành viên")
        with st.form("input_wins"):
            member_email = st.selectbox("Chọn thành viên", options=[email for email, u in st.session_state.users.items() if u['role']=='member' and u['approved']])
            wins_add = st.number_input("Số trận thắng thêm", min_value=0, step=1)
            submitted = st.form_submit_button("Cập nhật")
            if submitted:
                st.session_state.users[member_email]['wins'] += wins_add
                save_all()
                st.success("Cập nhật thành công!")
                st.rerun()

# --- Tab Vote tham gia chơi ---
def tab_vote():
    st.header("🗳️ Bình chọn tham gia chơi")
    if st.session_state.user_role == 'admin':
        st.subheader("Tạo bình chọn mới")
        with st.form("create_vote"):
            date_vote = st.date_input("Chọn ngày tham gia", value=datetime.today())
            submitted = st.form_submit_button("Tạo bình chọn")
            if submitted:
                for v in st.session_state.votes:
                    if v['date'] == date_vote.strftime("%Y-%m-%d"):
                        st.warning("Đã có bình chọn cho ngày này.")
                        break
                else:
                    st.session_state.votes.append({'date': date_vote.strftime("%Y-%m-%d"), 'voters': []})
                    save_all()
                    st.success("Tạo bình chọn thành công!")
                    st.rerun()

    if st.session_state.user_role == 'member':
        if not st.session_state.votes:
            st.info("Chưa có bình chọn nào.")
            return
        st.subheader("Bình chọn tham gia")
        for vote in st.session_state.votes:
            date_str = vote['date']
            voted = st.session_state.user_email in vote['voters']
            if voted:
                st.markdown(f"- ✅ Bạn đã tham gia bình chọn ngày **{date_str}**")
            else:
                if st.button(f"Tham gia ngày {date_str}", key=date_str):
                    vote['voters'].append(st.session_state.user_email)
                    save_all()
                    st.success(f"Bạn đã tham gia bình chọn ngày {date_str}")
                    st.rerun()

    st.subheader("Thống kê số lượng vote tham gia")
    if not st.session_state.votes:
        st.info("Chưa có bình chọn nào.")
        return
    data = [{'Ngày': v['date'], 'Số lượng tham gia': len(v['voters'])} for v in st.session_state.votes]
    df = pd.DataFrame(data).sort_values(by='Ngày', ascending=False)
    st.dataframe(df.style.bar(subset=['Số lượng tham gia'], color='#2196F3'))

# --- Tab quản lý tài chính ---
def tab_finance():
    st.header("💰 Quản lý tài chính")
    users = st.session_state.users
    members = [email for email, u in users.items() if u['role']=='member' and u['approved']]

    st.subheader("Nhập số tiền đóng góp của thành viên")
    with st.form("input_contribution"):
        member_email = st.selectbox("Chọn thành viên", options=members)
        amount = st.number_input("Số tiền đóng góp (VNĐ)", min_value=0, step=1000)
        submitted = st.form_submit_button("Cập nhật đóng góp")
        if submitted:
            users[member_email]['balance'] += amount
            save_all()
            st.success("Cập nhật đóng góp thành công!")
            st.rerun()

    if st.session_state.user_role == 'admin':
        st.subheader("Nhập chi phí buổi tập")
        with st.form("input_expense"):
            if not st.session_state.votes:
                st.info("Chưa có bình chọn nào để xác định người tham gia.")
            else:
                vote_dates = [v['date'] for v in st.session_state.votes]
                date_expense = st.selectbox("Chọn ngày buổi tập", options=vote_dates)
                cost = st.number_input("Chi phí buổi tập (VNĐ)", min_value=0, step=1000)
                submitted = st.form_submit_button("Nhập chi phí")
                if submitted:
                    vote = next((v for v in st.session_state.votes if v['date'] == date_expense), None)
                    if vote is None or len(vote['voters']) == 0:
                        st.error("Ngày này không có thành viên tham gia.")
                    else:
                        per_person = cost / len(vote['voters'])
                        for email in vote['voters']:
                            users[email]['balance'] -= per_person
                        st.session_state.expenses.append({'date': date_expense, 'amount': cost, 'participants': vote['voters']})
                        save_all()
                        st.success(f"Đã nhập chi phí và trừ tiền cho {len(vote['voters'])} thành viên.")
                        st.rerun()
    else:
        st.info("Chức năng nhập chi phí buổi tập chỉ dành cho quản trị viên.")

    st.subheader("Số dư tài chính các thành viên")
    df = pd.DataFrame([{'Tên': users[email]['name'], 'Số tiền còn lại (VNĐ)': users[email]['balance']} for email in members])
    st.dataframe(df.style.format({"Số tiền còn lại (VNĐ)": "{:,.0f}"}).bar(subset=['Số tiền còn lại (VNĐ)'], color='#FF9800'))

# --- Tab Home: biểu đồ thống kê ---
def tab_home():
    st.header("📊 Trang chủ - Thống kê tổng quan")

    users = st.session_state.users
    members = [u for u in users.values() if u['role']=='member' and u['approved']]
    if not members:
        st.info("Chưa có thành viên nào được phê duyệt.")
        return

    df = pd.DataFrame(members)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🏅 Top thành viên theo số trận thắng")
        df_rank = df[['name', 'wins']].sort_values(by='wins', ascending=False).head(10)
        st.bar_chart(df_rank.set_index('name'))

    with col2:
        st.subheader("💵 Top thành viên theo số tiền còn lại")
        df_balance = df[['name', 'balance']].sort_values(by='balance', ascending=False).head(10)
        st.bar_chart(df_balance.set_index('name'))

    with col3:
        st.subheader("🗳️ Số lần tham gia chơi")
        vote_counts = {email:0 for email in users}
        for vote in st.session_state.votes:
            for v in vote['voters']:
                vote_counts[v] = vote_counts.get(v, 0) + 1
        df_vote = pd.DataFrame([
            {'name': users[email]['name'], 'votes': count}
            for email, count in vote_counts.items() if users[email]['role']=='member' and users[email]['approved']
        ])
        df_vote = df_vote.sort_values(by='votes', ascending=False).head(10)
        st.bar_chart(df_vote.set_index('name'))

# --- Main app ---
def main():
    st.set_page_config(page_title="Quản lý CLB Pickleball Ban CĐSCN", layout="wide", page_icon="🏓")

    st.sidebar.title("🏓 Menu")
    if 'login' not in st.session_state or not st.session_state.login:
        choice = st.sidebar.radio("Chọn chức năng", ["Đăng nhập", "Đăng ký"])
        if choice == "Đăng nhập":
            login()
        else:
            register()
    else:
        user = st.session_state.users[st.session_state.user_email]
        st.sidebar.markdown(f"**Xin chào, {user['name']}** ({st.session_state.user_role})")
        if st.sidebar.button("🚪 Đăng xuất"):
            st.session_state.login = False
            st.rerun()

        tabs = ["Home", "Thành viên", "Ranking", "Vote", "Quản lý tài chính"]
        if st.session_state.user_role == 'admin':
            tabs.insert(1, "Phê duyệt thành viên")

        choice = st.sidebar.radio("Chọn chức năng", tabs)

        if choice == "Home":
            tab_home()
        elif choice == "Phê duyệt thành viên":
            admin_approve_users()
        elif choice == "Thành viên":
            tab_members()
        elif choice == "Ranking":
            tab_ranking()
        elif choice == "Vote":
            tab_vote()
        elif choice == "Quản lý tài chính":
            tab_finance()

if __name__ == "__main__":
    main()