# secrets.py
import keyring
import os
import json

# A single logical “service” name for all RAG‑chat secrets
SERVICE = "rag-chat"

def _make_username(entry_name: str) -> str:
    """
    Internal: canonicalize a key name into a username for keyring.
    e.g. entry_name="openai" -> username="rag-chat/openai"
    """
    return f"{SERVICE}/{entry_name}"

def store_secret(entry_name: str, secret_value: str) -> None:
    """
    Store (or update) a secret under the given entry name.
    entry_name: e.g. "openai", "pinecone-key", "pinecone-index"
    """
    username = _make_username(entry_name)
    keyring.set_password(SERVICE, username, secret_value)

def fetch_secret(entry_name: str) -> str | None:
    """
    Retrieve a secret by entry name. Returns None if not set.
    """
    username = _make_username(entry_name)
    return keyring.get_password(SERVICE, username)

def delete_secret(entry_name: str) -> None:
    """
    Remove a stored secret (if you need to rotate or clean up).
    """
    username = _make_username(entry_name)
    try:
        keyring.delete_password(SERVICE, username)
    except keyring.errors.PasswordDeleteError:
        pass  # already gone

def list_entries() -> list[str]:
    """
    List all entry names currently stored under this service.
    Note: keyring doesn’t have a native “list all keys” API on every
    backend, so this method uses an env‑backed index as a fallback.
    """
    # We maintain an index of entries in an ENV var, JSON‑encoded.
    raw = os.environ.get(f"{SERVICE}_INDEX")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []

def _update_index(entry_name: str, adding: bool) -> None:
    """
    Internal: update the index of known entry names.
    """
    entries = set(list_entries())
    if adding:
        entries.add(entry_name)
    else:
        entries.discard(entry_name)
    os.environ[f"{SERVICE}_INDEX"] = json.dumps(sorted(entries))

def add_secret(entry_name: str, secret_value: str) -> None:
    """
    Public API: store a secret and update index.
    """
    store_secret(entry_name, secret_value)
    _update_index(entry_name, adding=True)

def remove_secret(entry_name: str) -> None:
    """
    Public API: delete a secret and update index.
    """
    delete_secret(entry_name)
    _update_index(entry_name, adding=False)
