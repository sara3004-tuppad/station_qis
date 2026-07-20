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

    | Page | Who | What to do |
    |---|---|---|
    | Quality Team | Quality Team | Add new QIS entries (Type, PDI, Date) |
    | Stores | Stores Team | **QC Update** tab — update Pickup Status & GRN Date |
    | Stores | Stores Team | **Dispatch** tab — fill dispatch info & upload invoice PDF |
    | CPT | CPT Team | Review all deployment sites and set Allocation & Remarks |
    """
)
