from dataclasses import dataclass


@dataclass(slots=True)
class SignedDocument:
    author: str
    signature: bytes
    text: str


@dataclass(slots=True)
class PublicKeyBlob:
    owner: str
    key_blob: bytes


@dataclass(slots=True)
class SignedPublicKeyBlob:
    owner: str
    key_blob: bytes
    signature: bytes
