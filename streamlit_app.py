import streamlit as st
import json
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

# DATA PERSISTENCE SYSTEM - SỬ DỤNG SESSION STATE VÀ JSON
def init_data_storage():
    """Khởi tạo hệ thống lưu trữ dữ liệu persistent"""
    if 'data_initialized' not in st.session_state:
        # Cấu trúc dữ liệu chính
        default_data = {
            'users': [
                {
                    'id': 1,
                    'full_name': 'Administrator',
                    'email': 'admin@local',
                    'phone': '0000000000',
                    'birth_date': '1990-01-01',
                    'password': hashlib.sha256('Admin@123'.encode()).hexdigest(),
                    'is_approved': 1,
                    'is_admin': 1,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            ],
            'rankings': [],
            'vote_sessions': [],
            'votes': [],
            'finances': [],
            'next_user_id': 2,
            'next_ranking_id': 1,
            'next_vote_session_id': 1,
            'next_vote_id': 1,
            'next_finance_id': 1
        }
        
        # Khởi tạo dữ liệu
        st.session_state.club_data = default_data
        st.session_state.data_initialized = True

def save_data_to_session():
    """Lưu dữ liệu vào session state"""
    # Dữ liệu đã được lưu trong st.session_state.club_data
    pass

def get_data():
    """Lấy dữ liệu từ session state"""
    if 'club_data' not in st.session_state:
        init_data_storage()
    return st.session_state.club_data

def get_next_id(table_name):
    """Lấy ID tiếp theo cho table"""
    data = get_data()
    next_id_key = f'next_{table_name}_id'
    current_id = data[next_id_key]
    data[next_id_key] += 1
    return current_id

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(full_name, email, phone, birth_date, password):
    try:
        data = get_data()
        
        # Check if email exists
        for user in data['users']:
            if user['email'] == email:
                return False, "Email đã tồn tại!"
        
        # Add new user
        new_user = {
            'id': get_next_id('user'),
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'birth_date': str(birth_date),
            'password': hash_password(password),
            'is_approved': 0,
            'is_admin': 0,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        data['users'].append(new_user)
        return True, "Đăng ký thành công! Vui lòng chờ admin phê duyệt."
    except Exception as e:
        return False, f"Lỗi đăng ký: {str(e)}"

def login_user(email, password):
    try:
        data = get_data()
        hashed_password = hash_password(password)
        
        for user in data['users']:
            if user['email'] == email and user['password'] == hashed_password:
                if user['is_approved'] == 1 or user['is_admin'] == 1:
                    return True, {
                        'id': user['id'],
                        'name': user['full_name'],
                        'is_admin': user['is_admin'] == 1
                    }
                else:
                    return False, "Tài khoản chưa được phê duyệt!"
        
        return False, "Email hoặc mật khẩu không đúng!"
    except Exception as e:
        return False, f"Lỗi đăng nhập: {str(e)}"

# Data helper functions
def get_pending_members():
    data = get_data()
    pending = [user for user in data['users'] if user['is_approved'] == 0 and user['is_admin'] == 0]
    return pd.DataFrame(pending)

def get_approved_members():
    data = get_data()
    approved = [user for user in data['users'] if user['is_approved'] == 1 and user['is_admin'] == 0]
    return pd.DataFrame(approved)

def approve_member(user_id, admin_name):
    try:
        data = get_data()
        for user in data['users']:
            if user['id'] == user_id:
                user['is_approved'] = 1
                user['approved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                user['approved_by'] = admin_name
                return True
        return False
    except Exception as e:
        st.error(f"Lỗi phê duyệt: {str(e)}")
        return False

def reject_member(user_id):
    try:
        data = get_data()
        data['users'] = [user for user in data['users'] if user['id'] != user_id]
        return True
    except Exception as e:
        st.error(f"Lỗi từ chối: {str(e)}")
        return False

def get_rankings():
    data = get_data()
    
    # Count wins for each member
    member_wins = {}
    for user in data['users']:
        if user['is_approved'] == 1 and user['is_admin'] == 0:
            member_wins[user['full_name']] = 0
    
    for ranking in data['rankings']:
        # Find user name
        for user in data['users']:
            if user['id'] == ranking['user_id']:
                if user['full_name'] in member_wins:
                    member_wins[user['full_name']] += 1
                break
    
    # Convert to DataFrame
    rankings_list = [{'full_name': name, 'total_wins': wins} for name, wins in member_wins.items()]
    rankings_list.sort(key=lambda x: x['total_wins'], reverse=True)
    
    return pd.DataFrame(rankings_list)

def add_ranking(user_name, wins, match_date, location, score):
    try:
        data = get_data()
        
        # Find user ID
        user_id = None
        for user in data['users']:
            if user['full_name'] == user_name and user['is_approved'] == 1 and user['is_admin'] == 0:
                user_id = user['id']
                break
        
        if user_id:
            for _ in range(wins):
                new_ranking = {
                    'id': get_next_id('ranking'),
                    'user_id': user_id,
                    'match_date': str(match_date),
                    'location': location,
                    'score': score,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                data['rankings'].append(new_ranking)
            return True
        return False
    except Exception as e:
        st.error(f"Lỗi thêm ranking: {str(e)}")
        return False

def get_vote_sessions():
    data = get_data()
    
    vote_sessions_with_count = []
    for session in data['vote_sessions']:
        # Count votes for this session from members only
        vote_count = 0
        for vote in data['votes']:
            if vote['session_date'] == session['session_date']:
                # Check if voter is a member (not admin)
                for user in data['users']:
                    if user['id'] == vote['user_id'] and user['is_admin'] == 0:
                        vote_count += 1
                        break
        
        session_with_count = session.copy()
        session_with_count['vote_count'] = vote_count
        vote_sessions_with_count.append(session_with_count)
    
    # Sort by date descending
    vote_sessions_with_count.sort(key=lambda x: x['session_date'], reverse=True)
    
    return pd.DataFrame(vote_sessions_with_count)

def create_vote_session(session_date, description):
    try:
        data = get_data()
        new_session = {
            'id': get_next_id('vote_session'),
            'session_date': str(session_date),
            'description': description,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        data['vote_sessions'].append(new_session)
        return True
    except Exception as e:
        st.error(f"Lỗi tạo vote session: {str(e)}")
        return False

def vote_for_session(user_id, session_date):
    try:
        data = get_data()
        
        # Check if already voted
        for vote in data['votes']:
            if vote['user_id'] == user_id and vote['session_date'] == str(session_date):
                return False
        
        # Add vote
        new_vote = {
            'id': get_next_id('vote'),
            'user_id': user_id,
            'session_date': str(session_date),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        data['votes'].append(new_vote)
        return True
    except Exception as e:
        st.error(f"Lỗi vote: {str(e)}")
        return False

def get_vote_details(session_date):
    data = get_data()
    
    vote_details = []
    for vote in data['votes']:
        if vote['session_date'] == str(session_date):
            # Find user info
            for user in data['users']:
                if user['id'] == vote['user_id'] and user['is_admin'] == 0:
                    vote_details.append({
                        'full_name': user['full_name'],
                        'created_at': vote['created_at']
                    })
                    break
    
    return pd.DataFrame(vote_details)

def add_contribution(user_name, amount):
    try:
        data = get_data()
        
        # Find user ID
        user_id = None
        for user in data['users']:
            if user['full_name'] == user_name and user['is_approved'] == 1 and user['is_admin'] == 0:
                user_id = user['id']
                break
        
        if user_id:
            new_finance = {
                'id': get_next_id('finance'),
                'user_id': user_id,
                'amount': amount,
                'transaction_type': 'contribution',
                'description': 'Đóng quỹ',
                'session_date': '',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            data['finances'].append(new_finance)
            return True
        return False
    except Exception as e:
        st.error(f"Lỗi thêm đóng góp: {str(e)}")
        return False

def get_vote_sessions_for_expense():
    data = get_data()
    
    sessions_with_votes = []
    for session in data['vote_sessions']:
        # Count member votes
        vote_count = 0
        for vote in data['votes']:
            if vote['session_date'] == session['session_date']:
                # Check if voter is member
                for user in data['users']:
                    if user['id'] == vote['user_id'] and user['is_admin'] == 0:
                        vote_count += 1
                        break
        
        if vote_count > 0:
            session_data = session.copy()
            session_data['vote_count'] = vote_count
            sessions_with_votes.append(session_data)
    
    # Sort by date descending
    sessions_with_votes.sort(key=lambda x: x['session_date'], reverse=True)
    
    return pd.DataFrame(sessions_with_votes)

def add_expense(session_date, court_fee, water_fee, other_fee, description):
    try:
        data = get_data()
        total_fee = court_fee + water_fee + other_fee
        
        # Get member voters for this session
        voters = []
        for vote in data['votes']:
            if vote['session_date'] == str(session_date):
                # Check if voter is member
                for user in data['users']:
                    if user['id'] == vote['user_id'] and user['is_admin'] == 0:
                        voters.append(vote['user_id'])
                        break
        
        if voters:
            cost_per_person = total_fee // len(voters)
            
            for voter_id in voters:
                new_expense = {
                    'id': get_next_id('finance'),
                    'user_id': voter_id,
                    'amount': -cost_per_person,
                    'transaction_type': 'expense',
                    'description': description,
                    'session_date': str(session_date),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                data['finances'].append(new_expense)
            
            return True, f"Đã chia {total_fee:,} VNĐ cho {len(voters)} thành viên ({cost_per_person:,} VNĐ/người)"
        else:
            return False, "Không có thành viên nào vote cho buổi này"
    except Exception as e:
        return False, f"Lỗi thêm chi phí: {str(e)}"

def get_financial_summary():
    data = get_data()
    
    # Calculate for each member
    financial_summary = []
    for user in data['users']:
        if user['is_approved'] == 1 and user['is_admin'] == 0:
            total_contribution = 0
            total_expenses = 0
            sessions_attended = 0
            
            for finance in data['finances']:
                if finance['user_id'] == user['id']:
                    if finance['transaction_type'] == 'contribution':
                        total_contribution += finance['amount']
                    elif finance['transaction_type'] == 'expense':
                        total_expenses += finance['amount']  # negative amount
                        sessions_attended += 1
            
            balance = total_contribution + total_expenses  # expenses are negative
            
            financial_summary.append({
                'full_name': user['full_name'],
                'total_contribution': total_contribution,
                'sessions_attended': sessions_attended,
                'total_expenses': total_expenses,
                'balance': balance
            })
    
    # Sort by balance descending
    financial_summary.sort(key=lambda x: x['balance'], reverse=True)
    
    return pd.DataFrame(financial_summary)

def get_expense_history():
    data = get_data()
    
    # Group expenses by session
    session_expenses = {}
    for finance in data['finances']:
        if finance['transaction_type'] == 'expense' and finance['session_date']:
            session_date = finance['session_date']
            if session_date not in session_expenses:
                session_expenses[session_date] = {
                    'session_date': session_date,
                    'description': finance['description'],
                    'total_cost': 0,
                    'participants_count': 0,
                    'cost_per_person': abs(finance['amount']),
                    'created_at': finance['created_at']
                }
            session_expenses[session_date]['total_cost'] += abs(finance['amount'])
            session_expenses[session_date]['participants_count'] += 1
    
    # Convert to list and sort by date
    expense_list = list(session_expenses.values())
    expense_list.sort(key=lambda x: x['session_date'], reverse=True)
    
    return pd.DataFrame(expense_list)

def get_alerts():
    alerts = []
    
    try:
        financial_df = get_financial_summary()
        
        # Low balance alert
        for _, user in financial_df.iterrows():
            if user['balance'] < 100000:
                alerts.append(f"⚠️ {user['full_name']} có số dư thấp: {user['balance']:,} VNĐ")
        
        # Low voting activity (simplified - check last 30 days)
        data = get_data()
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        for user in data['users']:
            if user['is_approved'] == 1 and user['is_admin'] == 0:
                vote_count = 0
                for vote in data['votes']:
                    if vote['user_id'] == user['id'] and vote['created_at'] >= thirty_days_ago:
                        vote_count += 1
                
                if vote_count < 3:
                    alerts.append(f"📊 {user['full_name']} vote ít trong 30 ngày qua: {vote_count} lần")
        
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

# Initialize data storage
init_data_storage()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Trang chủ"

# Main app
def main():
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
    
    # Data persistence info
    st.subheader("📊 Thông tin hệ thống")
    st.info("💾 **Dữ liệu được lưu trữ persistent**: Khi reboot app, dữ liệu sẽ được giữ lại trong session của bạn. Để reset hoàn toàn, vui lòng xóa cache trình duyệt hoặc mở tab ẩn danh mới.")
    
    # Show current data stats
    data = get_data()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Người dùng", len(data['users']))
    
    with col2:
        st.metric("🏆 Kết quả trận đấu", len(data['rankings']))
    
    with col3:
        st.metric("🗳️ Phiên vote", len(data['vote_sessions']))
    
    with col4:
        st.metric("💰 Giao dịch", len(data['finances']))

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
        
        for idx, (_, player) in enumerate(rankings_df.iterrows(), 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "🏅"
            
            st.markdown(f"""
                <div class="ranking-card">
                    <h3>{medal} #{idx} - {player['full_name']}</h3>
                    <h2>🏆 {player['total_wins']} trận thắng</h2>
                </div>
            """, unsafe_allow_html=True)
        
        # Chart
        if len(rankings_df) > 1:
            chart_html = create_horizontal_bar_chart(rankings_df.head(10), "📊 Top 10 thành viên xuất sắc")
            st.markdown(chart_html, unsafe_allow_html=True)

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
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            chart_html = create_balance_chart(financial_df)
            st.markdown(chart_html, unsafe_allow_html=True)
        
        with col2:
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
    else:
        st.subheader(f"🚨 Có {len(alerts)} cảnh báo cần chú ý")
        
        for alert in alerts:
            if "số dư thấp" in alert:
                st.markdown(f'<div class="danger-card">{alert}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-card">{alert}</div>', unsafe_allow_html=True)
    
    # System statistics
    st.subheader("📊 Thống kê hệ thống")
    
    data = get_data()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pending_count = len([u for u in data['users'] if u['is_approved'] == 0 and u['is_admin'] == 0])
        st.metric("⏳ Chờ phê duyệt", pending_count)
    
    with col2:
        approved_count = len([u for u in data['users'] if u['is_approved'] == 1 and u['is_admin'] == 0])
        st.metric("✅ Thành viên active", approved_count)
    
    with col3:
        # Count votes in last 7 days from members
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        recent_votes = 0
        for vote in data['votes']:
            if vote['created_at'] >= seven_days_ago:
                # Check if voter is member
                for user in data['users']:
                    if user['id'] == vote['user_id'] and user['is_admin'] == 0:
                        recent_votes += 1
                        break
        st.metric("🗳️ Vote tuần này", recent_votes)

if __name__ == "__main__":
    main()
