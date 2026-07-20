import yaml
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st
from utils.styles import inject_mobile_css

from utils.excel_manager import (
    read_allocation_sheet,
    update_stores_dispatch_row,
    mark_email_sent,
    is_allocation_row_complete,
)
from utils.sharepoint import upload_pdf
from utils.email_sender import send_completion_email


def load_config():
    with open(Path(__file__).parent.parent / "config.yaml") as f:
        return yaml.safe_load(f)


cfg = load_config()
st.set_page_config(page_title="Stores — Dispatch", layout="centered")
inject_mobile_css()
st.title("Stores Team — Dispatch Update & Invoice Upload")

role = st.session_state.get("role", "")
if role != "Stores Team":
    st.warning("This page is for Stores Team only. Please select the correct role on the Home page.")
    st.stop()

try:
    df = read_allocation_sheet()
except Exception as e:
    st.error(f"Could not load Allocation sheet: {e}")
    st.stop()

if df.empty:
    st.info("No entries available yet.")
    st.stop()

site_options = df["Site Name"].dropna().tolist()
selected_site = st.selectbox("Select Site", site_options)
selected_row = df[df["Site Name"] == selected_site].iloc[0]

with st.expander("Site Details", expanded=False):
    cols = ["Site Name", "Site Type", "Region", "City", "Allocation", "Remarks"]
    disp = {c: selected_row.get(c, "") for c in cols if c in selected_row}
    st.json(disp)

with st.form("stores_dispatch_form"):
    col1, col2 = st.columns(2)
    with col1:
        dispatch_date = st.date_input(
            "Date of Dispatch *",
            value=pd.to_datetime(selected_row["Date of Dispatch"]).date()
            if pd.notna(selected_row.get("Date of Dispatch"))
            else date.today(),
        )
        no_qis_delivered = st.number_input(
            "No of QIS Delivered *",
            min_value=0,
            value=int(selected_row["No of QIS delivered"])
            if pd.notna(selected_row.get("No of QIS delivered"))
            else 0,
        )
    with col2:
        expected_delivery = st.date_input(
            "Expected Date of Delivery *",
            value=pd.to_datetime(selected_row["Expected date of delivery"]).date()
            if pd.notna(selected_row.get("Expected date of delivery"))
            else date.today(),
        )
        eway_bill = st.text_input(
            "E-Way Bill No *",
            value=selected_row.get("E-Way Bill", "") if pd.notna(selected_row.get("E-Way Bill")) else "",
        )

    invoice_pdf = st.file_uploader(
        "Upload Invoice PDF *",
        type=["pdf"],
        help="Upload the invoice PDF for this dispatch.",
    )

    submitted = st.form_submit_button("Save & Submit", type="primary")

if submitted:
    errors = []
    if not eway_bill.strip():
        errors.append("E-Way Bill No is required.")
    if invoice_pdf is None:
        errors.append("Invoice PDF is required.")
    if no_qis_delivered <= 0:
        errors.append("No of QIS Delivered must be greater than 0.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        try:
            # 1. Upload PDF to SharePoint
            pdf_bytes = invoice_pdf.read()
            pdf_filename = f"{selected_site.replace(' ', '_')}_{dispatch_date}_invoice.pdf"
            with st.spinner("Uploading invoice to SharePoint..."):
                sharepoint_url = upload_pdf(pdf_bytes, pdf_filename)
            st.success(f"Invoice uploaded: [View on SharePoint]({sharepoint_url})")

            # 2. Update Excel
            data = {
                "Date of Dispatch": dispatch_date,
                "No of QIS delivered": no_qis_delivered,
                "Expected date of delivery": expected_delivery,
                "E-Way Bill": eway_bill.strip(),
            }
            update_stores_dispatch_row(selected_site, data)

            # 3. Email if complete
            if cfg["email"].get("trigger_on_complete", True) and is_allocation_row_complete(selected_site):
                full_df = read_allocation_sheet()
                row_data = full_df[full_df["Site Name"] == selected_site].iloc[0].to_dict()
                row_data["SharePoint Invoice URL"] = sharepoint_url
                with st.spinner("Sending notification email..."):
                    send_completion_email(
                        "allocation",
                        row_data,
                        pdf_bytes=pdf_bytes,
                        pdf_filename=pdf_filename,
                    )
                mark_email_sent(selected_site)
                st.info("All fields complete — email with invoice sent to all teams.")
            else:
                st.success("Dispatch details saved. Email will be sent once all fields are complete.")

        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.subheader("All Allocation Entries")
st.dataframe(df, use_container_width=True, hide_index=True)
