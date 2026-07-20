import base64
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from utils.graph_client import graph_post


def _load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def _render_body(template_file: str, context: dict) -> str:
    templates_dir = Path(__file__).parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
    tmpl = env.get_template(Path(template_file).name)
    return tmpl.render(**context)


def _all_recipients(cfg: dict) -> list[str]:
    r = cfg["email"]["recipients"]
    return list({
        addr
        for group in r.values()
        for addr in group
        if addr
    })


def send_completion_email(
    sheet: str,
    row_data: dict,
    pdf_bytes: bytes | None = None,
    pdf_filename: str | None = None,
):
    """
    sheet: 'quality_clearance' or 'allocation'
    row_data: dict of all field values for the completed row
    pdf_bytes / pdf_filename: optional invoice attachment
    """
    cfg = _load_config()
    if cfg.get("dev_mode"):
        from utils.dev_mock import send_email_mock
        send_email_mock(sheet, row_data, pdf_bytes, pdf_filename)
        return
    email_cfg = cfg["email"]
    sender = email_cfg["sender"]
    recipients = _all_recipients(cfg)

    site_name = row_data.get("Site Name", row_data.get("QIS No", "Unknown"))
    subject = email_cfg["subject_template"].format(site_name=site_name)

    html_body = _render_body(
        email_cfg["email_template"],
        {"sheet": sheet, "row": row_data, "site_name": site_name},
    )

    to_list = [{"emailAddress": {"address": addr}} for addr in recipients]

    message: dict = {
        "subject": subject,
        "body": {"contentType": "HTML", "content": html_body},
        "toRecipients": to_list,
    }

    if pdf_bytes and pdf_filename:
        encoded = base64.b64encode(pdf_bytes).decode()
        message["attachments"] = [
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": pdf_filename,
                "contentType": "application/pdf",
                "contentBytes": encoded,
            }
        ]

    payload = {"message": message, "saveToSentItems": True}
    graph_post(
        f"https://graph.microsoft.com/v1.0/users/{sender}/sendMail",
        payload,
    )
