"""
Single config loader: merges config.yaml (non-sensitive) with
st.secrets (sensitive values injected by Streamlit Cloud or local
.streamlit/secrets.toml).

Usage:
    from utils.config import get_config
    cfg = get_config()
    cfg["graph"]["client_secret"]   # from secrets
    cfg["app"]["title"]             # from config.yaml
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

    # Overlay secrets — works both in Streamlit Cloud and local secrets.toml
    secrets = st.secrets if hasattr(st, "secrets") else {}

    if "graph" in secrets:
        cfg["graph"] = {
            "tenant_id": secrets["graph"]["tenant_id"],
            "client_id": secrets["graph"]["client_id"],
            "client_secret": secrets["graph"]["client_secret"],
        }

    if "sharepoint" in secrets:
        cfg["sharepoint"]["site_url"] = secrets["sharepoint"].get("site_url", "")

    if "excel" in secrets:
        cfg["excel"]["sharepoint_url"] = secrets["excel"]["sharepoint_url"]

    _config = cfg
    return _config
