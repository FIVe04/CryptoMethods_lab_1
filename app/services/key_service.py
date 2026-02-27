import re
from pathlib import Path

from Crypto.PublicKey import ECC

from app.core.exceptions import StorageError, ValidationError
from app.services.crypto_service import CryptoService


class KeyService:
    def __init__(self, keys_dir: Path, crypto: CryptoService) -> None:
        self._keys_dir = keys_dir
        self._crypto = crypto
        self._keys_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def validate_username(username: str) -> str:
        cleaned = username.strip()
        if not cleaned:
            raise ValidationError("Имя пользователя не задано")
        if len(cleaned) > 64:
            raise ValidationError("Имя пользователя слишком длинное")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", cleaned):
            raise ValidationError("Имя пользователя может содержать только A-Z, a-z, 0-9, ., _, -")
        return cleaned

    def ensure_user(self, username: str) -> ECC.EccKey:
        username = self.validate_username(username)
        key_path = self._private_key_path(username)
        if not key_path.exists():
            key = self._crypto.generate_private_key()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            key_path.write_bytes(self._crypto.export_private_key(key))
            return key
        return self._crypto.load_private_key(key_path.read_bytes())

    def load_private_key(self, username: str) -> ECC.EccKey:
        username = self.validate_username(username)
        key_path = self._private_key_path(username)
        if not key_path.exists():
            raise StorageError("Пара ключей пользователя не найдена")
        return self._crypto.load_private_key(key_path.read_bytes())

    def delete_user_keys(self, username: str) -> None:
        username = self.validate_username(username)
        key_dir = self._keys_dir / username
        if not key_dir.exists():
            raise StorageError("Пара ключей пользователя не найдена")
        for item in key_dir.iterdir():
            if item.is_file():
                item.unlink()
        key_dir.rmdir()

    def _private_key_path(self, username: str) -> Path:
        return self._keys_dir / username / "private.pem"
