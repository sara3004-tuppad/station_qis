"""
Single config loader: merges config.yaml (non-sensitive) with
st.secrets (sensitive values injected by Streamlit Cloud or local
.streamlit/secrets.toml).

Usage:
    from utils.config import get_config
    cfg = get_config()
    cfg["power_automate"]["webhook_url"]   # from secrets
    cfg["app"]["title"]                    # from config.yaml
"""

import yaml
from pathlib import Path
import streamlit as st

_config = None


def get_config() -> dict:
    global _config
    if _config is not None:
        return _config

    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    secrets = st.secrets if hasattr(st, "secrets") else {}

    if "power_automate" in secrets:
        for key in ("webhook_url", "excel_download_url", "excel_upload_url", "pdf_upload_url"):
            if key in secrets["power_automate"]:
                cfg["power_automate"][key] = secrets["power_automate"][key]

    _config = cfg
    return _config
