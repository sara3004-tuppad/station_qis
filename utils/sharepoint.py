from utils.config import get_config


def upload_pdf(file_bytes: bytes, filename: str) -> str:
    """Upload PDF to SharePoint invoice folder; returns the file's web URL."""
    if get_config().get("dev_mode"):
        from utils.dev_mock import upload_pdf_mock
        return upload_pdf_mock(file_bytes, filename)
    from utils.graph_client import upload_pdf_to_folder
    folder_share_url = get_config()["sharepoint"]["folder_share_url"]
    return upload_pdf_to_folder(folder_share_url, file_bytes, filename)
