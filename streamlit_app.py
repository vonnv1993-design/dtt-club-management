import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="DTT PICKLEBALL CLUB",
    page_icon="🏓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS (giữ nguyên như bạn đã cung cấp)
st.markdown("""
<style>
    /* CSS styles như code bạn đã cung cấp */
    /* ... (bạn giữ nguyên phần CSS) ... */
</style>
""", unsafe_allow_html=True)

DB_FILE = "pickleball_club.db"

def init_database():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                password TEXT NOT NULL,
                is_approved INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                approved_at TEXT,
                approved_by TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                match_date TEXT,
                location TEXT,
                score TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vote_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date TEXT,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS finances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                transaction_type TEXT,
                description TEXT,
                session_date TEXT,
                court_fee INTEGER DEFAULT 0,
                water_fee INTEGER DEFAULT 0,
                other_fee INTEGER DEFAULT 0,
                total_participants INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('admin@local',))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO users (full_name, email, phone, birth_date, password, is_approved, is_admin, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('Administrator', 'admin@local', '0000000000', '1990-01-01',
                  hashlib.sha256('Admin@123'.encode()).hexdigest(), 1, 1,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi khởi tạo database: {str(e)}")
        return False

def get_db_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(full_name, email, phone, birth_date, password):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        email_norm = email.lower().strip()
        cursor.execute('''
            INSERT INTO users (full_name, email, phone, birth_date, password, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (full_name, email_norm, phone, str(birth_date), hash_password(password),
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True, "Đăng ký thành công! Vui lòng chờ admin phê duyệt."
    except sqlite3.IntegrityError:
        if conn:
            conn.close()
        return False, "Email đã tồn tại!"
    except Exception as e:
        if conn:
            conn.close()
        return False, f"Lỗi đăng ký: {str(e)}"

def login_user(email, password):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        email_norm = email.lower().strip()
        cursor.execute('''
            SELECT id, full_name, is_approved, is_admin FROM users 
            WHERE email = ? AND password = ?
        ''', (email_norm, hash_password(password)))
        user = cursor.fetchone()
        conn.close()
        if user:
            is_admin = int(user[3])
            is_approved = int(user[2])
            if is_admin == 1 or is_approved == 1:
                return True, {
                    'id': user[0],
                    'name': user[1],
                    'is_admin': is_admin == 1
                }
            else:
                return False, "Tài khoản chưa được phê duyệt!"
        return False, "Email hoặc mật khẩu không đúng!"
    except Exception as e:
        return False, f"Lỗi đăng nhập: {str(e)}"

# Các hàm lấy danh sách, phê duyệt, từ chối, thêm, sửa, xóa thành viên, và các hàm quản lý khác giữ nguyên logic như bạn đã cung cấp,
# chỉ sửa lỗi nhỏ như chuẩn hóa email, lấy affected_rows đúng, và thay st.rerun() bằng st.experimental_rerun().

# Ví dụ hàm delete_member đã sửa:
def delete_member(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM rankings WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM votes WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM finances WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM users WHERE id = ? AND is_admin = 0', (user_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        if affected_rows > 0:
            return True, "Đã xóa thành viên và tất cả dữ liệu liên quan!"
        else:
            return False, "Không thể xóa (có thể là admin hoặc thành viên không tồn tại)!"
    except Exception as e:
        if conn:
            conn.close()
        return False, f"Lỗi xóa thành viên: {str(e)}"

# Hàm show_auth_page với chuẩn hóa email và dùng st.experimental_rerun()
def show_auth_page():
    tab1, tab2 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký"])
    with tab1:
        st.subheader("Đăng nhập vào hệ thống")
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="Nhập địa chỉ email")
            password = st.text_input("🔒 Mật khẩu", type="password", placeholder="Nhập mật khẩu")
            if st.form_submit_button("Đăng nhập", use_container_width=True):
                if email and password:
                    success, result = login_user(email, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user = result
                        st.experimental_rerun()
                    else:
                        st.error(result)
                else:
                    st.error("Vui lòng nhập đầy đủ thông tin!")
        st.info("💡 Cần hỗ trợ liên hệ vonnv")
    with tab2:
        st.subheader("Đăng ký thành viên mới")
        with st.form("register_form"):
            full_name = st.text_input("👤 Họ và tên", placeholder="Nhập họ và tên đầy đủ")
            email = st.text_input("📧 Email", placeholder="Nhập địa chỉ email")
            phone = st.text_input("📱 Số điện thoại", placeholder="Nhập số điện thoại")
            birth_date = st.date_input("📅 Ngày sinh", min_value=datetime(1950, 1, 1), max_value=datetime(2010, 12, 31))
            password = st.text_input("🔒 Mật khẩu", type="password", placeholder="Nhập mật khẩu")
            confirm_password = st.text_input("🔒 Xác nhận mật khẩu", type="password", placeholder="Nhập lại mật khẩu")
            if st.form_submit_button("Đăng ký", use_container_width=True):
                if all([full_name, email, phone, birth_date, password, confirm_password]):
                    if password == confirm_password:
                        success, message = register_user(full_name, email, phone, birth_date, password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.error("Mật khẩu xác nhận không khớp!")
                else:
                    st.error("Vui lòng nhập đầy đủ thông tin!")

# Hàm show_member_management_page với xác nhận xóa thành viên bằng st.session_state
def show_member_management_page():
    if not st.session_state.user['is_admin']:
        st.error("Chỉ admin mới có quyền truy cập trang này!")
        return
    st.title("✏️ Quản lý thành viên")
    tab1, tab2, tab3 = st.tabs(["➕ Thêm thành viên", "✏️ Sửa thành viên", "🗑️ Xóa thành viên"])
    with tab1:
        st.subheader("Thêm thành viên mới")
        st.info("💡 Thành viên được thêm bởi admin sẽ được phê duyệt ngay lập tức")
        with st.form("add_member_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("👤 Họ và tên", placeholder="Nhập họ và tên đầy đủ")
                email = st.text_input("📧 Email", placeholder="Nhập địa chỉ email")
                phone = st.text_input("📱 Số điện thoại", placeholder="Nhập số điện thoại")
            with col2:
                birth_date = st.date_input("📅 Ngày sinh", min_value=datetime(1950, 1, 1), max_value=datetime(2010, 12, 31))
                password = st.text_input("🔒 Mật khẩu", type="password", placeholder="Nhập mật khẩu")
                confirm_password = st.text_input("🔒 Xác nhận mật khẩu", type="password", placeholder="Nhập lại mật khẩu")
            if st.form_submit_button("💾 Thêm thành viên", use_container_width=True):
                if all([full_name, email, phone, birth_date, password, confirm_password]):
                    if password == confirm_password:
                        success, message = add_member_direct(full_name, email, phone, birth_date, password)
                        if success:
                            st.success(message)
                            st.experimental_rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Mật khẩu xác nhận không khớp!")
                else:
                    st.error("Vui lòng nhập đầy đủ thông tin!")
    with tab2:
        st.subheader("Chỉnh sửa thông tin thành viên")
        members_df = get_approved_members()
        if members_df.empty:
            st.info("Chưa có thành viên nào để chỉnh sửa")
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                member_options = [f"{row['full_name']} ({row['email']})" for _, row in members_df.iterrows()]
                selected_idx = st.selectbox("👤 Chọn thành viên cần sửa", range(len(member_options)), format_func=lambda x: member_options[x])
                selected_member = members_df.iloc[selected_idx]
            with col2:
                if st.button("📝 Chọn để sửa", use_container_width=True):
                    st.session_state.editing_member_id = selected_member['id']
                    st.experimental_rerun()
            if st.session_state.editing_member_id:
                member_data = get_member_by_id(st.session_state.editing_member_id)
                if member_data:
                    st.markdown(f"""
                        <div class="edit-form">
                            <h4>✏️ Đang sửa: {member_data['full_name']}</h4>
                        </div>
                    """, unsafe_allow_html=True)
                    with st.form("edit_member_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_full_name = st.text_input("👤 Họ và tên", value=member_data['full_name'])
                            edit_email = st.text_input("📧 Email", value=member_data['email'])
                            edit_phone = st.text_input("📱 Số điện thoại", value=member_data['phone'])
                        with col2:
                            edit_birth_date = st.date_input("📅 Ngày sinh", value=datetime.strptime(member_data['birth_date'], '%Y-%m-%d').date())
                            edit_password = st.text_input("🔒 Mật khẩu mới (để trống nếu không đổi)", type="password")
                            confirm_edit_password = st.text_input("🔒 Xác nhận mật khẩu mới", type="password")
                        col_submit, col_cancel = st.columns(2)
                        with col_submit:
                            if st.form_submit_button("💾 Cập nhật", use_container_width=True):
                                if edit_password and edit_password != confirm_edit_password:
                                    st.error("Mật khẩu xác nhận không khớp!")
                                else:
                                    success, message = update_member(
                                        st.session_state.editing_member_id,
                                        edit_full_name, edit_email, edit_phone, edit_birth_date,
                                        edit_password if edit_password else None
                                    )
                                    if success:
                                        st.success(message)
                                        st.session_state.editing_member_id = None
                                        st.experimental_rerun()
                                    else:
                                        st.error(message)
                        with col_cancel:
                            if st.form_submit_button("❌ Hủy", use_container_width=True):
                                st.session_state.editing_member_id = None
                                st.experimental_rerun()
    with tab3:
        st.subheader("Xóa thành viên")
        st.warning("⚠️ **Cảnh báo**: Xóa thành viên sẽ xóa toàn bộ dữ liệu liên quan (rankings, votes, finances)")
        members_df = get_approved_members()
        if members_df.empty:
            st.info("Chưa có thành viên nào để xóa")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📋 Danh sách thành viên")
                for _, member in members_df.iterrows():
                    st.markdown(f"""
                        <div class="member-card">
                            <strong>👤 {member['full_name']}</strong><br>
                            📧 {member['email']}<br>
                            📱 {member['phone']}
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🗑️ Xóa {member['full_name']}", key=f"delete_{member['id']}", type="secondary", use_container_width=True):
                        st.session_state.member_to_delete = member['id']
                        st.session_state.member_to_delete_name = member['full_name']
                        st.experimental_rerun()
            with col2:
                if 'member_to_delete' in st.session_state:
                    st.error(f"⚠️ Bạn có chắc chắn muốn xóa **{st.session_state.member_to_delete_name}**?")
                    st.write("Hành động này không thể hoàn tác!")
                    col_confirm, col_cancel_delete = st.columns(2)
                    with col_confirm:
                        if st.button("✅ Xác nhận xóa", key="confirm_delete", type="primary", use_container_width=True):
                            success, message = delete_member(st.session_state.member_to_delete)
                            if success:
                                st.success(message)
                                del st.session_state.member_to_delete
                                del st.session_state.member_to_delete_name
                                st.experimental_rerun()
                            else:
                                st.error(message)
                    with col_cancel_delete:
                        if st.button("❌ Hủy", key="cancel_delete", use_container_width=True):
                            del st.session_state.member_to_delete
                            del st.session_state.member_to_delete_name
                            st.experimental_rerun()

# Các hàm show_home_page, show_approval_page, show_members_page, show_ranking_page, show_voting_page, show_finance_page, show_alerts_page giữ nguyên như bạn đã cung cấp, chỉ thay st.rerun() bằng st.experimental_rerun().

def main():
    if not st.session_state.get('db_initialized', False):
        st.session_state.db_initialized = init_database()
    st.markdown("""
        <div class="main-header">
            <h1>🏓 DTT PICKLEBALL CLUB</h1>
            <p>Hệ thống quản lý câu lạc bộ Pickleball chuyên nghiệp</p>
        </div>
    """, unsafe_allow_html=True)
    if not st.session_state.get('logged_in', False):
        show_auth_page()
    else:
        show_main_app()

if __name__ == "__main__":
    main()