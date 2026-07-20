"""Stub implementations used when dev_mode: true in config.yaml."""

def upload_pdf_mock(file_bytes: bytes, filename: str) -> str:
    return f"https://mock.sharepoint.com/invoices/{filename}"


def send_email_mock(sheet: str, row_data: dict, pdf_bytes=None, pdf_filename=None):
    import streamlit as st
    st.toast(f"[DEV] Email would be sent for: {row_data.get('Site Name', row_data.get('QIS No', '?'))}", icon="📧")
