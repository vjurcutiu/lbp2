# secrets_loader.py

import os
from utils.services.api_vault.secrets import ApiKeyManager

class SecretsLoader:
    def __init__(self):
        self._manager = ApiKeyManager()

    def load_env(self):
        """
        Reloads vault secrets and sets them into os.environ so that
        downstream code (e.g. OpenAI()) can pick them up automatically.
        """
        # Bring in any new/updated secrets
        self._manager.reload_secrets()

        # List out all the secrets you need
        mapping = {
            "OPENAI_API_KEY": ["openai_api_key", "openai"],
            "PINECONE_API_KEY" :  ["pinecone_api_key"]
            # add more env‑var keys and their vault aliases here…
        }

        for env_key, aliases in mapping.items():
            # Find the first alias that exists in the vault
            for alias in aliases:
                val = self._manager.get_secret(alias)
                if val:
                    # Only set it if it's not already in the env,
                    # so you don’t clobber a manual override
                    os.environ.setdefault(env_key, val)
                    break

        # Optionally return the raw dict of values too
        return {k: os.environ[k] for k in mapping if k in os.environ}
