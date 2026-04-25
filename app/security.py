from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

from jose import JWTError, jwt

from app.settings import get_settings


HASH_NAME = "sha256"
HASH_ITERATIONS = 260000


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        algorithm, iterations, salt, stored_digest = hashed_password.split("$", 3)
    except ValueError:
        return False
    if algorithm != f"pbkdf2_{HASH_NAME}":
        return False
    digest = hashlib.pbkdf2_hmac(
        HASH_NAME,
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(digest, stored_digest)


def get_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        HASH_NAME,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        HASH_ITERATIONS,
    ).hex()
    return f"pbkdf2_{HASH_NAME}${HASH_ITERATIONS}${salt}${digest}"


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expires_at = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, str]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("invalid token") from exc
