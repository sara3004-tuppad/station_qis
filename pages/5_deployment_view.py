import streamlit as st

from utils.excel_manager import read_allocation_sheet
from utils.styles import inject_mobile_css

st.set_page_config(page_title="Deployment View", layout="centered")
inject_mobile_css()
st.title("Deployment Team — Site Allocations")

st.info(
    "This page is read-only. Deployment team data is populated automatically "
    "via Microsoft Forms + Power Automate into the Excel on SharePoint."
)

try:
    df = read_allocation_sheet()
    if df.empty:
        st.warning("No deployment entries found yet in the Excel sheet.")
    else:
        deployment_cols = [
            "Site Name", "Site Type", "No of QIS required", "Region",
            "City", "Lat", "Long", "Address", "POC",
            "Projected Energization Date", "Priority",
        ]
        existing_cols = [c for c in deployment_cols if c in df.columns]
        st.success(f"{len(df)} site(s) loaded from SharePoint Excel.")
        st.dataframe(df[existing_cols], use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Could not load data: {e}")
