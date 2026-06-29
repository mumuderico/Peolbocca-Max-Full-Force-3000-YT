"""
Persistent storage backed by MongoDB Atlas when MONGODB_URI is set,
falling back to local keys.json for local development.
"""
import os

_col = None


def _get_col():
    global _col
    if _col is not None:
        return _col
    uri = os.environ.get("MONGODB_URI", "")
    if not uri:
        try:
            import streamlit as st
            uri = st.secrets.get("MONGODB_URI", "")
        except Exception:
            pass
    if not uri:
        return None
    from pymongo import MongoClient
    _col = MongoClient(uri, serverSelectionTimeoutMS=5000)["streamlit_app"]["users"]
    return _col


# ── Profile (API keys) ────────────────────────────────────────────────────────

def load_profile(profile_id: str) -> dict:
    col = _get_col()
    if col is not None:
        doc = col.find_one({"_id": profile_id}, {"keys": 1})
        return doc.get("keys", {}) if doc else {}
    from modules.user_store import _load_data
    return _load_data().get("profiles", {}).get(profile_id, {})


def save_profile(profile_id: str, keys: dict) -> None:
    col = _get_col()
    if col is not None:
        col.update_one({"_id": profile_id}, {"$set": {"keys": keys}}, upsert=True)
        return
    from modules.user_store import _load_data, _KEYS_PATH
    import json
    data = _load_data()
    data["profiles"][profile_id] = keys
    with open(_KEYS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ── Script files ──────────────────────────────────────────────────────────────

def save_script_to_cloud(profile_id: str, preset: str, filename: str, content: str) -> None:
    col = _get_col()
    if col is None:
        return
    col.update_one(
        {"_id": profile_id},
        {"$set": {f"scripts.{preset}.{filename}": content}},
        upsert=True,
    )


def delete_script_from_cloud(profile_id: str, preset: str, filename: str) -> None:
    col = _get_col()
    if col is None:
        return
    col.update_one(
        {"_id": profile_id},
        {"$unset": {f"scripts.{preset}.{filename}": ""}},
    )


def create_preset_in_cloud(profile_id: str, preset: str) -> None:
    col = _get_col()
    if col is None:
        return
    col.update_one(
        {"_id": profile_id},
        {"$setOnInsert": {f"scripts.{preset}": {}}},
        upsert=True,
    )


def delete_preset_from_cloud(profile_id: str, preset: str) -> None:
    col = _get_col()
    if col is None:
        return
    col.update_one(
        {"_id": profile_id},
        {"$unset": {f"scripts.{preset}": ""}},
    )


def restore_scripts(profile_id: str, scripts_base_dir: str) -> None:
    """Restore a user's script files from MongoDB to disk (called on app startup)."""
    col = _get_col()
    if col is None:
        return
    doc = col.find_one({"_id": profile_id}, {"scripts": 1})
    if not doc or "scripts" not in doc:
        return
    user_dir = os.path.join(scripts_base_dir, profile_id)
    for preset, files in doc["scripts"].items():
        preset_dir = user_dir if preset == "Default" else os.path.join(user_dir, preset)
        os.makedirs(preset_dir, exist_ok=True)
        for filename, content in files.items():
            with open(os.path.join(preset_dir, filename), "w", encoding="utf-8") as f:
                f.write(content)
