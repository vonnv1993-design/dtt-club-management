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
    save_json(MATCHES_FILE, st.session_state.matches)

# --- Đường dẫn file dữ liệu ---
USERS_FILE = "users.json"
VOTES_FILE = "votes.json"
EXPENSES_FILE = "expenses.json"
MATCHES_FILE = "matches.json"

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

# --- Khởi tạo dữ liệu ---
if 'users' not in st.session_state:
    st.session_state.users = load_json(USERS_FILE, default_users)

if 'pending_users' not in st.session_state:
    pending = {email: u for email, u in st.session_state.users.items() if not u.get('approved', False)}
    st.session_state.pending_users = pending

if 'votes' not in st.session_state:
    st.session_state.votes = load_json(VOTES_FILE, [])

if 'expenses' not in st.session_state:
    st.session_state.expenses = load_json(EXPENSES_FILE, [])

if 'matches' not in st.session_state:
    st.session_state.matches = load_json(MATCHES_FILE, [])

if 'vote_history' not in st.session_state:
    st.session_state.vote_history = []

# --- Hàm lấy tên ngày tiếng Việt ---
def get_weekday_vn(date_obj):
    weekday_map = {
        "Monday": "Thứ Hai",
        "Tuesday": "Thứ Ba",
        "Wednesday": "Thứ Tư",
        "Thursday": "Thứ Năm",
        "Friday": "Thứ Sáu",
        "Saturday": "Thứ Bảy",
        "Sunday": "Chủ Nhật"
    }
    return weekday_map.get(date_obj.strftime("%A"), date_obj.strftime("%A"))

# --- Hàm thêm lịch sử sửa bình chọn ---
def add_vote_history(action, description):
    st.session_state.vote_history.append({
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'action': action,
        'description': description
    })

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

# --- Hàm đăng ký ---
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

# --- Tab phê duyệt thành viên ---
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

    attendance_count = {email: 0 for email in users if users[email]['role'] == 'member' and users[email]['approved']}
    for vote in st.session_state.votes:
        for voter in vote['voters']:
            if voter in attendance_count:
                attendance_count[voter] += 1

    data = []
    for u in members:
        email = next((e for e, user in users.items() if user == u), None)
        count = attendance_count.get(email, 0)
        data.append({
            'Tên': u['name'],
            'Số điện thoại': u['phone'],
            'Số lần tham gia luyện tập': count,
            'Số tiền còn lại (VNĐ)': u['balance']
        })

    df = pd.DataFrame(data)
    st.dataframe(df.style.format({"Số tiền còn lại (VNĐ)": "{:,.0f}"}))

# --- Tab Ranking ---
def tab_ranking():
    st.header("🏆 Xếp hạng thành viên theo số trận thắng")
    users = st.session_state.users
    members = {email: u for email, u in users.items() if u['role'] == 'member' and u['approved']}
    if not members:
        st.info("Chưa có thành viên nào được phê duyệt.")
        return

    df = pd.DataFrame([
        {'email': email, 'Tên': u['name'], 'Số trận thắng': u['wins']}
        for email, u in members.items()
    ])

    def rank_label(wins):
        if wins > 50:
            return "Hạt giống 1"
        elif wins > 30:
            return "Hạt giống 2"
        elif wins > 10:
            return "Hạt giống 3"
        else:
            return ""

    df['Xếp loại'] = df['Số trận thắng'].apply(rank_label)
    df = df.sort_values(by='Số trận thắng', ascending=False).reset_index(drop=True)

    if st.session_state.user_role == 'admin':
        st.subheader("Chỉnh sửa số trận thắng")
        df_edit = df[['Tên', 'Số trận thắng']].copy().reset_index(drop=True)
        try:
            edited_df = st.data_editor(df_edit)  # Sử dụng st.data_editor ổn định
        except Exception as e:
            st.error(f"Lỗi hiển thị bảng chỉnh sửa: {e}")
            st.write(df_edit)  # Fallback hiển thị tĩnh

        if st.button("Lưu cập nhật"):
            for idx, row in edited_df.iterrows():
                name = row['Tên']
                wins_new = int(row['Số trận thắng'])
                email = next((e for e, u in members.items() if u['name'] == name), None)
                if email:
                    st.session_state.users[email]['wins'] = wins_new
            save_all()
            st.success("Đã cập nhật số trận thắng!")
            st.rerun()
    else:
        st.dataframe(df[['Tên', 'Số trận thắng', 'Xếp loại']].style.bar(subset=['Số trận thắng'], color='#4CAF50'))

    st.subheader("Chi tiết trận thắng")
    matches = st.session_state.matches
    if not matches:
        st.info("Chưa có trận thắng nào được nhập.")
    else:
        member_emails = list(members.keys())
        member_email = st.selectbox("Chọn thành viên", options=member_emails)
        member_name = users[member_email]['name']
        member_matches = [m for m in matches if m['player_email'] == member_email]
        if not member_matches:
            st.info(f"{member_name} chưa có trận thắng nào được nhập.")
        else:
            df_match = pd.DataFrame(member_matches)
            df_match_display = df_match.rename(columns={
                'date': 'Ngày thắng',
                'location': 'Địa điểm',
                'score': 'Tỉ số',
                'min_wins': 'Số trận thắng tối thiểu'
            })
            df_match_display = df_match_display[['Ngày thắng', 'Địa điểm', 'Tỉ số', 'Số trận thắng tối thiểu']]
            st.dataframe(df_match_display)

    if st.session_state.user_role == 'admin':
        st.subheader("Nhập trận thắng mới cho thành viên")
        with st.form("input_wins"):
            member_email = st.selectbox("Chọn thành viên", options=member_emails, key="input_wins_member")
            min_wins = st.number_input("Số trận thắng tối thiểu", min_value=1, step=1)
            date_str = st.date_input("Ngày trận thắng", value=datetime.today())
            location = st.text_input("Địa điểm")
            score = st.text_input("Tỉ số trận thắng (ví dụ 21:15)")
            submitted = st.form_submit_button("Thêm trận thắng")
            if submitted:
                if not location or not score:
                    st.error("Vui lòng nhập đầy đủ địa điểm và tỉ số trận thắng.")
                else:
                    st.session_state.users[member_email]['wins'] += min_wins
                    st.session_state.matches.append({
                        'player_email': member_email,
                        'min_wins': min_wins,
                        'date': date_str.strftime("%Y-%m-%d"),
                        'location': location,
                        'score': score
                    })
                    save_all()
                    st.success("Đã thêm trận thắng thành công!")
                    st.rerun()

# --- Tab Vote ---
def tab_vote():
    st.header("🗳️ Bình chọn tham gia chơi")

    # Tạo bình chọn mới (admin)
    if st.session_state.user_role == 'admin':
        st.subheader("Tạo bình chọn mới")
        with st.form("create_vote"):
            date_vote = st.date_input("Chọn ngày tham gia", value=datetime.today())
            weekday_vn = get_weekday_vn(date_vote)
            description = st.text_area("Mô tả bình chọn (ví dụ: Buổi tập kỹ thuật, giao hữu...)")
            submitted = st.form_submit_button("Tạo bình chọn")
            if submitted:
                date_str = date_vote.strftime("%Y-%m-%d")
                if any(v['date'] == date_str for v in st.session_state.votes):
                    st.warning("Đã có bình chọn cho ngày này.")
                else:
                    st.session_state.votes.append({
                        'date': date_str,
                        'weekday': weekday_vn,
                        'description': description,
                        'voters': []
                    })
                    add_vote_history("Tạo mới", f"Ngày {date_str}: {description}")
                    save_all()
                    st.success("Tạo bình chọn thành công!")
                    st.rerun()

        # Hiển thị lịch sử sửa bình chọn (admin)
        st.subheader("📜 Lịch sử sửa bình chọn")
        if st.session_state.vote_history:
            df_history = pd.DataFrame(st.session_state.vote_history)
            df_history = df_history.sort_values(by='timestamp', ascending=False)
            st.dataframe(df_history)
        else:
            st.info("Chưa có lịch sử sửa bình chọn.")

    # Bình chọn cho member
    if st.session_state.user_role == 'member':
        if not st.session_state.votes:
            st.info("Chưa có bình chọn nào.")
            return
        st.subheader("Bình chọn tham gia")
        for vote in st.session_state.votes:
            date_str = vote['date']
            voted = st.session_state.user_email in vote['voters']
            desc = vote.get('description', '')
            weekday = vote.get('weekday', '')
            with st.expander(f"{weekday} - {date_str} - {desc}"):
                if voted:
                    st.markdown(f"- ✅ Bạn đã tham gia bình chọn ngày **{date_str}**")
                else:
                    if st.button(f"Tham gia ngày {date_str}", key=date_str):
                        vote['voters'].append(st.session_state.user_email)
                        save_all()
                        st.success(f"Bạn đã tham gia bình chọn ngày {date_str}")
                        st.rerun()

    # Thống kê số lượng vote tham gia (bỏ cột 'Thứ')
    st.subheader("Thống kê số lượng vote tham gia")
    if not st.session_state.votes:
        st.info("Chưa có bình chọn nào.")
        return
    data = [{'Ngày': v['date'], 'Mô tả': v.get('description', ''), 'Số lượng tham gia': len(v['voters'])} for v in st.session_state.votes]
    df = pd.DataFrame(data).sort_values(by='Ngày', ascending=False)
    st.dataframe(df.style.bar(subset=['Số lượng tham gia'], color='#2196F3'))

# --- Tab Home ---
@st.cache_data  # Cache dữ liệu tĩnh để tối ưu hiệu suất trên cloud
def tab_home():
    st.header("📊 Trang chủ - Thống kê tổng quan")

    users = st.session_state.users
    members = [u for u in users.values() if u['role'] == 'member' and u['approved']]
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
        vote_counts = {email: 0 for email in users}
        for vote in st.session_state.votes:
            for v in vote['voters']:
                vote_counts[v] = vote_counts.get(v, 0) + 1
        data = []
        for email, count in vote_counts.items():
            user = users.get(email)
            if user and user['role'] == 'member' and user['approved']:
                data.append({'name': user['name'], 'votes': count})
        df_vote = pd.DataFrame(data)
        if not df_vote.empty:
            df_vote = df_vote.sort_values(by='votes', ascending=False).head(10)
            st.bar_chart(df_vote.set_index('name'))
        else:
            st.info("Chưa có dữ liệu bình chọn tham gia.")

# --- Tab Quản lý tài chính (mẫu) ---
def tab_finance():
    st.header("💰 Quản lý tài chính")
    st.info("Chức năng quản lý tài chính đang được phát triển.")

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

        try:
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
        except Exception as e:
            st.error(f"Lỗi khi tải tab {choice}: {e}")

if __name__ == "__main__":
    main()

