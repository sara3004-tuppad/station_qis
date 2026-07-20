"""
Single config loader: merges config.yaml (non-sensitive) with
st.secrets (sensitive values injected by Streamlit Cloud or local
.streamlit/secrets.toml).

Usage:
    from utils.config import get_config
    cfg = get_config()
    cfg["graph"]["password"]               # from secrets
    cfg["excel"]["sharepoint_url"]         # from secrets
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

    if "graph" in secrets:
        cfg["graph"] = {
            "tenant_id": secrets["graph"]["tenant_id"],
            "client_id": secrets["graph"]["client_id"],
            "username":  secrets["graph"]["username"],
            "password":  secrets["graph"]["password"],
        }

    if "power_automate" in secrets:
        cfg["power_automate"]["webhook_url"] = secrets["power_automate"].get("webhook_url", "")

    if "sharepoint" in secrets:
        cfg["sharepoint"]["folder_share_url"] = secrets["sharepoint"].get("folder_share_url", "")

    if "excel" in secrets:
        cfg["excel"]["sharepoint_url"] = secrets["excel"]["sharepoint_url"]

    _config = cfg
    return _config
