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

site_options = df["Site Name"].dropna().tolist()
selected_site = st.selectbox("Select Site to update", site_options)

selected_row = df[df["Site Name"] == selected_site].iloc[0]

with st.expander("Deployment Team Details", expanded=True):
    cols = ["Site Name", "Site Type", "No of QIS required", "Region", "City",
            "Address", "POC", "Projected Energization Date", "Priority"]
    disp = {c: selected_row.get(c, "") for c in cols if c in selected_row}
    st.json(disp)

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

st.divider()
st.subheader("All Allocation Entries")
st.dataframe(df, use_container_width=True, hide_index=True)
