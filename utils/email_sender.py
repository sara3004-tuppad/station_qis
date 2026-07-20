"""
Send emails via Office 365 SMTP.

Uses the same M365 credentials already in secrets (graph.username / graph.password).
No Power Automate, no admin consent, no premium license required.

Office 365 SMTP settings:
  Host: smtp.office365.com
  Port: 587 (STARTTLS)
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from utils.config import get_config


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
    cfg = get_config()

    if cfg.get("dev_mode"):
        from utils.dev_mock import send_email_mock
        send_email_mock(sheet, row_data, pdf_bytes, pdf_filename)
        return

    graph_cfg = cfg.get("graph", {})
    sender = graph_cfg.get("username", "")
    password = graph_cfg.get("password", "")
    if not sender or not password:
        raise RuntimeError("graph.username and graph.password must be set in secrets to send email.")

    recipients = _all_recipients(cfg)
    if not recipients:
        return

    site_name = row_data.get("Site Name", row_data.get("QIS No", "Unknown"))
    subject = cfg["email"]["subject_template"].format(site_name=site_name)

    rows_html = "".join(
        f"<tr><td style='padding:4px 8px;border:1px solid #ddd'><b>{k}</b></td>"
        f"<td style='padding:4px 8px;border:1px solid #ddd'>{v}</td></tr>"
        for k, v in row_data.items()
        if v not in (None, "", float("nan"))
    )
    body_html = f"""
    <p>The following record has been completed in the Station QIS tracker.</p>
    <table style='border-collapse:collapse;font-family:sans-serif;font-size:14px'>
      {rows_html}
    </table>
    <p style='color:#888;font-size:12px'>Sent automatically by Station QIS Tracker</p>
    """

    msg = MIMEMultipart("mixed")
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))

    if pdf_bytes and pdf_filename:
        part = MIMEBase("application", "pdf")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{pdf_filename}"')
        msg.attach(part)

    with smtplib.SMTP("smtp.office365.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipients, msg.as_string())
