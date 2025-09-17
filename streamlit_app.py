import streamlit as st
import pandas as pd

st.set_page_config(page_title="Club Management App", layout="wide")

# --- Khởi tạo dữ liệu ---
if "members" not in st.session_state:
    st.session_state.members = pd.DataFrame(columns=["Name", "Email", "Role", "Join Date", "Points"])
if "finance" not in st.session_state:
    st.session_state.finance = pd.DataFrame(columns=["Date", "Description", "Amount", "Type"])
if "votes" not in st.session_state:
    st.session_state.votes = pd.DataFrame(columns=["Match", "Member", "Vote"])

st.title("⚽ Club Management App")

# --- Quản lý thành viên ---
st.header("👥 Members Management")
with st.form("add_member", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    name = col1.text_input("Name")
    email = col2.text_input("Email")
    role = col3.selectbox("Role", ["Player", "Manager"])
    join_date = st.date_input("Join Date")
    submitted = st.form_submit_button("➕ Add Member")
    if submitted and name:
        st.session_state.members.loc[len(st.session_state.members)] = [name, email, role, str(join_date), 0]
st.dataframe(st.session_state.members)

# --- Ranking ---
st.header("🏆 Ranking")
ranking = st.session_state.members.sort_values(by="Points", ascending=False)
st.dataframe(ranking[["Name", "Points"]])

# --- Tài chính ---
st.header("💰 Financial Tracking")
with st.form("add_finance", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    date = col1.date_input("Date")
    desc = col2.text_input("Description")
    amount = col3.number_input("Amount", value=0)
    type_ = st.selectbox("Type", ["Income", "Expense"])
    submitted = st.form_submit_button("➕ Add Record")
    if submitted and desc:
        st.session_state.finance.loc[len(st.session_state.finance)] = [str(date), desc, amount, type_]
st.dataframe(st.session_state.finance)

balance = st.session_state.finance.apply(lambda r: r["Amount"] if r["Type"]=="Income" else -r["Amount"], axis=1).sum()
st.metric("💵 Current Balance", f"{balance} VND")

# --- Vote cho trận đấu ---
st.header("🗳️ Vote for Next Match")
match_id = st.text_input("Match ID", "Match_1")
member = st.selectbox("Select Member", st.session_state.members["Name"].tolist())
vote = st.radio("Vote", ["Yes", "No"])
if st.button("Submit Vote"):
    st.session_state.votes.loc[len(st.session_state.votes)] = [match_id, member, vote]
st.dataframe(st.session_state.votes)

# --- Tính phí ---
st.header("💸 Fee Calculation")
total_fee = st.number_input("Total Match Fee", value=0)
if st.button("Calculate Fee"):
    players = st.session_state.votes[(st.session_state.votes["Match"] == match_id) & (st.session_state.votes["Vote"]=="Yes")]["Member"].tolist()
    if players:
        fee_per_player = total_fee / len(players)
        st.success(f"Each player pays: {fee_per_player:.0f} VND")
        for p in players:
            st.session_state.finance.loc[len(st.session_state.finance)] = [str(pd.Timestamp.today().date()), f"Match Fee ({match_id}) - {p}", fee_per_player, "Income"]
    else:
        st.warning("No players voted 'Yes'")
