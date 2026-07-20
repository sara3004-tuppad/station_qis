import yaml
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st
from utils.styles import inject_mobile_css

from utils.excel_manager import (
    read_quality_sheet,
    update_quality_row_stores,
)


def load_config():
    with open(Path(__file__).parent.parent / "config.yaml") as f:
        return yaml.safe_load(f)


cfg = load_config()
st.set_page_config(page_title="Stores — QC Update", layout="centered")
inject_mobile_css()
st.title("Stores Team — Quality Clearance Update")

role = st.session_state.get("role", "")
if role != "Stores Team":
    st.warning("This page is for Stores Team only. Please select the correct role on the Home page.")
    st.stop()

try:
    df = read_quality_sheet()
except Exception as e:
    st.error(f"Could not load Quality sheet: {e}")
    st.stop()

if df.empty:
    st.info("No QIS entries found. Quality Team must add entries first.")
    st.stop()

# Let stores pick which QIS to update
qis_options = df["QIS No"].dropna().astype(str).tolist()
selected_qis = st.selectbox("Select QIS No to update", qis_options)

selected_row = df[df["QIS No"].astype(str) == selected_qis].iloc[0]

st.markdown(f"**Type:** {selected_row.get('Type', '')} | **PDI:** {selected_row.get('PDI', '')} | **Date:** {selected_row.get('Date', '')}")

with st.form("stores_qc_form"):
    col1, col2 = st.columns(2)
    with col1:
        pickup_status = st.selectbox(
            "Pickup Status *",
            cfg["app"]["pickup_status_options"],
            index=cfg["app"]["pickup_status_options"].index(selected_row["Pickup status"])
            if pd.notna(selected_row.get("Pickup status")) and selected_row["Pickup status"] in cfg["app"]["pickup_status_options"]
            else 0,
        )
    with col2:
        grn_date = st.date_input(
            "GRN Date *",
            value=selected_row["GRN Date"] if pd.notna(selected_row.get("GRN Date")) else date.today(),
        )

    submitted = st.form_submit_button("Save Update", type="primary")

if submitted:
    try:
        update_quality_row_stores(selected_qis, pickup_status, grn_date)
        st.success(f"Updated QIS {selected_qis} — Pickup: {pickup_status}, GRN Date: {grn_date}")
    except Exception as e:
        st.error(f"Failed to update: {e}")

st.divider()
st.subheader("All Quality Entries")
st.dataframe(df, use_container_width=True, hide_index=True)
