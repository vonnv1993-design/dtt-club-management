import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import hashlib

# --- Hàm băm mật khẩu đơn giản ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Khởi tạo dữ liệu lưu trong session_state ---
if 'users' not in st.session_state:
    # users: dict email -> {name, phone, password_hash, role, approved, wins, balance, votes}
    st.session_state.users = {
        'admin': {
            'name': 'Admin',
            'phone': '',
            'password_hash': hash_password('Admin@123'),
            'role': 'admin',
            'approved': True,
            'wins': 0,
            'balance': 0,
            'votes': []
        }
    }

if 'pending_users' not in st.session_state:
    st.session_state.pending_users = {}  # email -> user info chờ duyệt

if 'votes' not in st.session_state:
    # votes: list of dict {date, voters: list of emails}
    st.session_state.votes = []

if 'expenses' not in st.session_state:
    # expenses: list of dict {date, amount, participants: list of emails}
    st.session_state.expenses = []

# --- Hàm đăng nhập ---
def login():
    st.title("Đăng nhập Câu lạc bộ Pickleball Ban CĐSCN")
    email = st.text_input("Email")
    password = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
        if email in st.session_state.users:
            user = st.session_state.users[email]
            if user['password_hash'] == hash_password(password):
                if user['approved']:
                    st.session_state['login'] = True
                    st.session_state['user_email'] = email
                    st.session_state['user_role'] = user['role']
                    st.success(f"Chào mừng {user['name']}!")
                else:
                    st.error("Tài khoản chưa được phê duyệt.")
            else:
                st.error("Mật khẩu không đúng.")
        else:
            st.error("Email không tồn tại.")

# --- Hàm đăng ký thành viên ---
def register():
    st.title("Đăng ký thành viên mới")
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
            # Lưu vào pending_users
            st.session_state.pending_users[email] = {
                'name': name,
                'phone': phone,
                'password_hash': hash_password(password),
                'role': 'member',
                'approved': False,
                'wins': 0,
                'balance': 0,
                'votes': []
            }
            st.success("Đăng ký thành công! Vui lòng chờ quản trị viên phê duyệt.")

# --- Tab quản trị viên duyệt thành viên ---
def admin_approve_users():
    st.title("Phê duyệt thành viên mới")
    pending = st.session_state.pending_users
    if not pending:
        st.info("Không có thành viên chờ phê duyệt.")
        return
    for email, info in list(pending.items()):
        st.write(f"**Tên:** {info['name']} - **Email:** {email} - **SĐT:** {info['phone']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Phê duyệt {email}"):
                info['approved'] = True
                st.session_state.users[email] = info
                del st.session_state.pending_users[email]
                st.success(f"Đã phê duyệt {email}")
                st.experimental_rerun()
        with col2:
            if st.button(f"Từ chối {email}"):
                del st.session_state.pending_users[email]
                st.warning(f"Đã từ chối {email}")
                st.experimental_rerun()

# --- Tab danh sách thành viên ---
def tab_members():
    st.title("Danh sách thành viên")
    users = st.session_state.users
    members = [u for u in users.values() if u['role'] == 'member' and u['approved']]
    if not members:
        st.info("Chưa có thành viên nào được phê duyệt.")
        return
    df = pd.DataFrame(members)
    df_display = df[['name', 'phone', 'wins', 'balance']]
    df_display.columns = ['Tên', 'Số điện thoại', 'Số trận thắng', 'Số tiền còn lại (VNĐ)']
    st.dataframe(df_display)

# --- Tab Ranking ---
def tab_ranking():
    st.title("Xếp hạng thành viên theo số trận thắng")
    users = st.session_state.users
    members = [u for u in users.values() if u['role'] == 'member' and u['approved']]
    if not members:
        st.info("Chưa có thành viên nào được phê duyệt.")
        return
    df = pd.DataFrame(members)
    df = df[['name', 'wins']]
    df = df.sort_values(by='wins', ascending=False)
    df.columns = ['Tên', 'Số trận thắng']
    st.dataframe(df)

    # Admin nhập trận thắng
    if st.session_state.user_role == 'admin':
        st.subheader("Nhập trận thắng cho thành viên")
        with st.form("input_wins"):
            member_email = st.selectbox("Chọn thành viên", options=[email for email, u in st.session_state.users.items() if u['role']=='member' and u['approved']])
            wins_add = st.number_input("Số trận thắng thêm", min_value=0, step=1)
            submitted = st.form_submit_button("Cập nhật")
            if submitted:
                st.session_state.users[member_email]['wins'] += wins_add
                st.success("Cập nhật thành công!")
                st.experimental_rerun()

# --- Tab Vote tham gia chơi ---
def tab_vote():
    st.title("Bình chọn tham gia chơi")
    # Admin tạo bình chọn
    if st.session_state.user_role == 'admin':
        st.subheader("Tạo bình chọn mới")
        with st.form("create_vote"):
            date_vote = st.date_input("Chọn ngày tham gia", value=datetime.today())
            submitted = st.form_submit_button("Tạo bình chọn")
            if submitted:
                # Kiểm tra đã có vote ngày đó chưa
                for v in st.session_state.votes:
                    if v['date'] == date_vote:
                        st.warning("Đã có bình chọn cho ngày này.")
                        break
                else:
                    st.session_state.votes.append({'date': date_vote, 'voters': []})
                    st.success("Tạo bình chọn thành công!")
                    st.experimental_rerun()

    # Thành viên vote
    if st.session_state.user_role == 'member':
        if not st.session_state.votes:
            st.info("Chưa có bình chọn nào.")
            return
        st.subheader("Bình chọn tham gia")
        for vote in st.session_state.votes:
            date_str = vote['date'].strftime("%Y-%m-%d")
            voted = st.session_state.user_email in vote['voters']
            if voted:
                st.write(f"Bạn đã tham gia bình chọn ngày {date_str}")
            else:
                if st.button(f"Tham gia ngày {date_str}", key=date_str):
                    vote['voters'].append(st.session_state.user_email)
                    st.success(f"Bạn đã tham gia bình chọn ngày {date_str}")
                    st.experimental_rerun()

    # Thống kê số lượng vote
    st.subheader("Thống kê số lượng vote tham gia")
    if not st.session_state.votes:
        st.info("Chưa có bình chọn nào.")
        return
    data = []
    for vote in st.session_state.votes:
        data.append({'Ngày': vote['date'], 'Số lượng tham gia': len(vote['voters'])})
    df = pd.DataFrame(data)
    df = df.sort_values(by='Ngày', ascending=False)
    st.dataframe(df)

# --- Tab quản lý tài chính ---
def tab_finance():
    st.title("Quản lý tài chính")
    users = st.session_state.users
    members = [email for email, u in users.items() if u['role']=='member' and u['approved']]

    # Admin nhập số tiền đóng góp
    st.subheader("Nhập số tiền đóng góp của thành viên")
    with st.form("input_contribution"):
        member_email = st.selectbox("Chọn thành viên", options=members)
        amount = st.number_input("Số tiền đóng góp (VNĐ)", min_value=0, step=1000)
        submitted = st.form_submit_button("Cập nhật đóng góp")
        if submitted:
            users[member_email]['balance'] += amount
            st.success("Cập nhật đóng góp thành công!")
            st.experimental_rerun()

    # Admin nhập chi phí buổi tập
    st.subheader("Nhập chi phí buổi tập")
    with st.form("input_expense"):
        if not st.session_state.votes:
            st.info("Chưa có bình chọn nào để xác định người tham gia.")
        else:
            # Chọn ngày có vote
            vote_dates = [v['date'] for v in st.session_state.votes]
            date_expense = st.selectbox("Chọn ngày buổi tập", options=vote_dates)
            cost = st.number_input("Chi phí buổi tập (VNĐ)", min_value=0, step=1000)
            submitted = st.form_submit_button("Nhập chi phí")
            if submitted:
                # Tìm vote ngày đó
                vote = next((v for v in st.session_state.votes if v['date'] == date_expense), None)
                if vote is None or len(vote['voters']) == 0:
                    st.error("Ngày này không có thành viên tham gia.")
                else:
                    per_person = cost / len(vote['voters'])
                    for email in vote['voters']:
                        users[email]['balance'] -= per_person
                    st.session_state.expenses.append({'date': date_expense, 'amount': cost, 'participants': vote['voters']})
                    st.success(f"Đã nhập chi phí và trừ tiền cho {len(vote['voters'])} thành viên.")
                    st.experimental_rerun()

    # Hiển thị bảng số dư tài chính
    st.subheader("Số dư tài chính các thành viên")
    df = pd.DataFrame([{'Tên': users[email]['name'], 'Số tiền còn lại (VNĐ)': users[email]['balance']} for email in members])
    st.dataframe(df)

# --- Tab Home: biểu đồ thống kê ---
def tab_home():
    st.title("Trang chủ - Thống kê")

    users = st.session_state.users
    members = [u for u in users.values() if u['role']=='member' and u['approved']]
    if not members:
        st.info("Chưa có thành viên nào được phê duyệt.")
        return

    df = pd.DataFrame(members)

    # Top Ranking
    st.subheader("Top thành viên theo số trận thắng")
    df_rank = df[['name', 'wins']].sort_values(by='wins', ascending=False).head(10)
    st.bar_chart(df_rank.set_index('name'))

    # Top tiền còn nhiều nhất
    st.subheader("Top thành viên theo số tiền còn lại")
    df_balance = df[['name', 'balance']].sort_values(by='balance', ascending=False).head(10)
    st.bar_chart(df_balance.set_index('name'))

    # Số lần vote tham gia
    st.subheader("Số lần tham gia chơi")
    # Tính số lần vote mỗi thành viên
    vote_counts = {}
    for email in users:
        vote_counts[email] = 0
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
    st.set_page_config(page_title="Quản lý CLB Pickleball Ban CĐSCN", layout="wide")

    if 'login' not in st.session_state or not st.session_state.login:
        # Nếu chưa đăng nhập, hiển thị đăng nhập và đăng ký
        tab = st.sidebar.selectbox("Chọn", ["Đăng nhập", "Đăng ký"])
        if tab == "Đăng nhập":
            login()
        else:
            register()
    else:
        # Đã đăng nhập
        st.sidebar.write(f"Xin chào, {st.session_state.users[st.session_state.user_email]['name']} ({st.session_state.user_role})")
        if st.sidebar.button("Đăng xuất"):
            st.session_state.login = False
            st.experimental_rerun()

        # Menu chính
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