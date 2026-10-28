"""Password-based encryption compatible with the page's Web Crypto code.

Key: PBKDF2-HMAC-SHA256(password, salt, ITERATIONS) -> 256-bit AES-GCM key.
Each payload: {"iv": b64(12 bytes), "ct": b64(ciphertext || 16-byte tag)}.
"""

import base64
import json
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 600_000
CHECK_TEXT = "us-market-news"


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def derive_key(password: str, salt: bytes, iterations: int = ITERATIONS) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return kdf.derive(password.encode())


def encrypt(key: bytes, obj) -> dict:
    iv = os.urandom(12)
    data = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()
    return {"iv": _b64(iv), "ct": _b64(AESGCM(key).encrypt(iv, data, None))}


def decrypt(key: bytes, payload: dict):
    """Return the decrypted object, or raise ValueError on a wrong key."""
    try:
        data = AESGCM(key).decrypt(base64.b64decode(payload["iv"]), base64.b64decode(payload["ct"]), None)
    except InvalidTag as exc:
        raise ValueError("wrong key") from exc
    return json.loads(data)


def new_meta(password: str) -> tuple[dict, bytes]:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    meta = {"v": 1, "kdf": "PBKDF2-SHA256", "iterations": ITERATIONS, "salt": _b64(salt),
            "check": encrypt(key, CHECK_TEXT)}
    return meta, key


def key_for_meta(password: str, meta: dict) -> bytes | None:
    """Derive the key for existing site metadata; None if the password changed."""
    key = derive_key(password, base64.b64decode(meta["salt"]), meta["iterations"])
    try:
        return key if decrypt(key, meta["check"]) == CHECK_TEXT else None
    except ValueError:
        return None
