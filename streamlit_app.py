import streamlit as st
import pandas as pd
import hashlib
import os

# ---------------------------
# Helper functions
# ---------------------------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists("users.csv"):
        df = pd.read_csv("users.csv")
        if "wins" not in df.columns:
            df["wins"] = 0
        return df
    else:
        return pd.DataFrame(columns=["id", "name", "email", "phone", "password", "approved", "is_admin", "wins"])

def save_users(df):
    df.to_csv("users.csv", index=False)

def load_votes():
    if os.path.exists("votes.csv"):
        return pd.read_csv("votes.csv")
    else:
        return pd.DataFrame(columns=["user_id", "candidate"])

def save_votes(df):
    df.to_csv("votes.csv", index=False)

# ---------------------------
# Khởi tạo dữ liệu mặc định
# ---------------------------

users_df = load_users()

if users_df.empty:
    users_df = pd.DataFrame([{
        "id": 1,
        "name": "Admin",
        "email": "admin@example.com",
        "phone": "0000000000",
        "password": hash_password("admin123"),
        "approved": True,
        "is_admin": True,
        "wins": 0
    }])
    save_users(users_df)

# ---------------------------
# UI
# ---------------------------

st.set_page_config(page_title="DTT Club Management", layout="wide")
st.title("🏓 DTT Club Management System")

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------------------
# Tabs
# ---------------------------
tab_login, tab_register, tab_vote, tab_admin = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký", "🗳️ Bình chọn", "⚙️ Quản trị"])

# ---------------------------
# Đăng nhập
# ---------------------------
with tab_login:
    st.subheader("Đăng nhập hệ thống")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Mật khẩu", type="password", key="login_password")

    if st.button("Đăng nhập", key="btn_login"):
        users_df = load_users()
        user = users_df[users_df["email"] == email]
        if not user.empty and user.iloc[0]["password"] == hash_password(password):
            if user.iloc[0]["approved"]:
                st.session_state.logged_in = True
                st.session_state.user = user.iloc[0].to_dict()
                st.success(f"Chào mừng {st.session_state.user['name']} 👋")
            else:
                st.error("Tài khoản chưa được phê duyệt.")
        else:
            st.error("Email hoặc mật khẩu không đúng.")

# ---------------------------
# Đăng ký
# ---------------------------
with tab_register:
    st.subheader("Đăng ký thành viên mới")

    name = st.text_input("Tên", key="reg_name")
    email = st.text_input("Email (unique)", key="reg_email")
    phone = st.text_input("Số điện thoại", key="reg_phone")
    password = st.text_input("Mật khẩu", type="password", key="reg_password")

    if st.button("Đăng ký", key="btn_register"):
        users_df = load_users()
        if email in users_df["email"].values:
            st.error("Email đã tồn tại.")
        else:
            new_id = users_df["id"].max() + 1 if not users_df.empty else 1
            new_user = {
                "id": new_id,
                "name": name,
                "email": email,
                "phone": phone,
                "password": hash_password(password),
                "approved": False,
                "is_admin": False,
                "wins": 0
            }
            users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
            save_users(users_df)
            st.success("Đăng ký thành công! Vui lòng chờ quản trị viên phê duyệt.")

# ---------------------------
# Bình chọn
# ---------------------------
with tab_vote:
    st.subheader("Bình chọn cho thành viên xuất sắc")

    if st.session_state.logged_in:
        users_df = load_users()
        candidates = users_df[users_df["approved"] & (~users_df["is_admin"])]
        candidate_names = candidates["name"].tolist()

        if candidate_names:
            choice = st.selectbox("Chọn thành viên", candidate_names, key="vote_choice")
            if st.button("Bình chọn", key="btn_vote"):
                votes_df = load_votes()
                if st.session_state.user["id"] in votes_df["user_id"].values:
                    st.error("Bạn đã bình chọn rồi.")
                else:
                    new_vote = {
                        "user_id": st.session_state.user["id"],
                        "candidate": choice
                    }
                    votes_df = pd.concat([votes_df, pd.DataFrame([new_vote])], ignore_index=True)
                    save_votes(votes_df)
                    st.success("Cảm ơn bạn đã bình chọn!")
        else:
            st.info("Chưa có ứng viên để bình chọn.")
    else:
        st.warning("Vui lòng đăng nhập trước khi bình chọn.")

# ---------------------------
# Quản trị viên
# ---------------------------
with tab_admin:
    st.subheader("Quản trị hệ thống")

    if st.session_state.logged_in and st.session_state.user["is_admin"]:
        st.write("Danh sách thành viên:")

        users_df = load_users()
        st.dataframe(users_df[["id", "name", "email", "phone", "approved", "is_admin", "wins"]])

        approve_id = st.number_input("Nhập ID để phê duyệt", min_value=1, step=1, key="approve_id")
        if st.button("Phê duyệt", key="btn_approve"):
            users_df.loc[users_df["id"] == approve_id, "approved"] = True
            save_users(users_df)
            st.success(f"Đã phê duyệt user ID {approve_id}")

        win_id = st.number_input("Nhập ID để cộng 1 chiến thắng", min_value=1, step=1, key="win_id")
        if st.button("Cộng 1 thắng", key="btn_add_win"):
            users_df.loc[users_df["id"] == win_id, "wins"] += 1
            save_users(users_df)
            st.success(f"Đã cộng 1 trận thắng cho user ID {win_id}")

    else:
        st.warning("Chỉ quản trị viên mới được truy cập.")
