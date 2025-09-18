import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timedelta
import os

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
    
    .pending-card {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #f39c12;
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
    
    .simple-chart {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin: 15px 0;
    }
    
    .edit-form {
        background: #e3f2fd;
        border: 1px solid #90caf9;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        border-left: 4px solid #2196f3;
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

# Database file path
DB_FILE = "pickleball_club.db"

# Database initialization
def init_database():
    """Khởi tạo database SQLite với file cố định"""
    try:
        conn = sqlite3.connect(DB_FILE)
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                approved_at TEXT,
                approved_by TEXT
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
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
                session_date TEXT,
                court_fee INTEGER DEFAULT 0,
                water_fee INTEGER DEFAULT 0,
                other_fee INTEGER DEFAULT 0,
                total_participants INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Insert default admin user if not exists
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
    """Tạo kết nối database an toàn"""
    return sqlite3.connect(DB_FILE, check_same_thread=False)

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(full_name, email, phone, birth_date, password):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (full_name, email, phone, birth_date, password, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (full_name, email, phone, str(birth_date), hash_password(password), 
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

# Database helper functions
def get_pending_members():
    """Lấy danh sách thành viên chờ phê duyệt"""
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
    """Lấy danh sách thành viên đã được phê duyệt"""
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

# THÊM CÁC HÀM QUẢN LÝ THÀNH VIÊN MỚI
def add_member_direct(full_name, email, phone, birth_date, password):
    """Admin thêm thành viên trực tiếp (đã được phê duyệt ngay)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (full_name, email, phone, birth_date, password, is_approved, created_at, approved_at, approved_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (full_name, email, phone, str(birth_date), hash_password(password), 1, 
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
    """Cập nhật thông tin thành viên"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if password:
            cursor.execute('''
                UPDATE users 
                SET full_name = ?, email = ?, phone = ?, birth_date = ?, password = ?
                WHERE id = ? AND is_admin = 0
            ''', (full_name, email, phone, str(birth_date), hash_password(password), user_id))
        else:
            cursor.execute('''
                UPDATE users 
                SET full_name = ?, email = ?, phone = ?, birth_date = ?
                WHERE id = ? AND is_admin = 0
            ''', (full_name, email, phone, str(birth_date), user_id))
        
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
    """Xóa thành viên và tất cả dữ liệu liên quan"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Xóa các dữ liệu liên quan trước
        cursor.execute('DELETE FROM rankings WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM votes WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM finances WHERE user_id = ?', (user_id,))
        
        # Xóa user (chỉ xóa thành viên, không xóa admin)
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
    """Lấy thông tin thành viên theo ID"""
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
        
        # Get user_id
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
        
        # Check if already voted
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
        st.error(f"Lỗi lấy vote details: {str(e)}")
        return pd.DataFrame()

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
    """Lấy danh sách các buổi đã có vote để chọn khi thêm chi phí"""
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
    """Thêm chi phí cho buổi tập và chia đều cho các thành viên đã vote"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        total_fee = court_fee + water_fee + other_fee
        
        # Lấy danh sách thành viên đã vote cho buổi này (chỉ thành viên, không bao gồm admin)
        cursor.execute('''
            SELECT v.user_id FROM votes v
            JOIN users u ON v.user_id = u.id
            WHERE v.session_date = ? AND u.is_admin = 0
        ''', (str(session_date),))
        
        voters = cursor.fetchall()
        
        if voters:
            cost_per_person = total_fee // len(voters)  # Chi phí mỗi người
            
            # Thêm chi phí cho từng thành viên đã vote
            for voter in voters:
                cursor.execute('''
                    INSERT INTO finances (user_id, amount, transaction_type, description, session_date, 
                                        court_fee, water_fee, other_fee, total_participants, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (voter[0], -cost_per_person, 'expense', description, str(session_date), 
                      court_fee//len(voters), water_fee//len(voters), other_fee//len(voters), 
                      len(voters), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
            conn.close()
            return True, f"Đã chia {total_fee:,} VNĐ cho {len(voters)} thành viên ({cost_per_person:,} VNĐ/người)"
        else:
            conn.close()
            return False, "Không có thành viên nào vote cho buổi này"
    except Exception as e:
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
    """Lấy lịch sử chi phí theo từng buổi tập"""
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

def get_alerts():
    alerts = []
    
    try:
        conn = get_db_connection()
        
        # Check low balance alert
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
        
        # Check low voting activity
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
    except Exception as e:
        st.error(f"Lỗi lấy alerts: {str(e)}")
    
    return alerts

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
if 'editing_member_id' not in st.session_state:
    st.session_state.editing_member_id = None

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
    
    # Hiển thị thông tin database
    if os.path.exists(DB_FILE):
        file_size = os.path.getsize(DB_FILE)
        st.sidebar.success(f"💾 Database: {file_size} bytes")
    else:
        st.sidebar.warning("⚠️ Database file không tồn tại")
    
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
    elif st.session_state.current_page == "✏️ Quản lý thành viên":
        show_member_management_page()
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
        menu_items.insert(2, "✏️ Quản lý thành viên")
    
    st.markdown('<div class="nav-menu">', unsafe_allow_html=True)
    
    cols = st.columns(len(menu_items) + 1)
    
    for i, item in enumerate(menu_items):
        with cols[i]:
            if st.button(item, key=f"nav_{item}", use_container_width=True):
                st.session_state.current_page = item
                st.session_state.editing_member_id = None  # Reset editing state
                st.rerun()
    
    with cols[-1]:
        if st.button("🚪 Đăng xuất", key="logout", use_container_width=True, type="primary"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.current_page = "🏠 Trang chủ"
            st.session_state.editing_member_id = None
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
    
    # BIỂU ĐỒ SỬ DỤNG STREAMLIT NATIVE
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="simple-chart">', unsafe_allow_html=True)
        st.subheader("🏆 Top 5 thành viên xuất sắc")
        if not rankings_df.empty:
            # Tạo DataFrame cho bar chart
            top_5 = rankings_df.head(5)
            chart_data = pd.DataFrame({
                'Thành viên': top_5['full_name'],
                'Trận thắng': top_5['total_wins']
            }).set_index('Thành viên')
            
            st.bar_chart(chart_data, height=300)
        else:
            st.info("Chưa có dữ liệu ranking")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="simple-chart">', unsafe_allow_html=True)
        st.subheader("💰 Top 5 thành viên đóng góp nhiều")
        if not financial_df.empty and financial_df['total_contribution'].sum() > 0:
            contrib_data = financial_df[financial_df['total_contribution'] > 0].head(5)
            if not contrib_data.empty:
                chart_data = pd.DataFrame({
                    'Thành viên': contrib_data['full_name'],
                    'Đóng góp (VNĐ)': contrib_data['total_contribution']
                }).set_index('Thành viên')
                
                st.bar_chart(chart_data, height=300)
            else:
                st.info("Chưa có đóng góp nào")
        else:
            st.info("Chưa có dữ liệu tài chính")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Database info
    st.subheader("📊 Thông tin hệ thống")
    if os.path.exists(DB_FILE):
        file_size = os.path.getsize(DB_FILE)
        st.info(f"💾 **Database SQLite**: {DB_FILE} ({file_size} bytes) - Dữ liệu được lưu trữ persistent")
    else:
        st.warning("⚠️ Database file không tồn tại")

def show_approval_page():
    if not st.session_state.user['is_admin']:
        st.error("Chỉ admin mới có quyền truy cập trang này!")
        return
    
    st.title("✅ Phê duyệt thành viên")
    
    # Debug info
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 0')
        total_non_admin = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_approved = 0 AND is_admin = 0')
        pending_count = cursor.fetchone()[0]
        conn.close()
        
        st.info(f"🔍 Debug: {total_non_admin} users không phải admin, {pending_count} users chờ phê duyệt")
    except Exception as e:
        st.error(f"Debug error: {str(e)}")
    
    pending_members = get_pending_members()
    
    if pending_members.empty:
        st.success("🎉 Không có thành viên nào cần phê duyệt!")
        
        # Show all users for debugging
        st.subheader("🔧 Debug - Tất cả users:")
        try:
            conn = get_db_connection()
            all_users = pd.read_sql_query('SELECT full_name, email, is_approved, is_admin FROM users', conn)
            conn.close()
            st.dataframe(all_users)
        except Exception as e:
            st.error(f"Lỗi hiển thị users: {str(e)}")
    else:
        st.subheader(f"📋 Có {len(pending_members)} thành viên chờ phê duyệt")
        
        for _, member in pending_members.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    st.markdown(f"""
                        <div class="pending-card">
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
                        else:
                            st.error("Lỗi phê duyệt!")
                
                with col4:
                    if st.button("❌ Từ chối", key=f"reject_{member['id']}", use_container_width=True):
                        if reject_member(member['id']):
                            st.warning(f"Đã từ chối {member['full_name']}")
                            st.rerun()
                        else:
                            st.error("Lỗi từ chối!")
                
                st.markdown("---")

# TRANG QUẢN LÝ THÀNH VIÊN MỚI
def show_member_management_page():
    if not st.session_state.user['is_admin']:
        st.error("Chỉ admin mới có quyền truy cập trang này!")
        return
    
    st.title("✏️ Quản lý thành viên")
    
    # Tabs for different management functions
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
                            st.rerun()
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
            # Member selection
            col1, col2 = st.columns([2, 1])
            with col1:
                member_options = [f"{row['full_name']} ({row['email']})" for _, row in members_df.iterrows()]
                selected_idx = st.selectbox("👤 Chọn thành viên cần sửa", range(len(member_options)), format_func=lambda x: member_options[x])
                selected_member = members_df.iloc[selected_idx]
            
            with col2:
                if st.button("📝 Chọn để sửa", use_container_width=True):
                    st.session_state.editing_member_id = selected_member['id']
                    st.rerun()
            
            # Edit form
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
                                        st.rerun()
                                    else:
                                        st.error(message)
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Hủy", use_container_width=True):
                                st.session_state.editing_member_id = None
                                st.rerun()
    
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
                        # Confirmation dialog
                        with col2:
                            st.error(f"⚠️ Bạn có chắc chắn muốn xóa **{member['full_name']}**?")
                            st.write("Hành động này không thể hoàn tác!")
                            
                            col_confirm, col_cancel_delete = st.columns(2)
                            
                            with col_confirm:
                                if st.button("✅ Xác nhận xóa", key=f"confirm_delete_{member['id']}", type="primary", use_container_width=True):
                                    success, message = delete_member(member['id'])
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                            
                            with col_cancel_delete:
                                if st.button("❌ Hủy", key=f"cancel_delete_{member['id']}", use_container_width=True):
                                    st.rerun()

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
                    members = get_approved_members()['full_name'].tolist() if not get_approved_members().empty else []
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
                        if add_ranking(selected_member, wins, match_date, location, score):
                            st.success(f"Đã thêm {wins} trận thắng cho {selected_member}")
                            st.rerun()
    
    if rankings_df.empty:
        st.info("Chưa có dữ liệu xếp hạng")
    else:
        st.subheader("📈 Bảng xếp hạng")
        
        # Hiển thị ranking cards
        for idx, (_, player) in enumerate(rankings_df.iterrows(), 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "🏅"
            
            st.markdown(f"""
                <div class="ranking-card">
                    <h3>{medal} #{idx} - {player['full_name']}</h3>
                    <h2>🏆 {player['total_wins']} trận thắng</h2>
                </div>
            """, unsafe_allow_html=True)
        
        # BIỂU ĐỒ STREAMLIT NATIVE
        if len(rankings_df) > 1:
            st.subheader("📊 Biểu đồ xếp hạng")
            chart_data = rankings_df.head(10).set_index('full_name')
            st.bar_chart(chart_data['total_wins'], height=400)

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
                    members_df = get_approved_members()
                    members = members_df['full_name'].tolist() if not members_df.empty else []
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
                                    st.error(message)
                else:
                    st.warning("Chưa có buổi tập nào có vote")
    
    # Expense history
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
    
    # Financial summary
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
        
        # BIỂU ĐỒ STREAMLIT NATIVE
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
    
    # System statistics
    st.subheader("📊 Thống kê hệ thống")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_approved = 0 AND is_admin = 0')
            pending_count = cursor.fetchone()[0]
            st.metric("⏳ Chờ phê duyệt", pending_count)
        
        with col2:
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_approved = 1 AND is_admin = 0')
            approved_count = cursor.fetchone()[0]
            st.metric("✅ Thành viên active", approved_count)
        
        with col3:
            seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM votes v
                JOIN users u ON v.user_id = u.id
                WHERE v.created_at >= ? AND u.is_admin = 0
            ''', (seven_days_ago,))
            recent_votes = cursor.fetchone()[0]
            st.metric("🗳️ Vote tuần này", recent_votes)
        
        conn.close()
    except Exception as e:
        st.error(f"Lỗi thống kê: {str(e)}")

if __name__ == "__main__":
    main()