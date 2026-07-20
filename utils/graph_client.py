"""
Graph API client using device-flow refresh token auth.

One-time setup: run get_refresh_token.py locally to get a refresh token,
then store it in secrets as graph.refresh_token.
No admin consent needed — authenticates as the file owner via their own token.
"""

import base64
import requests
import msal

from utils.config import get_config

_token = None

SCOPES = ["https://graph.microsoft.com/Files.ReadWrite"]


def get_access_token() -> str:
    global _token
    cfg = get_config()["graph"]
    app = msal.PublicClientApplication(
        client_id=cfg["client_id"],
        authority=f"https://login.microsoftonline.com/{cfg['tenant_id']}",
    )
    refresh_token = cfg.get("refresh_token", "")
    if not refresh_token:
        raise RuntimeError(
            "graph.refresh_token is not set in secrets. "
            "Run get_refresh_token.py locally to generate one."
        )
    result = app.acquire_token_by_refresh_token(
        refresh_token=refresh_token,
        scopes=SCOPES,
    )
    if "access_token" not in result:
        raise RuntimeError(f"Graph auth failed: {result.get('error_description')}")
    _token = result["access_token"]
    return _token


def _headers(extra: dict = {}) -> dict:
    return {"Authorization": f"Bearer {get_access_token()}", **extra}


def graph_get_bytes(url: str) -> bytes:
    resp = requests.get(url, headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.content


def graph_put_bytes(url: str, data: bytes, content_type: str = "application/octet-stream") -> dict:
    resp = requests.put(
        url,
        headers=_headers({"Content-Type": content_type}),
        data=data,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def _resolve_share_url(share_url: str) -> dict:
    """Resolve a SharePoint share URL to a drive item (works with Files.ReadWrite)."""
    encoded = base64.urlsafe_b64encode(share_url.encode()).decode().rstrip("=")
    resp = requests.get(
        f"https://graph.microsoft.com/v1.0/shares/u!{encoded}/driveItem",
        headers=_headers({"Accept": "application/json"}),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def download_excel_from_sharepoint(share_url: str) -> bytes:
    item = _resolve_share_url(share_url)
    drive_id = item["parentReference"]["driveId"]
    item_id = item["id"]
    return graph_get_bytes(
        f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"
    )


def upload_excel_to_sharepoint(share_url: str, file_bytes: bytes) -> None:
    item = _resolve_share_url(share_url)
    drive_id = item["parentReference"]["driveId"]
    item_id = item["id"]
    graph_put_bytes(
        f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content",
        file_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def upload_pdf_to_folder(folder_share_url: str, file_bytes: bytes, filename: str) -> str:
    """Upload a PDF into a SharePoint folder resolved from its share URL."""
    item = _resolve_share_url(folder_share_url)
    drive_id = item["parentReference"]["driveId"]
    folder_id = item["id"]
    result = graph_put_bytes(
        f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}:/{filename}:/content",
        file_bytes,
        content_type="application/pdf",
    )
    return result.get("webUrl", "")
