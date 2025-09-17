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

# Custom CSS for modern, responsive design
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5a87 100%);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .nav-menu {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 30px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    .user-info {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #1f4e79;
        margin: 10px 0;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        margin: 0;
    }
    
    .stat-label {
        color: #666;
        font-size: 0.9rem;
        margin-top: 5px;
    }
    
    .member-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 3px solid #28a745;
    }
    
    .alert-card {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #f39c12;
    }
    
    .danger-card {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #dc3545;
    }
    
    .vote-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin: 15px 0;
        border: 1px solid #e9ecef;
    }
    
    .ranking-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .expense-card {
        background: #fff8e1;
        border: 1px solid #ffcc02;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #ff9800;
    }
    
    .progress-bar {
        background-color: #e9ecef;
        border-radius: 10px;
        overflow: hidden;
        margin: 5px 0;
    }
    
    .progress-fill {
        height: 25px;
        border-radius: 10px;
        text-align: center;
        line-height: 25px;
        color: white;
        font-weight: bold;
        font-size: 12px;
    }
    
    @media (max-width: 768px) {
        .stat-card {
            margin: 5px 0;
            padding: 15px;
        }
        .stat-number {
            font-size: 2rem;
        }
        .main-header {
            padding: 15px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Database initialization - ĐƠN GIẢN HÓA
def init_database():
    try:
        conn = sqlite3.connect('pickleball_club.db')
        cursor = conn.cursor()
        
        # Users table
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Rankings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                match_date TEXT,
                location TEXT,
                score TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Vote sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vote_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date TEXT,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Votes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Finances table - ĐƠN GIẢN
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS finances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                transaction_type TEXT,
                description TEXT,
                session_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default admin user
        cursor.execute('''
            INSERT OR IGNORE INTO users (full_name, email, phone, birth_date, password, is_approved, is_admin)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Administrator', 'admin@local', '0000000000', '1990-01-01', 
              hashlib.sha256('Admin@123'.encode()).hexdigest(), 1, 1))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi khởi tạo database: {str(e)}")
        return False

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(full_name, email, phone, birth_date, password):
    try:
        conn = sqlite3.connect('pickleball_club.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (full_name, email, phone, birth_date, password)
            VALUES (?, ?, ?, ?, ?)
        ''', (full_name, email, phone, str(birth_date), hash_password(password)))
        
        conn.commit()
        conn.close()
        return True, "Đăng ký thành công! Vui lòng chờ admin phê duyệt."
    except sqlite3.IntegrityError:
        return False, "Email đã tồn tại!"
    except Exception as e:
        return False, f"Lỗi đăng ký: {str(e)}"

def login_user(email, password):
    try:
        conn = sqlite3.connect('pickleball_club.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, full_name, is_approved, is_admin FROM users 
            WHERE email = ? AND password = ?
        ''', (email, hash_password(password)))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            if user[2] == 1 or user[3] == 1:  # approved or admin
                return True, {
                    'id': user[0],
                    'name': user[1],
                    'is_admin': user[3] == 1
                }
            else:
                return False, "Tài khoản chưa được phê duyệt!"
        return False, "Email hoặc mật khẩu không đúng!"
    except Exception as e:
        return False, f"Lỗi đăng nhập: {str(e)}"

# Database helper functions - SỬA LẠI ĐỂ TRÁNH LỖI
def safe_query(query, params=None):
    """Thực hiện query một cách an toàn"""
    try:
        conn = sqlite3.connect('pickleball_club.db')
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Lỗi database: {str(e)}")
        return pd.DataFrame()

def get_pending_members():
    query = '''
        SELECT id, full_name, email, phone, birth_date, created_at
        FROM users 
        WHERE is_approved = 0 AND is_admin = 0
        ORDER BY created_at DESC
    '''
    return safe_query(query)

def get_approved_members():
    query = '''
        SELECT id, full_name, phone, birth_date
        FROM users 
        WHERE is_approved = 1 AND is_admin = 0
        ORDER BY full_name
    '''
    return safe_query(query)

def approve_member(user_id, admin_name):
    try:
        conn = sqlite3.connect('pickleball_club.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_approved = 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi phê duyệt: {str(e)}")
        return False

def reject_member(user_id):
    try:
        conn = sqlite3.connect('pickleball_club.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi từ chối: {str(e)}")
        return False

def get_rankings():
    query = '''
        SELECT u.full_name, COUNT(r.id) as total_wins
        FROM users u
        LEFT JOIN rankings r ON u.id = r.user_id
        WHERE u.is_approved = 1 AND u.is_admin = 0
        GROUP BY u.id, u.full_name
        ORDER BY total_wins DESC
    '''
    return safe_query(query)

def add_ranking(user_name, wins, match_date, location, score):
    try:
        conn = sqlite3.connect('pickleball_club.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE full_name = ? AND is_approved = 1 AND is_admin = 0', (user_name,))
        user = cursor.fetchone()
        
        if user:
            for _ in range(wins):
                cursor.execute('''
                    INSERT INTO rankings (user_id, match_date, location, score)
                    VALUES (?, ?, ?, ?)
                ''', (user[0], str(match_date), location, score))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi thêm ranking: {str(e)}")
        return False

def get_vote_sessions():
    query = '''
        SELECT vs.id, vs.session_date, vs.description, 
               (SELECT COUNT(*) FROM votes v JOIN users u ON v.user_id = u.id 
                WHERE v.session_date = vs.session_date AND u.is_admin = 0) as vote_count
        FROM vote_sessions vs
        ORDER BY vs.session_date DESC
    '''
    return safe_query(query)

def create_vote_session(session_date, description):
    try:
        conn = sqlite3.connect('pickleball_club.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO vote_sessions (session_date, description)
            VALUES (?, ?)
        ''', (str(session_date), description))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi tạo vote session: {str(e)}")
        return False

def vote_for_session(user_id, session_date):
    try:
        conn = sqlite3.connect('pickleball_club.db')
        cursor = conn.cursor()
        
        # Check if already voted
        cursor.execute('SELECT id FROM votes WHERE user_id = ? AND session_date = ?', (user_id, str(session_date)))
        
        if not cursor.fetchone():
            cursor.execute('INSERT INTO votes (user_id, session_date) VALUES (?, ?)', (user_id, str(session_date)))
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
    query = '''
        SELECT u.full_name, v.created_at
        FROM votes v
        JOIN users u ON v.user_id = u.id
        WHERE v.session_date = ? AND u.is_admin = 0
        ORDER BY v.created_at
    '''
    return safe_query(query, [str(session_date)])

def add_contribution(user_name, amount):
    try:
        conn = sqlite3.connect('pickleball_club.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE full_name = ? AND is_approved = 1 AND is_admin = 0', (user_name,))
        user = cursor.fetchone()
        
        if user:
            cursor.execute('''
                INSERT INTO finances (user_id, amount, transaction_type, description)
                VALUES (?, ?, ?, ?)
            ''', (user[0], amount, 'contribution', 'Đóng quỹ'))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi thêm đóng góp: {str(e)}")
        return False

def get_vote_sessions_for_expense():
    query = '''
        SELECT vs.session_date, vs.description, 
               (SELECT COUNT(*) FROM votes v JOIN users u ON v.user_id = u.id 
                WHERE v.session_date = vs.session_date AND u.is_admin = 0) as vote_count
        FROM vote_sessions vs
        WHERE (SELECT COUNT(*) FROM votes v JOIN users u ON v.user_id = u.id 
               WHERE v.session_date = vs.session_date AND u.is_admin = 0) > 0
        ORDER BY vs.session_date DESC
    '''
    return safe_query(query)

def add_expense(session_date, court_fee, water_fee, other_fee, description):
    try:
        conn = sqlite3.connect('pickleball_club.db')
        cursor = conn.cursor()
        
        total_fee = court_fee + water_fee + other_fee
        
        # Get voters (only members, not admin)
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
                    INSERT INTO finances (user_id, amount, transaction_type, description, session_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (voter[0], -cost_per_person, 'expense', description, str(session_date)))
        
        conn.commit()
        conn.close()
        return True, f"Đã chia {total_fee:,} VNĐ cho {len(voters)} thành viên ({cost_per_person:,} VNĐ/người)"
    except Exception as e:
        st.error(f"Lỗi thêm chi phí: {str(e)}")
        return False, str(e)

def get_financial_summary():
    query = '''
        SELECT 
            u.full_name,
            COALESCE(SUM(CASE WHEN f.transaction_type = 'contribution' THEN f.amount ELSE 0 END), 0) as total_contribution,
            COUNT(CASE WHEN f.transaction_type = 'expense' THEN 1 END) as sessions_attended,
            COALESCE(SUM(CASE WHEN f.transaction_type = 'expense' THEN f.amount ELSE 0 END), 0) as total_expenses,
            COALESCE(SUM(f.amount), 0) as balance
        FROM users u
        LEFT JOIN finances f ON u.id = f.user_id
        WHERE u.is_approved = 1 AND u.is_admin = 0
        GROUP BY u.id, u.full_name
        ORDER BY balance DESC
    '''
    return safe_query(query)

def get_expense_history():
    query = '''
        SELECT 
            session_date,
            description,
            COUNT(*) as participants_count,
            SUM(-amount) as total_cost,
            (-amount) as cost_per_person,
            created_at
        FROM finances
        WHERE transaction_type = 'expense'
        GROUP BY session_date, description, amount
        ORDER BY session_date DESC
    '''
    return safe_query(query)

def get_alerts():
    alerts = []
    try:
        # Low balance alert
        low_balance_query = '''
            SELECT u.full_name, COALESCE(SUM(f.amount), 0) as balance
            FROM users u
            LEFT JOIN finances f ON u.id = f.user_id
            WHERE u.is_approved = 1 AND u.is_admin = 0
            GROUP BY u.id, u.full_name
            HAVING balance < 100000
        '''
        low_balance_df = safe_query(low_balance_query)
        
        for _, user in low_balance_df.iterrows():
            alerts.append(f"⚠️ {user['full_name']} có số dư thấp: {user['balance']:,} VNĐ")
        
        # Low voting activity
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        low_vote_query = '''
            SELECT u.full_name, COUNT(v.id) as vote_count
            FROM users u
            LEFT JOIN votes v ON u.id = v.user_id
            WHERE u.is_approved = 1 AND u.is_admin = 0
            GROUP BY u.id, u.full_name
            HAVING vote_count < 3
        '''
        low_vote_df = safe_query(low_vote_query)
        
        for _, user in low_vote_df.iterrows():
            alerts.append(f"📊 {user['full_name']} vote ít trong 30 ngày qua: {user['vote_count']} lần")
            
    except Exception as e:
        st.error(f"Lỗi lấy alerts: {str(e)}")
    
    return alerts

# Custom chart functions
def create_horizontal_bar_chart(data, title):
    if data.empty:
        return f"<p>Chưa có dữ liệu cho {title}</p>"
    
    max_value = data.iloc[:, 1].max() if len(data) > 0 else 1
    
    chart_html = f"<h4>{title}</h4>"
    for _, row in data.head(5).iterrows():
        name = row.iloc[0]
        value = row.iloc[1]
        percentage = (value / max_value) * 100 if max_value > 0 else 0
        
        chart_html += f"""
        <div style="margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span><strong>{name}</strong></span>
                <span>{value}</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {percentage}%; background: linear-gradient(90deg, #1f4e79, #2d5a87);">
                    {percentage:.1f}%
                </div>
            </div>
        </div>
        """
    return chart_html

def create_balance_chart(data):
    if data.empty:
        return "<p>Chưa có dữ liệu tài chính</p>"
    
    max_abs = max(abs(data['balance'].min()), abs(data['balance'].max())) if len(data) > 0 else 1
    
    chart_html = "<h4>📊 Số dư thành viên</h4>"
    for _, row in data.iterrows():
        name = row['full_name']
        balance = row['balance']
        percentage = abs(balance) / max_abs * 100 if max_abs > 0 else 0
        color = "#28a745" if balance >= 0 else "#dc3545"
        
        chart_html += f"""
        <div style="margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span><strong>{name}</strong></span>
                <span style="color: {color};">{balance:,} VNĐ</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {percentage}%; background: {color};">
                    {percentage:.1f}%
                </div>
            </div>
        </div>
        """
    return chart_html

# Initialize database
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = init_database()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Trang chủ"

# Main app
def main():
    if not st.session_state.db_initialized:
        st.error("Không thể khởi tạo database. Vui lòng thử lại!")
        return
        
    st.markdown("""
        <div class="main-header">
            <h1>🏓 DTT PICKLEBALL CLUB</h1>
            <p>Hệ thống quản lý câu lạc bộ Pickleball chuyên nghiệp</p>
        </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        show_auth_page()
    else:
        show_main_app()

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
                        st.rerun()
                    else:
                        st.error(result)
                else:
                    st.error("Vui lòng nhập đầy đủ thông tin!")
        
        st.info("💡 Tài khoản admin mặc định: admin@local / Admin@123")
    
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

def show_main_app():
    user_role = "👑 Quản trị viên" if st.session_state.user['is_admin'] else "👤 Thành viên"
    
    st.markdown(f"""
        <div class="user-info">
            <h3>Chào mừng, {st.session_state.user['name']}!</h3>
            <p>{user_role}</p>
        </div>
    """, unsafe_allow_html=True)
    
    show_navigation_menu()
    
    # Main content routing
    if st.session_state.current_page == "🏠 Trang chủ":
        show_home_page()
    elif st.session_state.current_page == "✅ Phê duyệt thành viên":
        show_approval_page()
    elif st.session_state.current_page == "👥 Danh sách thành viên":
        show_members_page()
    elif st.session_state.current_page == "🏆 Xếp hạng":
        show_ranking_page()
    elif st.session_state.current_page == "🗳️ Bình chọn":
        show_voting_page()
    elif st.session_state.current_page == "💰 Tài chính":
        show_finance_page()
    elif st.session_state.current_page == "⚠️ Cảnh báo":
        show_alerts_page()

def show_navigation_menu():
    menu_items = ["🏠 Trang chủ", "👥 Danh sách thành viên", "🏆 Xếp hạng", "🗳️ Bình chọn", "💰 Tài chính", "⚠️ Cảnh báo"]
    
    if st.session_state.user['is_admin']:
        menu_items.insert(1, "✅ Phê duyệt thành viên")
    
    st.markdown('<div class="nav-menu">', unsafe_allow_html=True)
    
    cols = st.columns(len(menu_items) + 1)
    
    for i, item in enumerate(menu_items):
        with cols[i]:
            if st.button(item, key=f"nav_{item}", use_container_width=True):
                st.session_state.current_page = item
                st.rerun()
    
    with cols[-1]:
        if st.button("🚪 Đăng xuất", key="logout", use_container_width=True, type="primary"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.current_page = "🏠 Trang chủ"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_home_page():
    st.title("📊 Trang chủ - Tổng quan")
    
    members_df = get_approved_members()
    rankings_df = get_rankings()
    financial_df = get_financial_summary()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(members_df)}</div>
                <div class="stat-label">👥 Tổng số thành viên</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        top_wins = rankings_df.iloc[0]['total_wins'] if not rankings_df.empty else 0
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{top_wins}</div>
                <div class="stat-label">🏆 Nhiều trận thắng nhất</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_balance = financial_df['balance'].sum() if not financial_df.empty else 0
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{total_balance:,}</div>
                <div class="stat-label">💰 Tổng quỹ (VNĐ)</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if not rankings_df.empty:
            chart_html = create_horizontal_bar_chart(rankings_df, "🏆 Top 5 thành viên xuất sắc")
            st.markdown(chart_html, unsafe_allow_html=True)
        else:
            st.info("Chưa có dữ liệu ranking")
    
    with col2:
        if not financial_df.empty and financial_df['total_contribution'].sum() > 0:
            contrib_data = financial_df[financial_df['total_contribution'] > 0].head(5)
            if not contrib_data.empty:
                chart_html = create_horizontal_bar_chart(
                    contrib_data[['full_name', 'total_contribution']], 
                    "💰 Top 5 thành viên đóng góp nhiều"
                )
                st.markdown(chart_html, unsafe_allow_html=True)
            else:
                st.info("Chưa có đóng góp nào")
        else:
            st.info("Chưa có dữ liệu tài chính")

def show_approval_page():
    if not st.session_state.user['is_admin']:
        st.error("Chỉ admin mới có quyền truy cập trang này!")
        return
    
    st.title("✅ Phê duyệt thành viên")
    
    pending_members = get_pending_members()
    
    if pending_members.empty:
        st.success("🎉 Không có thành viên nào cần phê duyệt!")
    else:
        st.subheader(f"📋 Có {len(pending_members)} thành viên chờ phê duyệt")
        
        for _, member in pending_members.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    st.markdown(f"""
                        <div class="member-card">
                            <strong>👤 {member['full_name']}</strong><br>
                            📧 {member['email']}<br>
                            📱 {member['phone']}<br>
                            📅 {member['birth_date']}
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.info(f"📅 Đăng ký: {member['created_at']}")
                
                with col3:
                    if st.button("✅ Phê duyệt", key=f"approve_{member['id']}", use_container_width=True):
                        if approve_member(member['id'], st.session_state.user['name']):
                            st.success(f"Đã phê duyệt {member['full_name']}")
                            st.rerun()
                
                with col4:
                    if st.button("❌ Từ chối", key=f"reject_{member['id']}", use_container_width=True):
                        if reject_member(member['id']):
                            st.warning(f"Đã từ chối {member['full_name']}")
                            st.rerun()
                
                st.markdown("---")

def show_members_page():
    st.title("👥 Danh sách thành viên")
    
    members_df = get_approved_members()
    
    if members_df.empty:
        st.info("Chưa có thành viên nào được phê duyệt")
    else:
        st.subheader(f"📊 Tổng số: {len(members_df)} thành viên")
        
        search_term = st.text_input("🔍 Tìm kiếm thành viên", placeholder="Nhập tên để tìm kiếm...")
        
        if search_term:
            members_df = members_df[members_df['full_name'].str.contains(search_term, case=False, na=False)]
        
        if not members_df.empty:
            display_df = members_df.copy()
            display_df.index = range(1, len(display_df) + 1)
            
            st.dataframe(
                display_df.rename(columns={
                    'full_name': 'Họ và tên',
                    'phone': 'Số điện thoại',
                    'birth_date': 'Ngày sinh'
                })[['Họ và tên', 'Số điện thoại', 'Ngày sinh']],
                use_container_width=True
            )

def show_ranking_page():
    st.title("🏆 Xếp hạng thành viên")
    
    rankings_df = get_rankings()
    
    if st.session_state.user['is_admin']:
        with st.expander("➕ Thêm kết quả trận đấu"):
            with st.form("add_ranking_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    members = get_approved_members()['full_name'].tolist()
                    if members:
                        selected_member = st.selectbox("👤 Chọn thành viên", members)
                        wins = st.number_input("🏆 Số trận thắng", min_value=1, max_value=10, value=1)
                        match_date = st.date_input("📅 Ngày thi đấu", value=datetime.now().date())
                
                with col2:
                    location = st.text_input("📍 Địa điểm", placeholder="VD: Sân ABC")
                    score = st.text_input("📊 Tỷ số", placeholder="VD: 11-8, 11-6")
                
                if st.form_submit_button("💾 Lưu kết quả", use_container_width=True):
                    if selected_member and location and score:
                        if add_ranking(selected_member, wins, match_date, location, score):
                            st.success(f"Đã thêm {wins} trận thắng cho {selected_member}")
                            st.rerun()
    
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

def show_voting_page():
    st.title("🗳️ Bình chọn tham gia")
    
    if st.session_state.user['is_admin']:
        with st.expander("➕ Tạo phiên bình chọn mới"):
            with st.form("create_vote_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    session_date = st.date_input("📅 Ngày chơi", min_value=datetime.now().date())
                
                with col2:
                    description = st.text_input("📝 Mô tả", placeholder="VD: Giao lưu cuối tuần")
                
                if st.form_submit_button("🗳️ Tạo phiên bình chọn", use_container_width=True):
                    if description:
                        if create_vote_session(session_date, description):
                            st.success("Đã tạo phiên bình chọn mới!")
                            st.rerun()
    
    vote_sessions = get_vote_sessions()
    
    if vote_sessions.empty:
        st.info("Chưa có phiên bình chọn nào")
    else:
        st.subheader("📋 Các phiên bình chọn")
        
        for _, session in vote_sessions.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"""
                        <div class="vote-card">
                            <h4>📅 {session['session_date']}</h4>
                            <p>📝 {session['description']}</p>
                            <p>👥 <strong>{session['vote_count']}</strong> thành viên tham gia</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if not st.session_state.user['is_admin']:
                        if st.button("🗳️ Vote", key=f"vote_{session['id']}", use_container_width=True):
                            success = vote_for_session(st.session_state.user['id'], session['session_date'])
                            if success:
                                st.success("Đã vote thành công!")
                                st.rerun()
                            else:
                                st.warning("Bạn đã vote cho phiên này!")
                    else:
                        st.info("Admin không thể vote")
                
                with col3:
                    if st.button("👁️ Chi tiết", key=f"detail_{session['id']}", use_container_width=True):
                        vote_details = get_vote_details(session['session_date'])
                        
                        with st.expander(f"Chi tiết phiên {session['session_date']}", expanded=True):
                            if not vote_details.empty:
                                for _, voter in vote_details.iterrows():
                                    st.markdown(f"""
                                        <div class="member-card">
                                            👤 <strong>{voter['full_name']}</strong><br>
                                            🕒 {voter['created_at']}
                                        </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("Chưa có thành viên nào vote cho phiên này")

def show_finance_page():
    st.title("💰 Quản lý tài chính")
    
    if st.session_state.user['is_admin']:
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("➕ Thêm đóng góp"):
                with st.form("add_contribution_form"):
                    members = get_approved_members()['full_name'].tolist()
                    if members:
                        member_name = st.selectbox("👤 Thành viên", members)
                        amount = st.number_input("💵 Số tiền (VNĐ)", min_value=10000, step=10000)
                        
                        if st.form_submit_button("💾 Lưu", use_container_width=True):
                            if add_contribution(member_name, amount):
                                st.success(f"Đã thêm {amount:,} VNĐ cho {member_name}")
                                st.rerun()
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
                                    st.rerun()
                else:
                    st.warning("Chưa có buổi tập nào có vote")
    
    # Financial summary
    financial_df = get_financial_summary()
    
    if not financial_df.empty:
        st.subheader("📊 Tổng quan tài chính")
        
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
        
        st.subheader("📋 Chi tiết tài chính")
        
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

def show_alerts_page():
    st.title("⚠️ Cảnh báo hệ thống")
    
    alerts = get_alerts()
    
    if not alerts:
        st.success("🎉 Không có cảnh báo nào!")
    else:
        st.subheader(f"🚨 Có {len(alerts)} cảnh báo cần chú ý")
        
        for alert in alerts:
            if "số dư thấp" in alert:
                st.markdown(f'<div class="danger-card">{alert}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-card">{alert}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()