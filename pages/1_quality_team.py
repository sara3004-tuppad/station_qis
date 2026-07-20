import yaml
from pathlib import Path
from datetime import date

import streamlit as st

from utils.excel_manager import append_quality_row, read_quality_sheet
from utils.styles import inject_mobile_css


def load_config():
    with open(Path(__file__).parent.parent / "config.yaml") as f:
        return yaml.safe_load(f)


cfg = load_config()
st.set_page_config(page_title="Quality Team", layout="centered")
inject_mobile_css()
st.title("Quality Team — Add QIS Entry")

role = st.session_state.get("role", "")
if role != "Quality Team":
    st.warning("This page is for Quality Team only. Please select the correct role on the Home page.")
    st.stop()

st.subheader("New QIS Entry")

with st.form("quality_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        entry_date = st.date_input("Date *", value=date.today())
        qis_no = st.text_input("QIS No *")
    with col2:
        qis_type = st.text_input("Type *", placeholder="e.g. split AC QIS, 6DS")
        pdi = st.selectbox("PDI *", cfg["app"]["pdi_options"])

    submitted = st.form_submit_button("Save Entry", type="primary")

if submitted:
    if not qis_no.strip():
        st.error("QIS No is required.")
    elif not qis_type.strip():
        st.error("Type is required.")
    else:
        row = {
            "Date": entry_date,
            "QIS No": qis_no.strip(),
            "Type": qis_type.strip(),
            "PDI": pdi,
        }
        try:
            append_quality_row(row)
            st.success(f"Entry saved for QIS No: {qis_no}")
        except Exception as e:
            st.error(f"Failed to save: {e}")

st.divider()
st.subheader("Existing Entries")
try:
    df = read_quality_sheet()
    if df.empty:
        st.info("No entries yet.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Could not load sheet: {e}")
