# secrets_loader.py

import os
from utils.services.api_vault.secrets import fetch_secret, env_service

import os
from dotenv import load_dotenv
from utils.services.api_vault.secrets import fetch_secret, env_service

class SecretsLoader:
    def __init__(self):
        # No in-memory index; we fetch directly from the credential store
        pass

    def load_env(self) -> dict[str, str]:
        """
        Load environment variables from .env file and vault secrets,
        set them into os.environ so that downstream code can pick them up automatically.

        Returns:
            A dict of environment variables that were loaded.
        """
        # Load from .env file first
        load_dotenv()
        print("Loaded environment variables from .env file")

        # Debug: show which service name is being used for keyring
        print(f"Using keyring service: {env_service}")

        # Map your application env-vars to one or more vault aliases
        mapping: dict[str, list[str]] = {
            "OPENAI_API_KEY": ["openai_api_key", "openai"],
            "PINECONE_API_KEY": ["pinecone_api_key"],
            # add more env-var keys and their vault aliases here…
        }

        loaded: dict[str, str] = {}
        # Include all env vars loaded from .env initially
        for key, value in os.environ.items():
            loaded[key] = value

        # Override or add vault secrets to env
        for env_key, aliases in mapping.items():
            for alias in aliases:
                val = fetch_secret(alias)
                if val:
                    if env_key in os.environ:
                        print(f"Overriding existing {env_key} in environment with vault value from alias '{alias}'")
                    else:
                        print(f"Setting {env_key} from vault alias '{alias}'")

                    os.environ[env_key] = val
                    loaded[env_key] = val
                    break

        return loaded
