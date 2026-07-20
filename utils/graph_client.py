import base64
import requests
import yaml
from pathlib import Path

_config = None
_token = None


def _load_config():
    global _config
    if _config is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path) as f:
            _config = yaml.safe_load(f)
    return _config


def get_access_token() -> str:
    import msal
    global _token
    cfg = _load_config()["graph"]
    authority = f"https://login.microsoftonline.com/{cfg['tenant_id']}"
    app = msal.ConfidentialClientApplication(
        client_id=cfg["client_id"],
        client_credential=cfg["client_secret"],
        authority=authority,
    )
    result = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    if "access_token" not in result:
        raise RuntimeError(f"Graph auth failed: {result.get('error_description')}")
    _token = result["access_token"]
    return _token


def graph_get(url: str) -> dict:
    token = get_access_token()
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def graph_get_bytes(url: str) -> bytes:
    token = get_access_token()
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content


def graph_post(url: str, json_body: dict) -> dict:
    token = get_access_token()
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=json_body,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def graph_put_bytes(url: str, data: bytes, content_type: str = "application/octet-stream") -> dict:
    token = get_access_token()
    resp = requests.put(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
        },
        data=data,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def resolve_sharelink_to_drive_item(share_url: str) -> dict:
    """
    Convert a SharePoint share URL into a Graph API drive item object.
    Returns the item metadata including id, parentReference (driveId), and download URL.
    """
    # Graph API requires the share URL to be base64-encoded in a specific way
    encoded = base64.urlsafe_b64encode(share_url.encode()).decode().rstrip("=")
    shares_url = f"https://graph.microsoft.com/v1.0/shares/u!{encoded}/driveItem"
    return graph_get(shares_url)


def download_excel_from_sharepoint(share_url: str) -> bytes:
    """Download the Excel file bytes from a SharePoint share URL."""
    item = resolve_sharelink_to_drive_item(share_url)
    drive_id = item["parentReference"]["driveId"]
    item_id = item["id"]
    download_url = (
        f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"
    )
    return graph_get_bytes(download_url)


def upload_excel_to_sharepoint(share_url: str, file_bytes: bytes) -> None:
    """Upload updated Excel bytes back to the same SharePoint file."""
    item = resolve_sharelink_to_drive_item(share_url)
    drive_id = item["parentReference"]["driveId"]
    item_id = item["id"]
    upload_url = (
        f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"
    )
    graph_put_bytes(upload_url, file_bytes, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
