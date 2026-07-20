import streamlit as st
from utils.config import get_config
from utils.styles import inject_mobile_css

cfg = get_config()
st.set_page_config(
    page_title=cfg["app"]["title"],
    page_icon="🚉",
    layout="centered",
)
inject_mobile_css()

st.title(cfg["app"]["title"])
st.markdown(
    """
    Use the sidebar to navigate to your page:

    | Page | Purpose |
    |---|---|
    | Quality Team | Add new QIS entries |
    | Stores (QC Update) | Update Pickup Status & GRN Date |
    | CPT | Set Allocation & Remarks |
    | Stores (Dispatch) | Fill dispatch info & upload invoice PDF |
    | Deployment View | Read-only — Deployment Team data |
    """
)
