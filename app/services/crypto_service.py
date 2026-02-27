from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS

from app.core.exceptions import CryptoError


class CryptoService:
    def generate_private_key(self) -> ECC.EccKey:
        return ECC.generate(curve="P-256")

    def export_private_key(self, key: ECC.EccKey) -> bytes:
        return key.export_key(format="PEM").encode("utf-8")

    def load_private_key(self, payload: bytes) -> ECC.EccKey:
        try:
            return ECC.import_key(payload)
        except (ValueError, TypeError) as error:
            raise CryptoError("Не удалось прочитать закрытый ключ") from error

    def export_public_key(self, key: ECC.EccKey) -> bytes:
        return key.public_key().export_key(format="DER")

    def load_public_key(self, payload: bytes) -> ECC.EccKey:
        try:
            return ECC.import_key(payload)
        except (ValueError, TypeError) as error:
            raise CryptoError("Не удалось прочитать открытый ключ") from error

    def sign(self, private_key: ECC.EccKey, payload: bytes) -> bytes:
        digest = SHA256.new(payload)
        signer = DSS.new(private_key, "fips-186-3")
        try:
            return signer.sign(digest)
        except ValueError as error:
            raise CryptoError("Не удалось подписать данные") from error

    def verify(self, public_key: ECC.EccKey, payload: bytes, signature: bytes) -> bool:
        digest = SHA256.new(payload)
        verifier = DSS.new(public_key, "fips-186-3")
        try:
            verifier.verify(digest, signature)
            return True
        except ValueError:
            return False
