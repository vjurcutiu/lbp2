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

def load_all_secrets() -> dict[str, str]:
    """
    Load all secrets from the index and return a dictionary of entry_name -> secret_value.
    """
    secrets = {}
    for entry_name in list_entries():
        secret = fetch_secret(entry_name)
        if secret is not None:
            secrets[entry_name] = secret
    return secrets

class ApiKeyManager:
    """
    Service to manage API keys/secrets loaded from Windows Credentials Manager.
    Loads all secrets at start and can reload after updates.
    """
    def __init__(self):
        self.secrets = load_all_secrets()

    def reload_secrets(self):
        """
        Reload all secrets from the credential store.
        """
        self.secrets = load_all_secrets()

    def get_secret(self, entry_name: str) -> str | None:
        """
        Get a secret by entry name from the loaded secrets.
        """
        return self.secrets.get(entry_name)
