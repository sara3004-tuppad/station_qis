import yaml
from pathlib import Path
import streamlit as st
from utils.styles import inject_mobile_css

def load_config():
    with open(Path(__file__).parent / "config.yaml") as f:
        return yaml.safe_load(f)

cfg = load_config()
st.set_page_config(
    page_title=cfg["app"]["title"],
    page_icon="🚉",
    layout="centered",
)
inject_mobile_css()

st.title(cfg["app"]["title"])

# Role selector in sidebar
st.sidebar.header("Select Your Role")
roles = cfg["app"]["roles"]
role = st.sidebar.selectbox("I am from:", roles)

# Optional role password check
passwords = cfg["app"].get("role_passwords", {})
required_pw = passwords.get(role, "")
if required_pw:
    entered = st.sidebar.text_input("Password", type="password")
    if entered != required_pw:
        st.sidebar.error("Incorrect password.")
        st.warning("Please enter the correct password for your role.")
        st.stop()

st.session_state["role"] = role
st.sidebar.success(f"Logged in as: **{role}**")

# Navigation guidance
st.markdown(
    f"""
    Welcome, **{role}**. Use the sidebar pages to complete your tasks:

    | Page | For |
    |---|---|
    | Quality Team | Quality Team — add new QIS entries |
    | Stores (QC Update) | Stores Team — update Pickup Status & GRN Date |
    | CPT | CPT — set Allocation & Remarks |
    | Stores (Dispatch) | Stores Team — fill dispatch info & upload invoice PDF |
    | Deployment View | Read-only — view Deployment Team data from MS Forms |
    """
)
