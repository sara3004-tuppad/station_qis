import re

from utils.config import get_config
from utils.graph_client import graph_get, graph_put_bytes


def _get_site_id(site_url: str) -> str:
    match = re.match(r"https://([^/]+)(/.*)", site_url)
    if not match:
        raise ValueError(f"Invalid SharePoint site URL: {site_url}")
    hostname = match.group(1)
    path = match.group(2)
    data = graph_get(f"https://graph.microsoft.com/v1.0/sites/{hostname}:{path}")
    return data["id"]


def _get_drive_id(site_id: str) -> str:
    data = graph_get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives")
    for drive in data.get("value", []):
        if drive.get("name") in ("Documents", "Shared Documents"):
            return drive["id"]
    return data["value"][0]["id"]


def _upload_pdf_real(file_bytes: bytes, filename: str) -> str:
    cfg = get_config()
    sp_cfg = cfg["sharepoint"]
    site_id = _get_site_id(sp_cfg["site_url"])
    drive_id = _get_drive_id(site_id)
    folder = sp_cfg["upload_folder"].strip("/")
    upload_url = (
        f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}"
        f"/root:/{folder}/{filename}:/content"
    )
    result = graph_put_bytes(upload_url, file_bytes, content_type="application/pdf")
    return result.get("webUrl", "")


def upload_pdf(file_bytes: bytes, filename: str) -> str:
    """Upload PDF to SharePoint; returns web URL of the uploaded file."""
    if get_config().get("dev_mode"):
        from utils.dev_mock import upload_pdf_mock
        return upload_pdf_mock(file_bytes, filename)
    return _upload_pdf_real(file_bytes, filename)
