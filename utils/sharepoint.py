from utils.config import get_config


def upload_pdf(file_bytes: bytes, filename: str) -> str:
    """Upload PDF to SharePoint via Power Automate; returns the file's web URL."""
    if get_config().get("dev_mode"):
        from utils.dev_mock import upload_pdf_mock
        return upload_pdf_mock(file_bytes, filename)
    from utils.pa_client import upload_pdf as pa_upload_pdf
    return pa_upload_pdf(file_bytes, filename)
