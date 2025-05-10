# secrets.py
import keyring
import os
import json
import re

# A single logical “service” name for all RAG‑chat secrets
env_service = os.getenv("SERVICE_NAME", "LEXBOT-PRO")

def _normalize_entry(entry_name: str) -> str:
    """
    Internal: normalize entry names to uppercase, underscores, no spaces.
    e.g. "OpenAI Key" -> "OPENAI_KEY"
    """
    return re.sub(r"\W+", "_", entry_name.strip()).upper()


def _make_username(entry_name: str) -> str:
    """
    Internal: canonicalize entry name into a username for keyring.
    """
    return _normalize_entry(entry_name)



def store_secret(entry_name: str, secret_value: str) -> None:
    """
    Store (or update) a secret under the given entry name.
    entry_name: e.g. "openai", "pinecone-key", "pinecone index"
    """
    username = _make_username(entry_name)
    print("Saving keyring entry:", username, "@", env_service)
    keyring.set_password(env_service, username, secret_value)


def fetch_secret(entry_name: str) -> str | None:
    """
    Retrieve a secret by entry name. Returns None if not set.
    """
    username = _make_username(entry_name)
    return keyring.get_password(env_service, username)


def delete_secret(entry_name: str) -> None:
    """
    Remove a stored secret (if you need to rotate or clean up).
    """
    username = _make_username(entry_name)
    try:
        keyring.delete_password(env_service, username)
    except keyring.errors.PasswordDeleteError:
        pass  # already gone


def list_entries() -> list[str]:
    """
    List all entry names currently stored under this service.
    Uses an ENV‑backed JSON index as fallback.
    """
    raw = os.environ.get(f"{env_service}_INDEX")
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
    normalized = _normalize_entry(entry_name)
    if adding:
        entries.add(normalized)
    else:
        entries.discard(normalized)
    os.environ[f"{env_service}_INDEX"] = json.dumps(sorted(entries))


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
    Load all secrets from the index and return a dict of entry_name -> secret_value.
    """
    secrets = {}
    for entry_name in list_entries():
        secret = fetch_secret(entry_name)
        if secret is not None:
            secrets[entry_name] = secret
    return secrets


class ApiKeyManager:
    """
    Service to manage API keys/secrets loaded from OS credential store.
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
        normalized = _normalize_entry(entry_name)
        return self.secrets.get(normalized)
