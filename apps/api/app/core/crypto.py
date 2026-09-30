"""Encryption-at-rest for `blog_platforms.password_encrypted` — see
docs/DATABASE_SCHEMA.md ("باید با KMS/Fernet رمزنگاری شود، هرگز plain-text").

Fernet (symmetric, authenticated) rather than a real KMS: this is a
single-tenant internal tool storing a handful of blog-login passwords, not
a multi-tenant secrets store — reaching for AWS KMS/Vault here would be the
"غیرضروری" complexity the project explicitly avoids. Revisit if this ever
needs per-tenant keys or key rotation without a maintenance window.
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

_fernet = Fernet(settings.FERNET_KEY.encode("utf-8"))


class DecryptionError(Exception):
    pass


def encrypt_secret(plain_text: str) -> str:
    return _fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    try:
        return _fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise DecryptionError("Stored credential could not be decrypted (wrong FERNET_KEY?)") from exc
