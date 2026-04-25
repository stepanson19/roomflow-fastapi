from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    database_url: str
    secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int


@lru_cache
def get_settings() -> Settings:
    secret_key = os.getenv("ROOMFLOW_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("ROOMFLOW_SECRET_KEY is required")
    return Settings(
        database_url=os.getenv("ROOMFLOW_DATABASE_URL", "sqlite:///./roomflow.db"),
        secret_key=secret_key,
        jwt_algorithm=os.getenv("ROOMFLOW_JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("ROOMFLOW_TOKEN_MINUTES", "120")),
    )
