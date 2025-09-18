import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timedelta

# --- Cấu hình trang ---
st.set_page_config(
    page_title="DTT PICKLEBALL CLUB",
    page_icon="🏓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS tùy chỉnh ---
st.markdown("""
<style>
    /* CSS bạn đã cung cấp, giữ nguyên */
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5a87 100%);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    /* ... (bạn thêm toàn bộ CSS từ code gốc) ... */
</style>
""", unsafe_allow_html=True)

DB_FILE = "pickleball_club.db"

# --- Database ---
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

# --- Authentication ---
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

# --- Thành viên ---
def get_pending_members():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query('''
            SELECT id, full_name, email, phone, birth_date, created_at
            FROM users 
            WHERE is_approved = 0 AND is_admin = 0
            ORDER BY created_at DESC
        ''', conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Lỗi lấy pending members: {str(e)}")
        return pd.DataFrame()

def get_approved_members():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query('''
            SELECT id, full_name, email, phone, birth_date
            FROM users 
            WHERE is_approved = 1 AND is_admin = 0
            ORDER BY full_name
        ''', conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Lỗi lấy approved members: {str(e)}")
        return pd.DataFrame()

def approve_member(user_id, admin_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET is_approved = 1, approved_at = ?, approved_by = ?
            WHERE id = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), admin_name, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi phê duyệt: {str(e)}")
        return False

def reject_member(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi từ chối: {str(e)}")
        return False

def add_member_direct(full_name, email, phone, birth_date, password):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        email_norm = email.lower().strip()
        cursor.execute('''
            INSERT INTO users (full_name, email, phone, birth_date, password, is_approved, created_at, approved_at, approved_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (full_name, email_norm, phone, str(birth_date), hash_password(password), 1, 
              datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
              datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
              'Admin'))
        conn.commit()
        conn.close()
        return True, "Đã thêm thành viên thành công!"
    except sqlite3.IntegrityError:
        if conn:
            conn.close()
        return False, "Email đã tồn tại!"
    except Exception as e:
        if conn:
            conn.close()
        return False, f"Lỗi thêm thành viên: {str(e)}"

def update_member(user_id, full_name, email, phone, birth_date, password=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        email_norm = email.lower().strip()
        if password:
            cursor.execute('''
                UPDATE users 
                SET full_name = ?, email = ?, phone = ?, birth_date = ?, password = ?
                WHERE id = ? AND is_admin = 0
            ''', (full_name, email_norm, phone, str(birth_date), hash_password(password), user_id))
        else:
            cursor.execute('''
                UPDATE users 
                SET full_name = ?, email = ?, phone = ?, birth_date = ?
                WHERE id = ? AND is_admin = 0
            ''', (full_name, email_norm, phone, str(birth_date), user_id))
        conn.commit()
        conn.close()
        return True, "Đã cập nhật thông tin thành viên!"
    except sqlite3.IntegrityError:
        if conn:
            conn.close()
        return False, "Email đã tồn tại!"
    except Exception as e:
        if conn:
            conn.close()
        return False, f"Lỗi cập nhật: {str(e)}"

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

def get_member_by_id(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, full_name, email, phone, birth_date
            FROM users 
            WHERE id = ? AND is_admin = 0
        ''', (user_id,))
        member = cursor.fetchone()
        conn.close()
        if member:
            return {
                'id': member[0],
                'full_name': member[1],
                'email': member[2],
                'phone': member[3],
                'birth_date': member[4]
            }
        return None
    except Exception as e:
        st.error(f"Lỗi lấy thông tin thành viên: {str(e)}")
        return None

# --- Xếp hạng ---
def get_rankings():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query('''
            SELECT u.full_name, COUNT(r.id) as total_wins
            FROM users u
            LEFT JOIN rankings r ON u.id = r.user_id
            WHERE u.is_approved = 1 AND u.is_admin = 0
            GROUP BY u.id, u.full_name
            ORDER BY total_wins DESC
        ''', conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Lỗi lấy rankings: {str(e)}")
        return pd.DataFrame()

def add_ranking(user_name, wins, match_date, location, score):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE full_name = ? AND is_approved = 1 AND is_admin = 0', (user_name,))
        user = cursor.fetchone()
        if user:
            for _ in range(wins):
                cursor.execute('''
                    INSERT INTO rankings (user_id, match_date, location, score, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user[0], str(match_date), location, score, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi thêm ranking: {str(e)}")
        return False

# --- Bình chọn ---
def get_vote_sessions():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query('''
            SELECT vs.id, vs.session_date, vs.description, 
                   COUNT(CASE WHEN u.is_admin = 0 THEN v.id END) as vote_count
            FROM vote_sessions vs
            LEFT JOIN votes v ON vs.session_date = v.session_date
            LEFT JOIN users u ON v.user_id = u.id
            GROUP BY vs.id, vs.session_date, vs.description
            ORDER BY vs.session_date DESC
        ''', conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Lỗi lấy vote sessions: {str(e)}")
        return pd.DataFrame()

def create_vote_session(session_date, description):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO vote_sessions (session_date, description, created_at)
            VALUES (?, ?, ?)
        ''', (str(session_date), description, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi tạo vote session: {str(e)}")
        return False

def vote_for_session(user_id, session_date):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM votes WHERE user_id = ? AND session_date = ?
        ''', (user_id, str(session_date)))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO votes (user_id, session_date, created_at)
                VALUES (?, ?, ?)
            ''', (user_id, str(session_date), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            return True
        else:
            conn.close()
            return False
    except Exception as e:
        st.error(f"Lỗi vote: {str(e)}")
        return False

def get_vote_details(session_date):
    try:
        conn = get_db_connection()
        df = pd.read_sql_query('''
            SELECT u.full_name, v.created_at
            FROM votes v
            JOIN users u ON v.user_id = u.id
            WHERE v.session_date = ? AND u.is_admin = 0
            ORDER BY v.created_at
        ''', conn, params=[str(session_date)])
        conn.close()
        return df
    except Exception as e:
        st.error(f"Lỗi lấy chi tiết vote: {str(e)}")
        return pd.DataFrame()

# --- Tài chính ---
def add_contribution(user_name, amount):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE full_name = ? AND is_approved = 1 AND is_admin = 0', (user_name,))
        user = cursor.fetchone()
        if user:
            cursor.execute('''
                INSERT INTO finances (user_id, amount, transaction_type, description, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user[0], amount, 'contribution', 'Đóng quỹ', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi thêm đóng góp: {str(e)}")
        return False

def get_vote_sessions_for_expense():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query('''
            SELECT vs.session_date, vs.description, 
                   COUNT(CASE WHEN u.is_admin = 0 THEN v.id END) as vote_count
            FROM vote_sessions vs
            LEFT JOIN votes v ON vs.session_date = v.session_date
            LEFT JOIN users u ON v.user_id = u.id
            GROUP BY vs.session_date, vs.description
            HAVING vote_count > 0
            ORDER BY vs.session_date DESC
        ''', conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Lỗi lấy vote sessions for expense: {str(e)}")
        return pd.DataFrame()

def add_expense(session_date, court_fee, water_fee, other_fee, description):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        total_fee = court_fee + water_fee + other_fee
        cursor.execute('''
            SELECT v.user_id FROM votes v
            JOIN users u ON v.user_id = u.id
            WHERE v.session_date = ? AND u.is_admin = 0
        ''', (str(session_date),))
        voters = cursor.fetchall()
        if voters:
            cost_per_person = total_fee // len(voters)
            for voter in voters:
                cursor.execute('''
                    INSERT INTO finances (user_id, amount, transaction_type, description, session_date, 
                                        court_fee, water_fee, other_fee, total_participants, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (voter[0], -cost_per_person, 'expense', description, str(session_date), 
                      court_fee // len(voters), water_fee // len(voters), other_fee // len(voters), 
                      len(voters), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            return True, f"Đã chia {total_fee:,} VNĐ cho {len(voters)} thành viên ({cost_per_person:,} VNĐ/người)"
        else:
            conn.close()
            return False, "Không có thành viên nào vote cho buổi này"
    except Exception as e:
        if conn:
            conn.close()
        return False, f"Lỗi thêm chi phí: {str(e)}"
def get_financial_summary():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query('''
            SELECT u.full_name,
                   COALESCE(SUM(CASE WHEN f.transaction_type = 'contribution' THEN f.amount ELSE 0 END), 0) as total_contribution,
                   COUNT(CASE WHEN f.transaction_type = 'expense' THEN 1 END) as sessions_attended,
                   COALESCE(SUM(CASE WHEN f.transaction_type = 'expense' THEN f.amount ELSE 0 END), 0) as total_expenses,
                   COALESCE(SUM(f.amount), 0) as balance
            FROM users u
            LEFT JOIN finances f ON u.id = f.user_id
            WHERE u.is_approved = 1 AND u.is_admin = 0
            GROUP BY u.id, u.full_name
            ORDER BY balance DESC
        ''', conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Lỗi lấy financial summary: {str(e)}")
        return pd.DataFrame()

def get_expense_history():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query('''
            SELECT 
                f.session_date,
                f.description,
                MAX(f.total_participants) as participants_count,
                SUM(-f.amount) as total_cost,
                (-f.amount) as cost_per_person,
                f.created_at
            FROM finances f
            WHERE f.transaction_type = 'expense' AND f.session_date != ''
            GROUP BY f.session_date, f.description, f.amount, f.created_at
            ORDER BY f.session_date DESC, f.created_at DESC
        ''', conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Lỗi lấy expense history: {str(e)}")
        return pd.DataFrame()

def show_finance_page():
    st.title("💰 Quản lý tài chính")
    if st.session_state.user['is_admin']:
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("➕ Thêm đóng góp"):
                with st.form("add_contribution_form"):
                    members_df = get_approved_members()
                    members = members_df['full_name'].tolist() if not members_df.empty else []
                    if members:
                        member_name = st.selectbox("👤 Thành viên", members)
                        amount = st.number_input("💵 Số tiền (VNĐ)", min_value=10000, step=10000)
                        if st.form_submit_button("💾 Lưu", use_container_width=True):
                            if add_contribution(member_name, amount):
                                st.success(f"Đã thêm {amount:,} VNĐ cho {member_name}")
                                st.experimental_rerun()
                    else:
                        st.warning("Chưa có thành viên nào được phê duyệt")
        with col2:
            with st.expander("➕ Thêm chi phí buổi tập"):
                vote_sessions_df = get_vote_sessions_for_expense()
                if not vote_sessions_df.empty:
                    with st.form("add_expense_form"):
                        session_options = []
                        for _, row in vote_sessions_df.iterrows():
                            session_options.append(f"{row['session_date']} - {row['description']} ({row['vote_count']} người)")
                        selected_session_idx = st.selectbox("📅 Chọn buổi tập", range(len(session_options)), 
                                                           format_func=lambda x: session_options[x])
                        selected_session = vote_sessions_df.iloc[selected_session_idx]
                        st.info(f"💡 Chi phí sẽ được chia đều cho {selected_session['vote_count']} thành viên")
                        court_fee = st.number_input("🏸 Tiền sân (VNĐ)", min_value=0, step=10000, value=200000)
                        water_fee = st.number_input("💧 Tiền nước (VNĐ)", min_value=0, step=5000, value=50000)
                        other_fee = st.number_input("➕ Chi phí khác (VNĐ)", min_value=0, step=5000, value=0)
                        description = st.text_input("📝 Ghi chú", value="Chi phí buổi tập")
                        total = court_fee + water_fee + other_fee
                        if total > 0:
                            cost_per_person = total // selected_session['vote_count']
                            st.success(f"💰 Tổng: {total:,} VNĐ | Mỗi người: {cost_per_person:,} VNĐ")
                        if st.form_submit_button("💾 Lưu chi phí", use_container_width=True):
                            if total > 0:
                                success, message = add_expense(selected_session['session_date'], court_fee, water_fee, other_fee, description)
                                if success:
                                    st.success(message)
                                    st.experimental_rerun()
                                else:
                                    st.error(message)
                else:
                    st.warning("Chưa có buổi tập nào có vote")
    st.subheader("📋 Lịch sử chi phí các buổi tập")
    expense_history = get_expense_history()
    if not expense_history.empty:
        for _, expense in expense_history.iterrows():
            st.markdown(f"""
                <div class="expense-card">
                    <h4>📅 {expense['session_date']} - {expense['description']}</h4>
                    <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                        <div>
                            <strong>👥 Số người tham gia:</strong> {expense['participants_count']}<br>
                            <strong>👤 Chi phí/người:</strong> {expense['cost_per_person']:,} VNĐ
                        </div>
                        <div style="text-align: right;">
                            <strong>💰 Tổng chi phí:</strong> {expense['total_cost']:,} VNĐ
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Chưa có chi phí nào được ghi nhận")
    financial_df = get_financial_summary()
    if not financial_df.empty:
        st.subheader("📊 Tổng quan tài chính thành viên")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_contributions = financial_df['total_contribution'].sum()
            st.metric("💰 Tổng đóng góp", f"{total_contributions:,} VNĐ")
        with col2:
            total_expenses = abs(financial_df['total_expenses'].sum())
            st.metric("💸 Tổng chi phí", f"{total_expenses:,} VNĐ")
        with col3:
            total_balance = financial_df['balance'].sum()
            st.metric("🏦 Số dư quỹ", f"{total_balance:,} VNĐ")
        with col4:
            avg_sessions = financial_df['sessions_attended'].mean()
            st.metric("📊 TB buổi tham gia", f"{avg_sessions:.1f}")
        st.subheader("📋 Chi tiết tài chính từng thành viên")
        display_df = financial_df.copy()
        display_df['total_contribution'] = display_df['total_contribution'].apply(lambda x: f"{x:,} VNĐ")
        display_df['total_expenses'] = display_df['total_expenses'].apply(lambda x: f"{abs(x):,} VNĐ")
        display_df['balance'] = display_df['balance'].apply(lambda x: f"{x:,} VNĐ")
        display_df.index = range(1, len(display_df) + 1)
        st.dataframe(
            display_df.rename(columns={
                'full_name': 'Tên thành viên',
                'total_contribution': 'Đã đóng góp',
                'sessions_attended': 'Buổi tham gia',
                'total_expenses': 'Tổng chi phí',
                'balance': 'Số dư'
            }),
            use_container_width=True
        )
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Số dư thành viên")
            if len(financial_df) > 0:
                balance_chart = financial_df.set_index('full_name')['balance']
                st.bar_chart(balance_chart, height=300)
            else:
                st.info("Chưa có dữ liệu")
        with col2:
            st.subheader("💰 Top đóng góp")
            contrib_data = financial_df[financial_df['total_contribution'] > 0].head(5)
            if not contrib_data.empty:
                contrib_chart = contrib_data.set_index('full_name')['total_contribution']
                st.bar_chart(contrib_chart, height=300)
            else:
                st.info("Chưa có đóng góp nào")

def show_ranking_page():
    st.title("🏆 Xếp hạng thành viên")
    rankings_df = get_rankings()
    if st.session_state.user['is_admin']:
        with st.expander("➕ Thêm kết quả trận đấu"):
            with st.form("add_ranking_form"):
                members = get_approved_members()['full_name'].tolist() if not get_approved_members().empty else []
                if members:
                    selected_member = st.selectbox("👤 Chọn thành viên", members)
                    wins = st.number_input("🏆 Số trận thắng", min_value=1, max_value=10, value=1)
                    match_date = st.date_input("📅 Ngày thi đấu", value=datetime.now().date())
                else:
                    st.warning("Chưa có thành viên nào được phê duyệt")
                    selected_member = None
                location = st.text_input("📍 Địa điểm", placeholder="VD: Sân ABC")
                score = st.text_input("📊 Tỷ số", placeholder="VD: 11-8, 11-6")
                if st.form_submit_button("💾 Lưu kết quả", use_container_width=True):
                    if selected_member and location and score:
                        if add_ranking(selected_member, wins, match_date, location, score):
                            st.success(f"Đã thêm {wins} trận thắng cho {selected_member}")
                            st.experimental_rerun()
    if rankings_df.empty:
        st.info("Chưa có dữ liệu xếp hạng")
    else:
        st.subheader("📈 Bảng xếp hạng")
        for idx, (_, player) in enumerate(rankings_df.iterrows(), 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "🏅"
            st.markdown(f"""
                <div class="ranking-card">
                    <h3>{medal} #{idx} - {player['full_name']}</h3>
                    <h2>🏆 {player['total_wins']} trận thắng</h2>
                </div>
            """, unsafe_allow_html=True)
        if len(rankings_df) > 1:
            st.subheader("📊 Biểu đồ xếp hạng")
            chart_data = rankings_df.head(10).set_index('full_name')
            st.bar_chart(chart_data['total_wins'], height=400)

def show_voting_page():
    st.title("🗳️ Bình chọn buổi tập")
    vote_sessions_df = get_vote_sessions()
    if st.session_state.user['is_admin']:
        with st.expander("➕ Tạo buổi bình chọn mới"):
            with st.form("create_vote_session_form"):
                session_date = st.date_input("📅 Ngày buổi tập", value=datetime.now().date())
                description = st.text_input("📝 Mô tả")
                if st.form_submit_button("💾 Tạo", use_container_width=True):
                    if create_vote_session(session_date, description):
                        st.success("Đã tạo buổi bình chọn mới")
                        st.experimental_rerun()
    if vote_sessions_df.empty:
        st.info("Chưa có buổi bình chọn nào")
        return
    for _, session in vote_sessions_df.iterrows():
        with st.expander(f"📅 {session['session_date']} - {session['description']} ({session['vote_count']} phiếu)"):
            voted = False
            if st.session_state.user['is_admin']:
                st.info("Admin không thể bình chọn")
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id FROM votes WHERE user_id = ? AND session_date = ?
                ''', (st.session_state.user['id'], session['session_date']))
                voted = cursor.fetchone() is not None
                conn.close()
                if voted:
                    st.success("Bạn đã bình chọn cho buổi này")
                else:
                    if st.button(f"👍 Bình chọn buổi {session['session_date']}", key=f"vote_{session['id']}"):
                        if vote_for_session(st.session_state.user['id'], session['session_date']):
                            st.success("Cảm ơn bạn đã bình chọn!")
                            st.experimental_rerun()
                        else:
                            st.error("Bạn đã bình chọn rồi")
            vote_details = get_vote_details(session['session_date'])
            if not vote_details.empty:
                st.write("Danh sách thành viên đã bình chọn:")
                st.table(vote_details[['full_name', 'created_at']].rename(columns={'full_name': 'Tên', 'created_at': 'Thời gian'}))
            else:
                st.write("Chưa có thành viên nào bình chọn")

# --- Giao diện đăng nhập và đăng ký ---
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

# --- Menu điều hướng ---
def show_navigation_menu():
    menu_items = ["🏠 Trang chủ", "👥 Danh sách thành viên", "🏆 Xếp hạng", "🗳️ Bình chọn", "💰 Tài chính", "⚠️ Cảnh báo"]
    if st.session_state.user['is_admin']:
        menu_items.insert(1, "✅ Phê duyệt thành viên")
        menu_items.insert(2, "✏️ Quản lý thành viên")
    st.markdown('<div class="nav-menu">', unsafe_allow_html=True)
    cols = st.columns(len(menu_items) + 1)
    for i, item in enumerate(menu_items):
        with cols[i]:
            if st.button(item, key=f"nav_{item}", use_container_width=True):
                st.session_state.current_page = item
                st.session_state.editing_member_id = None
                st.experimental_rerun()
    with cols[-1]:
        if st.button("🚪 Đăng xuất", key="logout", use_container_width=True, type="primary"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.current_page = "🏠 Trang chủ"
            st.session_state.editing_member_id = None
            st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- Trang chủ ---
def show_home_page():
    st.title("🏠 Trang chủ")
    st.write("Chào mừng bạn đến với hệ thống quản lý câu lạc bộ Pickleball DTT!")

# --- Các trang khác (phê duyệt thành viên, quản lý thành viên, danh sách thành viên, cảnh báo) ---
# Bạn có thể thêm các hàm này tương tự như đã làm với các trang trên.

# --- Ứng dụng chính ---
def show_main_app():
    user_role = "👑 Quản trị viên" if st.session_state.user['is_admin'] else "👤 Thành viên"
    st.markdown(f"""
        <div class="user-info">
            <h3>Chào mừng, {st.session_state.user['name']}!</h3>
            <p>{user_role}</p>
        </div>
    """, unsafe_allow_html=True)
    show_navigation_menu()
    page = st.session_state.get('current_page', "🏠 Trang chủ")
    if page == "🏠 Trang chủ":
        show_home_page()
    elif page == "✅ Phê duyệt thành viên":
        # show_approval_page()  # Bạn cần định nghĩa hàm này
        st.info("Chức năng phê duyệt thành viên chưa được triển khai trong đoạn code này.")
    elif page == "✏️ Quản lý thành viên":
        # show_member_management_page()  # Bạn cần định nghĩa hàm này
        st.info("Chức năng quản lý thành viên chưa được triển khai trong đoạn code này.")
    elif page == "👥 Danh sách thành viên":
        # show_members_page()  # Bạn cần định nghĩa hàm này
        st.info("Chức năng danh sách thành viên chưa được triển khai trong đoạn code này.")
    elif page == "🏆 Xếp hạng":
        show_ranking_page()
    elif page == "🗳️ Bình chọn":
        show_voting_page()
    elif page == "💰 Tài chính":