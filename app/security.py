"""
Mini README:
This module provides password hashing, API key generation, and auth helpers.
Security-sensitive functionality is consolidated here for auditability.
"""

import secrets

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)
