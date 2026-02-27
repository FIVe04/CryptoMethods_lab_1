from pathlib import Path

from app.services.crypto_service import CryptoService
from app.services.document_service import DocumentService
from app.services.key_service import KeyService
from app.services.public_key_service import PublicKeyService
from app.ui.main_window import MainWindow


def build_app(base_dir: Path) -> MainWindow:
    data_dir = base_dir / "data"
    keys_dir = data_dir / "keys"
    pk_dir = data_dir / "pk"

    crypto_service = CryptoService()
    key_service = KeyService(keys_dir=keys_dir, crypto=crypto_service)
    public_key_service = PublicKeyService(storage_dir=pk_dir, crypto=crypto_service)
    document_service = DocumentService(crypto=crypto_service)

    return MainWindow(
        key_service=key_service,
        public_key_service=public_key_service,
        document_service=document_service,
    )
