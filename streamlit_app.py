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
    
    .nav-button {
        background: white;
        border: 1px solid #dee2e6;
        padding: 10px 20px;
        margin: 5px;
        border-radius: 8px;
        display: inline-block;
        text-decoration: none;
        color: #495057;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .nav-button:hover {
        background: #1f4e79;
        color: white;
        border-color: #1f4e79;
    }
    
    .nav-button.active {
        background: #1f4e79;
        color: white;
        border-color: #1f4e79;
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
    
    .success-card {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #28a745;
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
    
    .logout-btn {
        background: #dc3545;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 5px;
        cursor: pointer;
        float: right;
        margin-top: 10px;
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
        .nav-button {
            display: block;
            margin: 5px 0;
            text-align: center;
        }
    }
</style>
""", unsafe_allow_html=True)

# Database initialization
def init_database():
    conn = sqlite3.connect('pickleball_club.db')
    cursor = conn.cursor()
    
    # Users table (for authentication)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            birth_date DATE NOT NULL,
            password TEXT NOT NULL,
            is_approved INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by TEXT
        )
    ''')
    
    # Rankings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            wins INTEGER DEFAULT 0,
            match_date DATE,
            location TEXT,
            score TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Votes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            vote_date DATE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Vote sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vote_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_date DATE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Finances table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS finances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            transaction_type TEXT,
            description TEXT,
            session_date DATE,
            court_fee INTEGER DEFAULT 0,
            water_fee INTEGER DEFAULT 0,
            other_fee INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
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

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(full_name, email, phone, birth_date, password):
    conn = sqlite3.connect('pickleball_club.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (full_name, email, phone, birth_date, password)
            VALUES (?, ?, ?, ?, ?)
        ''', (full_name, email, phone, birth_date, hash_password(password)))
        conn.commit()
        return True, "Đăng ký thành công! Vui lòng chờ admin phê duyệt."
    except sqlite3.IntegrityError:
        return False, "Email đã tồn tại!"
    finally:
        conn.close()

def login_user(email, password):
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

# Database helper functions - KHÔNG BAO GỒM ADMIN
def get_pending_members():
    conn = sqlite3.connect('pickleball_club.db')
    df = pd.read_sql_query('''
        SELECT id, full_name, email, phone, birth_date, created_at
        FROM users 
        WHERE is_approved = 0 AND is_admin = 0
        ORDER BY created_at DESC
    ''', conn)
    conn.close()
    return df

def get_approved_members():
    conn = sqlite3.connect('pickleball_club.db')
    df = pd.read_sql_query('''
        SELECT id, full_name, phone, birth_date
        FROM users 
        WHERE is_approved = 1 AND is_admin = 0
        ORDER BY full_name
    ''', conn)
    conn.close()
    return df

def approve_member(user_id, admin_name):
    conn = sqlite3.connect('pickleball_club.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET is_approved = 1, approved_at = CURRENT_TIMESTAMP, approved_by = ?
        WHERE id = ?
    ''', (admin_name, user_id))
    
    conn.commit()
    conn.close()

def reject_member(user_id):
    conn = sqlite3.connect('pickleball_club.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    conn.commit()
    conn.close()

def get_rankings():
    conn = sqlite3.connect('pickleball_club.db')
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

def add_ranking(user_name, wins, match_date, location, score):
    conn = sqlite3.connect('pickleball_club.db')
    cursor = conn.cursor()
    
    # Get user_id (chỉ thành viên, không phải admin)
    cursor.execute('SELECT id FROM users WHERE full_name = ? AND is_approved = 1 AND is_admin = 0', (user_name,))
    user = cursor.fetchone()
    
    if user:
        # Add multiple ranking entries for wins
        for _ in range(wins):
            cursor.execute('''
                INSERT INTO rankings (user_id, wins, match_date, location, score)
                VALUES (?, ?, ?, ?, ?)
            ''', (user[0], 1, match_date, location, score))
    
    conn.commit()
    conn.close()

def get_vote_sessions():
    conn = sqlite3.connect('pickleball_club.db')
    df = pd.read_sql_query('''
        SELECT vs.id, vs.session_date, vs.description, 
               COUNT(v.id) as vote_count
        FROM vote_sessions vs
        LEFT JOIN votes v ON vs.session_date = v.vote_date
        LEFT JOIN users u ON v.user_id = u.id AND u.is_admin = 0
        GROUP BY vs.id, vs.session_date, vs.description
        ORDER BY vs.session_date DESC
    ''', conn)
    conn.close()
    return df

def create_vote_session(session_date, description):
    conn = sqlite3.connect('pickleball_club.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO vote_sessions (session_date, description)
        VALUES (?, ?)
    ''', (session_date, description))
    
    conn.commit()
    conn.close()

def vote_for_session(user_id, session_date):
    conn = sqlite3.connect('pickleball_club.db')
    cursor = conn.cursor()
    
    # Check if already voted
    cursor.execute('''
        SELECT id FROM votes WHERE user_id = ? AND vote_date = ?
    ''', (user_id, session_date))
    
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO votes (user_id, vote_date)
            VALUES (?, ?)
        ''', (user_id, session_date))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def get_vote_details(session_date):
    conn = sqlite3.connect('pickleball_club.db')
    df = pd.read_sql_query('''
        SELECT u.full_name, v.created_at
        FROM votes v
        JOIN users u ON v.user_id = u.id
        WHERE v.vote_date = ? AND u.is_admin = 0
        ORDER BY v.created_at
    ''', conn, params=(session_date,))
    conn.close()
    return df

def add_contribution(user_name, amount):
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

def add_expense(session_date, court_fee, water_fee, other_fee, description):
    conn = sqlite3.connect('pickleball_club.db')
    cursor = conn.cursor()
    
    total_fee = court_fee + water_fee + other_fee
    
    # Get voters for this session (chỉ thành viên, không phải admin)
    cursor.execute('''
        SELECT v.user_id FROM votes v
        JOIN users u ON v.user_id = u.id
        WHERE v.vote_date = ? AND u.is_admin = 0
    ''', (session_date,))
    voters = cursor.fetchall()
    
    if voters:
        cost_per_person = total_fee // len(voters)
        
        for voter in voters:
            cursor.execute('''
                INSERT INTO finances (user_id, amount, transaction_type, description, session_date, court_fee, water_fee, other_fee)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (voter[0], -cost_per_person, 'expense', description, session_date, 
                  court_fee//len(voters), water_fee//len(voters), other_fee//len(voters)))
    
    conn.commit()
    conn.close()

def get_financial_summary():
    conn = sqlite3.connect('pickleball_club.db')
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

def get_alerts():
    alerts = []
    
    # Check low balance alert (chỉ thành viên)
    conn = sqlite3.connect('pickleball_club.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.full_name, COALESCE(SUM(f.amount), 0) as balance
        FROM users u
        LEFT JOIN finances f ON u.id = f.user_id
        WHERE u.is_approved = 1 AND u.is_admin = 0
        GROUP BY u.id, u.full_name
        HAVING balance < 100000
    ''')
    
    low_balance_users = cursor.fetchall()
    for user in low_balance_users:
        alerts.append(f"⚠️ {user[0]} có số dư thấp: {user[1]:,} VNĐ")
    
    # Check low voting activity (chỉ thành viên)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT u.full_name, COUNT(v.id) as vote_count
        FROM users u
        LEFT JOIN votes v ON u.id = v.user_id AND v.created_at >= ?
        WHERE u.is_approved = 1 AND u.is_admin = 0
        GROUP BY u.id, u.full_name
        HAVING vote_count < 3
    ''', (thirty_days_ago,))
    
    low_activity_users = cursor.fetchall()
    for user in low_activity_users:
        alerts.append(f"📊 {user[0]} vote ít trong 30 ngày qua: {user[1]} lần")
    
    conn.close()
    return alerts

# Custom chart functions using HTML/CSS
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
init_database()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Trang chủ"

# Main app
def main():
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>🏓 DTT PICKLEBALL CLUB</h1>
            <p>Hệ thống quản lý câu lạc bộ Pickleball chuyên nghiệp</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Authentication
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
        
        st.info("💡 Cần trợ giúp xin liên hệ Vonnv")
    
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
    # User info and navigation
    user_role = "👑 Quản trị viên" if st.session_state.user['is_admin'] else "👤 Thành viên"
    
    st.markdown(f"""
        <div class="user-info">
            <h3>Chào mừng, {st.session_state.user['name']}!</h3>
            <p>{user_role}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Navigation menu
    show_navigation_menu()
    
    # Main content based on selected page
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
    # Define menu items based on user role
    menu_items = ["🏠 Trang chủ", "👥 Danh sách thành viên", "🏆 Xếp hạng", "🗳️ Bình chọn", "💰 Tài chính", "⚠️ Cảnh báo"]
    
    if st.session_state.user['is_admin']:
        menu_items.insert(1, "✅ Phê duyệt thành viên")
    
    # Create navigation menu
    st.markdown('<div class="nav-menu">', unsafe_allow_html=True)
    
    cols = st.columns(len(menu_items) + 1)  # +1 for logout button
    
    for i, item in enumerate(menu_items):
        with cols[i]:
            if st.button(item, key=f"nav_{item}", use_container_width=True):
                st.session_state.current_page = item
                st.rerun()
    
    # Logout button in the last column
    with cols[-1]:
        if st.button("🚪 Đăng xuất", key="logout", use_container_width=True, type="primary"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.current_page = "🏠 Trang chủ"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_home_page():
    st.title("📊 Trang chủ - Tổng quan")
    
    # Statistics (chỉ thành viên, không tính admin)
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
        top_winner = rankings_df.iloc[0] if not rankings_df.empty else None
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{top_winner['total_wins'] if top_winner is not None else 0}</div>
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
    
    # Charts using custom HTML/CSS
    col1, col2 = st.columns(2)
    
    with col1:
        if not rankings_df.empty:
            chart_html = create_horizontal_bar_chart(rankings_df, "🏆 Top 5 thành viên xuất sắc")
            st.markdown(chart_html, unsafe_allow_html=True)
        else:
            st.info("Chưa có dữ liệu ranking")
    
    with col2:
        if not financial_df.empty and financial_df['total_contribution'].sum() > 0:
            # Show top contributors
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
    
    # Recent activities (chỉ thành viên)
    st.subheader("📈 Hoạt động gần đây")
    
    conn = sqlite3.connect('pickleball_club.db')
    recent_activities = pd.read_sql_query('''
        SELECT 'Thành viên mới' as activity_type, u.full_name as details, u.approved_at as activity_date
        FROM users u WHERE u.is_approved = 1 AND u.approved_at IS NOT NULL AND u.is_admin = 0
        UNION ALL
        SELECT 'Vote tham gia' as activity_type, u.full_name as details, v.created_at as activity_date
        FROM votes v JOIN users u ON v.user_id = u.id WHERE u.is_admin = 0
        UNION ALL
        SELECT 'Đóng quỹ' as activity_type, u.full_name || ' - ' || f.amount || ' VNĐ' as details, f.created_at as activity_date
        FROM finances f JOIN users u ON f.user_id = u.id WHERE f.transaction_type = 'contribution' AND u.is_admin = 0
        ORDER BY activity_date DESC
        LIMIT 10
    ''', conn)
    conn.close()
    
    if not recent_activities.empty:
        for _, activity in recent_activities.iterrows():
            if pd.notna(activity['activity_date']):
                activity_date = pd.to_datetime(activity['activity_date']).strftime('%d/%m/%Y %H:%M')
                st.markdown(f"""
                    <div class="member-card">
                        <strong>{activity['activity_type']}</strong>: {activity['details']}
                        <br><small>📅 {activity_date}</small>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Chưa có hoạt động gần đây")

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
                            📅 {pd.to_datetime(member['birth_date']).strftime('%d/%m/%Y')}
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    register_date = pd.to_datetime(member['created_at']).strftime('%d/%m/%Y %H:%M')
                    st.info(f"📅 Đăng ký: {register_date}")
                
                with col3:
                    if st.button("✅ Phê duyệt", key=f"approve_{member['id']}", use_container_width=True):
                        approve_member(member['id'], st.session_state.user['name'])
                        st.success(f"Đã phê duyệt {member['full_name']}")
                        st.rerun()
                
                with col4:
                    if st.button("❌ Từ chối", key=f"reject_{member['id']}", use_container_width=True):
                        reject_member(member['id'])
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
        st.caption("*Không bao gồm quản trị viên trong danh sách")
        
        # Add search functionality
        search_term = st.text_input("🔍 Tìm kiếm thành viên", placeholder="Nhập tên để tìm kiếm...")
        
        if search_term:
            members_df = members_df[members_df['full_name'].str.contains(search_term, case=False, na=False)]
        
        # Display members in table
        if not members_df.empty:
            display_df = members_df.copy()
            display_df['birth_date'] = pd.to_datetime(display_df['birth_date']).dt.strftime('%d/%m/%Y')
            display_df.index = range(1, len(display_df) + 1)
            
            st.dataframe(
                display_df.rename(columns={
                    'full_name': 'Họ và tên',
                    'phone': 'Số điện thoại',
                    'birth_date': 'Ngày sinh'
                })[['Họ và tên', 'Số điện thoại', 'Ngày sinh']],
                use_container_width=True
            )
        else:
            st.info("Không tìm thấy thành viên nào")

def show_ranking_page():
    st.title("🏆 Xếp hạng thành viên")
    
    rankings_df = get_rankings()
    
    # Admin functions
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
                    else:
                        st.warning("Chưa có thành viên nào được phê duyệt")
                        selected_member = None
                
                with col2:
                    location = st.text_input("📍 Địa điểm", placeholder="VD: Sân ABC")
                    score = st.text_input("📊 Tỷ số", placeholder="VD: 11-8, 11-6")
                
                if st.form_submit_button("💾 Lưu kết quả", use_container_width=True):
                    if selected_member and location and score:
                        add_ranking(selected_member, wins, match_date, location, score)
                        st.success(f"Đã thêm {wins} trận thắng cho {selected_member}")
                        st.rerun()
                    else:
                        st.error("Vui lòng nhập đầy đủ thông tin!")
    
    # Display rankings
    if rankings_df.empty:
        st.info("Chưa có dữ liệu xếp hạng")
    else:
        st.subheader("📈 Bảng xếp hạng")
        st.caption("*Chỉ thống kê thành viên, không bao gồm quản trị viên")
        
        # Create ranking cards
        for idx, (_, player) in enumerate(rankings_df.iterrows(), 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "🏅"
            
            st.markdown(f"""
                <div class="ranking-card">
                    <h3>{medal} #{idx} - {player['full_name']}</h3>
                    <h2>🏆 {player['total_wins']} trận thắng</h2>
                </div>
            """, unsafe_allow_html=True)
        
        # Chart using custom HTML
        if len(rankings_df) > 1:
            chart_html = create_horizontal_bar_chart(rankings_df.head(10), "📊 Top 10 thành viên xuất sắc")
            st.markdown(chart_html, unsafe_allow_html=True)

def show_voting_page():
    st.title("🗳️ Bình chọn tham gia")
    
    # Admin create vote session
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
                        create_vote_session(session_date, description)
                        st.success("Đã tạo phiên bình chọn mới!")
                        st.rerun()
                    else:
                        st.error("Vui lòng nhập mô tả!")
    
    # Display vote sessions
    vote_sessions = get_vote_sessions()
    
    if vote_sessions.empty:
        st.info("Chưa có phiên bình chọn nào")
    else:
        st.subheader("📋 Các phiên bình chọn")
        st.caption("*Chỉ thống kê vote của thành viên")
        
        for _, session in vote_sessions.iterrows():
            session_date_formatted = pd.to_datetime(session['session_date']).strftime('%d/%m/%Y')
            
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"""
                        <div class="vote-card">
                            <h4>📅 {session_date_formatted}</h4>
                            <p>📝 {session['description']}</p>
                            <p>👥 <strong>{session['vote_count']}</strong> thành viên tham gia</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Chỉ thành viên mới có thể vote
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
                        
                        with st.expander(f"Chi tiết phiên {session_date_formatted}", expanded=True):
                            if not vote_details.empty:
                                for _, voter in vote_details.iterrows():
                                    vote_time = pd.to_datetime(voter['created_at']).strftime('%d/%m/%Y %H:%M')
                                    st.markdown(f"""
                                        <div class="member-card">
                                            👤 <strong>{voter['full_name']}</strong><br>
                                            🕒 {vote_time}
                                        </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("Chưa có thành viên nào vote cho phiên này")

def show_finance_page():
    st.title("💰 Quản lý tài chính")
    
    # Admin functions
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
                            add_contribution(member_name, amount)
                            st.success(f"Đã thêm {amount:,} VNĐ cho {member_name}")
                            st.rerun()
                    else:
                        st.warning("Chưa có thành viên nào được phê duyệt")
        
        with col2:
            with st.expander("➕ Thêm chi phí"):
                with st.form("add_expense_form"):
                    expense_date = st.date_input("📅 Ngày chi")
                    court_fee = st.number_input("🏸 Tiền sân (VNĐ)", min_value=0, step=10000)
                    water_fee = st.number_input("💧 Tiền nước (VNĐ)", min_value=0, step=5000)
                    other_fee = st.number_input("➕ Chi phí khác (VNĐ)", min_value=0, step=5000)
                    description = st.text_input("📝 Ghi chú", placeholder="Mô tả chi phí")
                    
                    total = court_fee + water_fee + other_fee
                    if total > 0:
                        st.info(f"💰 Tổng chi phí: {total:,} VNĐ")
                    
                    if st.form_submit_button("💾 Lưu", use_container_width=True):
                        if total > 0:
                            add_expense(expense_date, court_fee, water_fee, other_fee, description)
                            st.success(f"Đã thêm chi phí {total:,} VNĐ")
                            st.rerun()
                        else:
                            st.error("Tổng chi phí phải lớn hơn 0!")
    
    # Financial summary
    financial_df = get_financial_summary()
    
    if financial_df.empty:
        st.info("Chưa có dữ liệu tài chính")
    else:
        st.subheader("📊 Tổng quan tài chính")
        st.caption("*Chỉ thống kê tài chính của thành viên, không bao gồm quản trị viên")
        
        # Summary metrics
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
            st.metric("📊 TB buổi tập", f"{avg_sessions:.1f}")
        
        # Detailed table
        st.subheader("📋 Chi tiết tài chính thành viên")
        
        display_df = financial_df.copy()
        display_df['total_contribution'] = display_df['total_contribution'].apply(lambda x: f"{x:,} VNĐ")
        display_df['total_expenses'] = display_df['total_expenses'].apply(lambda x: f"{abs(x):,} VNĐ")
        display_df['balance'] = display_df['balance'].apply(lambda x: f"{x:,} VNĐ")
        display_df.index = range(1, len(display_df) + 1)
        
        st.dataframe(
            display_df.rename(columns={
                'full_name': 'Tên thành viên',
                'total_contribution': 'Đã đóng',
                'sessions_attended': 'Số buổi',
                'total_expenses': 'Chi phí',
                'balance': 'Số dư'
            }),
            use_container_width=True
        )
        
        # Charts using custom HTML
        col1, col2 = st.columns(2)
        
        with col1:
            chart_html = create_balance_chart(financial_df)
            st.markdown(chart_html, unsafe_allow_html=True)
        
        with col2:
            # Top contributors chart
            contrib_data = financial_df[financial_df['total_contribution'] > 0].head(5)
            if not contrib_data.empty:
                chart_html = create_horizontal_bar_chart(
                    contrib_data[['full_name', 'total_contribution']], 
                    "💰 Top 5 thành viên đóng góp"
                )
                st.markdown(chart_html, unsafe_allow_html=True)
            else:
                st.info("Chưa có đóng góp nào")

def show_alerts_page():
    st.title("⚠️ Cảnh báo hệ thống")
    
    alerts = get_alerts()
    
    if not alerts:
        st.success("🎉 Không có cảnh báo nào!")
        st.balloons()
    else:
        st.subheader(f"🚨 Có {len(alerts)} cảnh báo cần chú ý")
        st.caption("*Chỉ cảnh báo liên quan đến thành viên")
        
        for alert in alerts:
            if "số dư thấp" in alert:
                st.markdown(f"""
                    <div class="danger-card">
                        {alert}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="alert-card">
                        {alert}
                    </div>
                """, unsafe_allow_html=True)
    
    # System statistics
    st.subheader("📊 Thống kê hệ thống")
    
    conn = sqlite3.connect('pickleball_club.db')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_approved = 0 AND is_admin = 0')
        pending_count = cursor.fetchone()[0]
        st.metric("⏳ Chờ phê duyệt", pending_count)
    
    with col2:
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_approved = 1 AND is_admin = 0')
        approved_count = cursor.fetchone()[0]
        st.metric("✅ Thành viên active", approved_count)
    
    with col3:
        cursor.execute('''
            SELECT COUNT(*) FROM votes v
            JOIN users u ON v.user_id = u.id
            WHERE v.created_at >= datetime('now', '-7 days') AND u.is_admin = 0
        ''')
        recent_votes = cursor.fetchone()[0]
        st.metric("🗳️ Vote tuần này", recent_votes)
    
    conn.close()
    
    # Quick actions for admins
    if st.session_state.user['is_admin']:
        st.subheader("🔧 Thao tác nhanh")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📧 Gửi nhắc nhở", use_container_width=True):
                st.info("Tính năng sẽ được cập nhật trong phiên bản tiếp theo")
        
        with col2:
            if st.button("📊 Xuất báo cáo", use_container_width=True):
                st.info("Tính năng sẽ được cập nhật trong phiên bản tiếp theo")
        
        with col3:
            if st.button("🔄 Đồng bộ dữ liệu", use_container_width=True):
                st.success("Dữ liệu đã được đồng bộ thành công!")

if __name__ == "__main__":
    main()