from datetime import date

import pandas as pd
import streamlit as st
from utils.styles import inject_mobile_css

from utils.config import get_config
from utils.excel_manager import (
    read_quality_sheet,
    read_allocation_sheet,
    update_quality_row_stores,
    update_stores_dispatch_row,
    mark_email_sent,
    is_allocation_row_complete,
)
from utils.sharepoint import upload_pdf
from utils.email_sender import send_completion_email


cfg = get_config()
st.set_page_config(page_title="Stores", layout="centered")
inject_mobile_css()
st.title("Stores Team")

tab_qc, tab_dispatch = st.tabs(["QC Update", "Dispatch"])

# ---------------------------------------------------------------------------
# Tab 1 — QC Update (Quality Clearance sheet)
# ---------------------------------------------------------------------------
with tab_qc:
    st.subheader("Quality Clearance Update")
    try:
        qc_df = read_quality_sheet()
    except Exception as e:
        st.error(f"Could not load Quality sheet: {e}")
        st.stop()

    if qc_df.empty:
        st.info("No QIS entries found. Quality Team must add entries first.")
    else:
        qis_options = qc_df["QIS No"].dropna().astype(str).tolist()
        selected_qis = st.selectbox("Select QIS No to update", qis_options)
        selected_row = qc_df[qc_df["QIS No"].astype(str) == selected_qis].iloc[0]

        st.markdown(
            f"**Type:** {selected_row.get('Type', '')} | "
            f"**PDI:** {selected_row.get('PDI', '')} | "
            f"**Date:** {selected_row.get('Date', '')}"
        )

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
            submitted_qc = st.form_submit_button("Save Update", type="primary")

        if submitted_qc:
            try:
                update_quality_row_stores(selected_qis, pickup_status, grn_date)
                st.success(f"Updated QIS {selected_qis} — Pickup: {pickup_status}, GRN Date: {grn_date}")
            except Exception as e:
                st.error(f"Failed to update: {e}")

        st.divider()
        st.subheader("All Quality Entries")
        st.dataframe(qc_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Tab 2 — Dispatch (Allocation sheet)
# ---------------------------------------------------------------------------
with tab_dispatch:
    st.subheader("Dispatch Update & Invoice Upload")
    try:
        alloc_df = read_allocation_sheet()
    except Exception as e:
        st.error(f"Could not load Allocation sheet: {e}")
        st.stop()

    if alloc_df.empty:
        st.info("No entries available yet.")
    else:
        site_options = alloc_df["Site Name"].dropna().tolist()
        selected_site = st.selectbox("Select Site", site_options, key="dispatch_site")
        selected_row = alloc_df[alloc_df["Site Name"] == selected_site].iloc[0]

        with st.expander("Site Details", expanded=False):
            cols = ["Site Name", "Site Type", "Region", "City", "Allocation", "Remarks"]
            disp = {c: selected_row.get(c, "") for c in cols if c in selected_row}
            st.table(pd.Series(disp).rename("Value"))

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
            submitted_dispatch = st.form_submit_button("Save & Submit", type="primary")

        if submitted_dispatch:
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
                    pdf_bytes = invoice_pdf.read()
                    pdf_filename = f"{selected_site.replace(' ', '_')}_{dispatch_date}_invoice.pdf"
                    with st.spinner("Uploading invoice to SharePoint..."):
                        sharepoint_url = upload_pdf(pdf_bytes, pdf_filename)
                    st.success(f"Invoice uploaded: [View on SharePoint]({sharepoint_url})")

                    data = {
                        "Date of Dispatch": dispatch_date,
                        "No of QIS delivered": no_qis_delivered,
                        "Expected date of delivery": expected_delivery,
                        "E-Way Bill": eway_bill.strip(),
                    }
                    update_stores_dispatch_row(selected_site, data)

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
        st.dataframe(alloc_df, use_container_width=True, hide_index=True)
