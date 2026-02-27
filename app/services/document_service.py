from pathlib import Path

from Crypto.PublicKey import ECC

from app.core.formats import decode_signed_document, encode_signed_document
from app.core.models import SignedDocument
from app.services.crypto_service import CryptoService


class DocumentService:
    def __init__(self, crypto: CryptoService) -> None:
        self._crypto = crypto

    def save_document(self, destination: Path, author: str, private_key: ECC.EccKey, text: str) -> None:
        text_bytes = text.encode("utf-8")
        signature = self._crypto.sign(private_key, text_bytes)
        payload = encode_signed_document(SignedDocument(author=author, signature=signature, text=text))
        destination.write_bytes(payload)

    def load_document(self, source: Path) -> SignedDocument:
        payload = source.read_bytes()
        return decode_signed_document(payload)

    def verify_document(self, document: SignedDocument, author_public_key: ECC.EccKey) -> bool:
        return self._crypto.verify(author_public_key, document.text.encode("utf-8"), document.signature)
