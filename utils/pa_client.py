"""
Power Automate HTTP client.

Replaces graph_client.py entirely. All SharePoint file I/O goes through
three Power Automate flows that run under the flow owner's account —
no app registration, no admin-granted permissions required.

Flow setup instructions are in the README / secrets.toml comments.
"""

import base64
import requests

from utils.config import get_config


def _pa(key: str) -> str:
    url = get_config().get("power_automate", {}).get(key, "")
    if not url:
        raise RuntimeError(
            f"power_automate.{key} is not set in secrets. "
            "Create the Power Automate flow and paste its HTTP trigger URL."
        )
    return url


def download_excel() -> bytes:
    """Call the excel-download flow; returns raw Excel file bytes."""
    resp = requests.post(_pa("excel_download_url"), json={}, timeout=60)
    resp.raise_for_status()
    return base64.b64decode(resp.json()["content"])


def upload_excel(file_bytes: bytes) -> None:
    """Call the excel-upload flow with base64-encoded Excel bytes."""
    payload = {"content": base64.b64encode(file_bytes).decode()}
    resp = requests.post(_pa("excel_upload_url"), json=payload, timeout=60)
    resp.raise_for_status()


def upload_pdf(file_bytes: bytes, filename: str) -> str:
    """Call the pdf-upload flow; returns the SharePoint web URL of the saved file."""
    payload = {
        "content": base64.b64encode(file_bytes).decode(),
        "filename": filename,
    }
    resp = requests.post(_pa("pdf_upload_url"), json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json().get("url", "")
