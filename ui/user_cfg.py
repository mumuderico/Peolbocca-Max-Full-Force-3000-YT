import os
import streamlit as st
import config


def get_key(name: str) -> str:
    """Return a config value, preferring the session-loaded user profile over module defaults."""
    user_keys = st.session_state.get("user_keys", {})
    if name in user_keys:
        return user_keys[name]
    return getattr(config, name, "")


def get_scripts_dir() -> str:
    """Return the per-user scripts directory when a profile is active, else the global default."""
    active = st.session_state.get("active_profile")
    if active:
        return os.path.join(config.SCRIPTS_DIR, active)
    return config.SCRIPTS_DIR
