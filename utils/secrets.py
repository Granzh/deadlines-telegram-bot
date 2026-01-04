"""
Secure secrets management utilities
"""

import os
import json
import base64
from pathlib import Path
from typing import Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecretsManager:
    """Secure secrets manager with encryption"""

    def __init__(self, key_file: str = ".secrets.key"):
        self.key_file = Path(key_file)
        self.secrets_file = Path(".secrets.enc")
        self._key = None
        self._fernet = None

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        if self._key:
            return self._key

        if self.key_file.exists():
            self._key = self.key_file.read_bytes()
        else:
            # Generate new key
            self._key = Fernet.generate_key()
            self.key_file.write_bytes(self._key)
            # Set restrictive permissions
            self.key_file.chmod(0o600)

        return self._key

    def _get_cipher(self) -> Fernet:
        """Get encryption cipher"""
        if self._fernet:
            return self._fernet

        key = self._get_or_create_key()
        self._fernet = Fernet(key)
        return self._fernet

    def set_secret(self, key: str, value: str) -> None:
        """Store a secret securely"""
        secrets = self._load_secrets()
        secrets[key] = value
        self._save_secrets(secrets)

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret"""
        secrets = self._load_secrets()
        return secrets.get(key)

    def delete_secret(self, key: str) -> bool:
        """Delete a secret"""
        secrets = self._load_secrets()
        if key in secrets:
            del secrets[key]
            self._save_secrets(secrets)
            return True
        return False

    def _load_secrets(self) -> Dict[str, str]:
        """Load decrypted secrets from file"""
        if not self.secrets_file.exists():
            return {}

        try:
            cipher = self._get_cipher()
            encrypted_data = self.secrets_file.read_bytes()
            decrypted_data = cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception:
            # If decryption fails, start fresh
            return {}

    def _save_secrets(self, secrets: Dict[str, str]) -> None:
        """Save secrets to encrypted file"""
        cipher = self._get_cipher()
        data = json.dumps(secrets).encode()
        encrypted_data = cipher.encrypt(data)
        self.secrets_file.write_bytes(encrypted_data)
        # Set restrictive permissions
        self.secrets_file.chmod(0o600)

    def list_secrets(self) -> list[str]:
        """List all secret keys"""
        return list(self._load_secrets().keys())


# Global secrets manager instance
_secrets_manager = None


def get_secrets_manager() -> SecretsManager:
    """Get global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def set_secure_secret(key: str, value: str) -> None:
    """Store a secret securely"""
    get_secrets_manager().set_secret(key, value)


def get_secure_secret(key: str) -> Optional[str]:
    """Retrieve a secret securely"""
    # First try environment variable
    env_value = os.getenv(key)
    if env_value:
        return env_value

    # Then try encrypted storage
    return get_secrets_manager().get_secret(key)


def init_secrets_from_env() -> None:
    """Initialize secrets from environment variables"""
    sensitive_keys = [
        "BOT_TOKEN",
        "DATABASE_URL",
        "API_KEY",
        "SECRET_KEY",
        "PASSWORD",
        "TOKEN",
    ]

    secrets_manager = get_secrets_manager()

    for key in os.environ:
        # Check if this is a sensitive key
        if any(sensitive in key.upper() for sensitive in sensitive_keys):
            value = os.getenv(key)
            if value:
                secrets_manager.set_secret(key, value)
