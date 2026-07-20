from datetime import date

import pandas as pd
import streamlit as st
from utils.styles import inject_mobile_css

from utils.config import get_config
from utils.excel_manager import (
    read_quality_sheet,
    read_allocation_sheet,
    bulk_update_quality_rows_stores,
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
        pickup_options = cfg["app"]["pickup_status_options"]

        _EMPTY = {"", "none", "nan", "nat"}

        def _is_pending(row):
            pickup = str(row.get("Pickup status", "")).strip().lower()
            grn = str(row.get("GRN Date", "")).strip().lower()
            return pickup in _EMPTY or grn in _EMPTY

        pending_mask = qc_df.apply(_is_pending, axis=1)
        pending_df = qc_df[pending_mask].copy()

        if pending_df.empty:
            st.success("All QIS entries have Pickup Status and GRN Date filled.")
        else:
            st.caption(f"{len(pending_df)} pending entries — edit directly in the table below, then click Save.")

            # Build editable subset: read-only context cols + editable cols
            display_cols = ["QIS No", "Type", "PDI", "Date", "Pickup status", "GRN Date"]
            edit_df = pending_df[display_cols].reset_index(drop=True)

            # Normalise GRN Date column to date objects for the date picker
            edit_df["GRN Date"] = pd.to_datetime(edit_df["GRN Date"], errors="coerce").dt.date

            edited = st.data_editor(
                edit_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "QIS No": st.column_config.TextColumn("QIS No", disabled=True),
                    "Type": st.column_config.TextColumn("Type", disabled=True),
                    "PDI": st.column_config.TextColumn("PDI", disabled=True),
                    "Date": st.column_config.TextColumn("Date", disabled=True),
                    "Pickup status": st.column_config.SelectboxColumn(
                        "Pickup Status",
                        options=pickup_options,
                        required=False,
                    ),
                    "GRN Date": st.column_config.DateColumn(
                        "GRN Date",
                        format="YYYY-MM-DD",
                    ),
                },
                key="qc_editor",
            )

            if st.button("Save All Updates", type="primary"):
                # Apply edits from session state delta onto the base df
                # (the `edited` return value may be stale on button-click rerun)
                merged = edit_df.copy()
                delta = st.session_state.get("qc_editor", {}).get("edited_rows", {})
                for row_idx, changes in delta.items():
                    for col, val in changes.items():
                        merged.at[int(row_idx), col] = val

                updates = {}
                for _, row in merged.iterrows():
                    qis_no = str(row["QIS No"])
                    updates[qis_no] = {
                        "pickup_status": row["Pickup status"] if pd.notna(row["Pickup status"]) else "",
                        "grn_date": row["GRN Date"] if pd.notna(row["GRN Date"]) else None,
                    }
                try:
                    with st.spinner("Saving to Excel..."):
                        bulk_update_quality_rows_stores(updates)
                    st.success(f"Saved {len(updates)} entries.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save: {e}")

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
