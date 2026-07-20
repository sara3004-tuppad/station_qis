"""
Send emails via a Power Automate HTTP-triggered flow.

The flow receives a JSON payload and uses its Office 365 Send Email action.
No Graph API app registration or credentials required — the flow runs under
the flow owner's account.

Power Automate flow setup (one-time):
1. Create a new flow: Trigger = "When an HTTP request is received"
2. Add action: "Send an email (V2)" (Office 365 Outlook connector)
   - To:      @{triggerBody()?['to']}
   - Subject: @{triggerBody()?['subject']}
   - Body:    @{triggerBody()?['body']}         (toggle to HTML mode)
3. Optionally add "Add attachment" if you need PDF support later
4. Save the flow and copy the HTTP POST URL into secrets as power_automate.webhook_url
"""

import requests

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
    """
    sheet: 'quality_clearance' or 'allocation'
    row_data: dict of field values for the completed row
    pdf_bytes / pdf_filename: ignored for now (attach in the flow if needed)
    """
    cfg = get_config()

    if cfg.get("dev_mode"):
        from utils.dev_mock import send_email_mock
        send_email_mock(sheet, row_data, pdf_bytes, pdf_filename)
        return

    webhook_url = cfg.get("power_automate", {}).get("webhook_url", "")
    if not webhook_url:
        raise RuntimeError(
            "power_automate.webhook_url is not set in secrets. "
            "Create a Power Automate HTTP-triggered flow and paste its URL."
        )

    email_cfg = cfg["email"]
    recipients = _all_recipients(cfg)
    site_name = row_data.get("Site Name", row_data.get("QIS No", "Unknown"))
    subject = email_cfg["subject_template"].format(site_name=site_name)

    # Build a plain HTML table from row_data so the flow needs zero templating
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

    payload = {
        "to": ";".join(recipients),   # Power Automate accepts semicolon-separated
        "subject": subject,
        "body": body_html,
        "sheet": sheet,
    }

    resp = requests.post(webhook_url, json=payload, timeout=30)
    resp.raise_for_status()
