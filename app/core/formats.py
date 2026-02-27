import struct

from app.core.exceptions import FormatError
from app.core.models import PublicKeyBlob, SignedDocument, SignedPublicKeyBlob


_LENGTH = struct.Struct(">I")


def _pack_part(data: bytes) -> bytes:
    return _LENGTH.pack(len(data)) + data


def _read_part(buffer: bytes, offset: int) -> tuple[bytes, int]:
    if offset + _LENGTH.size > len(buffer):
        raise FormatError("Поврежденный формат файла")
    size = _LENGTH.unpack(buffer[offset : offset + _LENGTH.size])[0]
    offset += _LENGTH.size
    end = offset + size
    if end > len(buffer):
        raise FormatError("Поврежденный формат файла")
    return buffer[offset:end], end


def encode_signed_document(document: SignedDocument) -> bytes:
    author_raw = document.author.encode("utf-8")
    text_raw = document.text.encode("utf-8")
    return b"".join(
        [
            _pack_part(author_raw),
            _pack_part(document.signature),
            text_raw,
        ]
    )


def decode_signed_document(payload: bytes) -> SignedDocument:
    author_raw, offset = _read_part(payload, 0)
    signature_raw, offset = _read_part(payload, offset)
    text_raw = payload[offset:]
    try:
        author = author_raw.decode("utf-8")
        text = text_raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise FormatError("Некорректная кодировка документа") from error
    return SignedDocument(author=author, signature=signature_raw, text=text)


def encode_public_key_blob(blob: PublicKeyBlob) -> bytes:
    owner_raw = blob.owner.encode("utf-8")
    return b"".join([_pack_part(owner_raw), _pack_part(blob.key_blob)])


def decode_public_key_blob(payload: bytes) -> PublicKeyBlob:
    owner_raw, offset = _read_part(payload, 0)
    key_blob, offset = _read_part(payload, offset)
    if offset != len(payload):
        raise FormatError("Лишние данные в файле открытого ключа")
    try:
        owner = owner_raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise FormatError("Некорректная кодировка имени владельца ключа") from error
    return PublicKeyBlob(owner=owner, key_blob=key_blob)


def encode_signed_public_key_blob(blob: SignedPublicKeyBlob) -> bytes:
    owner_raw = blob.owner.encode("utf-8")
    return b"".join([_pack_part(owner_raw), _pack_part(blob.key_blob), blob.signature])


def decode_signed_public_key_blob(payload: bytes) -> SignedPublicKeyBlob:
    owner_raw, offset = _read_part(payload, 0)
    key_blob, offset = _read_part(payload, offset)
    signature = payload[offset:]
    if not signature:
        raise FormatError("Отсутствует подпись открытого ключа")
    try:
        owner = owner_raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise FormatError("Некорректная кодировка имени владельца ключа") from error
    return SignedPublicKeyBlob(owner=owner, key_blob=key_blob, signature=signature)
