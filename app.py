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

# Temporary debug — remove after confirming secrets are loaded correctly
with st.expander("🔧 Debug: Secrets check", expanded=False):
    graph_cfg = cfg.get("graph", {})
    st.write("tenant_id set:", bool(graph_cfg.get("tenant_id")))
    st.write("client_id set:", bool(graph_cfg.get("client_id")))
    st.write("refresh_token set:", bool(graph_cfg.get("refresh_token")))
    st.write("excel.sharepoint_url set:", bool(cfg.get("excel", {}).get("sharepoint_url")))

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
