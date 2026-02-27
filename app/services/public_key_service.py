from pathlib import Path

from Crypto.PublicKey import ECC

from app.core.exceptions import FormatError, StorageError
from app.core.formats import (
    decode_public_key_blob,
    decode_signed_public_key_blob,
    encode_public_key_blob,
    encode_signed_public_key_blob,
)
from app.core.models import PublicKeyBlob, SignedPublicKeyBlob
from app.services.crypto_service import CryptoService


class PublicKeyService:
    def __init__(self, storage_dir: Path, crypto: CryptoService) -> None:
        self._storage_dir = storage_dir
        self._crypto = crypto
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def export_public_key(self, owner: str, private_key: ECC.EccKey, destination: Path) -> None:
        blob = self._crypto.export_public_key(private_key)
        payload = encode_public_key_blob(PublicKeyBlob(owner=owner, key_blob=blob))
        destination.write_bytes(payload)

    def import_public_key(self, source: Path, signer_private_key: ECC.EccKey) -> str:
        payload = source.read_bytes()
        owner, blob = self._extract_owner_and_blob(payload)
        data_to_sign = encode_public_key_blob(PublicKeyBlob(owner=owner, key_blob=blob))
        signature = self._crypto.sign(signer_private_key, data_to_sign)
        signed_blob = SignedPublicKeyBlob(owner=owner, key_blob=blob, signature=signature)
        storage_path = self._storage_dir / f"{owner}.spub"
        storage_path.write_bytes(encode_signed_public_key_blob(signed_blob))
        return owner

    def load_and_verify_public_key(self, owner: str, verifier_public_key: ECC.EccKey) -> ECC.EccKey:
        storage_path = self._storage_dir / f"{owner}.spub"
        if not storage_path.exists():
            raise StorageError("Открытый ключ автора не найден в хранилище")
        payload = storage_path.read_bytes()
        signed_blob = decode_signed_public_key_blob(payload)
        data = encode_public_key_blob(PublicKeyBlob(owner=signed_blob.owner, key_blob=signed_blob.key_blob))
        if not self._crypto.verify(verifier_public_key, data, signed_blob.signature):
            raise StorageError("Подпись под открытым ключом не подтверждена")
        if signed_blob.owner != owner:
            raise StorageError("Несоответствие имени владельца открытого ключа")
        return self._crypto.load_public_key(signed_blob.key_blob)

    def _extract_owner_and_blob(self, payload: bytes) -> tuple[str, bytes]:
        try:
            unsigned = decode_public_key_blob(payload)
            return unsigned.owner, unsigned.key_blob
        except FormatError:
            signed = decode_signed_public_key_blob(payload)
            return signed.owner, signed.key_blob
