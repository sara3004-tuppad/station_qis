import pandas as pd
import streamlit as st
from utils.styles import inject_mobile_css

from utils.config import get_config
from utils.excel_manager import read_allocation_sheet, update_cpt_row, is_allocation_row_complete
from utils.email_sender import send_completion_email


cfg = get_config()
st.set_page_config(page_title="CPT", layout="centered")
inject_mobile_css()
st.title("CPT — Allocation & Remarks")

try:
    df = read_allocation_sheet()
except Exception as e:
    st.error(f"Could not load Allocation sheet: {e}")
    st.stop()

if df.empty:
    st.info("No deployment entries yet. Deployment Team data must be synced first.")
    st.stop()

# ---------------------------------------------------------------------------
# All deployment sites — full overview for CPT to review before deciding
# ---------------------------------------------------------------------------
st.subheader("All Deployment Sites")
deployment_cols = [
    "Site Name", "Site Type", "No of QIS required", "Region",
    "City", "Lat", "Long", "Address", "POC",
    "Projected Energization Date", "Priority", "Allocation",
]
existing_cols = [c for c in deployment_cols if c in df.columns]
st.dataframe(df[existing_cols], use_container_width=True, hide_index=True)

st.divider()

# ---------------------------------------------------------------------------
# Update allocation for a selected site
# ---------------------------------------------------------------------------
st.subheader("Update Allocation")
site_options = df["Site Name"].dropna().tolist()
selected_site = st.selectbox("Select Site", site_options)
selected_row = df[df["Site Name"] == selected_site].iloc[0]

# Show full site details so CPT has all info before deciding
detail_cols = [
    "Site Name", "Site Type", "No of QIS required", "Region", "City",
    "Lat", "Long", "Address", "POC", "Projected Energization Date", "Priority",
]
with st.expander("Site Details", expanded=True):
    disp = {c: selected_row.get(c, "") for c in detail_cols if c in selected_row}
    st.table(pd.Series(disp).rename("Value"))

with st.form("cpt_form"):
    allocation = st.selectbox(
        "Allocation *",
        ["Yes", "No", "Pending"],
        index=["Yes", "No", "Pending"].index(selected_row["Allocation"])
        if pd.notna(selected_row.get("Allocation")) and selected_row["Allocation"] in ["Yes", "No", "Pending"]
        else 0,
    )
    remarks = st.text_area(
        "Remarks",
        value=selected_row.get("Remarks", "") if pd.notna(selected_row.get("Remarks")) else "",
    )
    submitted = st.form_submit_button("Save", type="primary")

if submitted:
    try:
        update_cpt_row(selected_site, allocation, remarks)
        st.success(f"Saved Allocation={allocation} for {selected_site}")

        if cfg["email"].get("trigger_on_complete", True) and is_allocation_row_complete(selected_site):
            full_df = read_allocation_sheet()
            row_data = full_df[full_df["Site Name"] == selected_site].iloc[0].to_dict()
            send_completion_email("allocation", row_data)
            st.info("All allocation fields complete — notification email sent.")
    except Exception as e:
        st.error(f"Failed to save: {e}")
