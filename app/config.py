import os
from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    
    # Database settings
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "")
    DB_NAME = os.getenv("DB_NAME", "foodlink_db")

    # Address validation (Canada Post AddressComplete)
    CANADA_POST_API_KEY = os.getenv("CANADA_POST_API_KEY", "")
    CANADA_POST_API_BASE = os.getenv(
        "CANADA_POST_API_BASE",
        "https://ws1.postescanadapost.ca/AddressComplete/Interactive",
    )
    ADDRESS_VALIDATION_ALLOW_FALLBACK = _as_bool(
        os.getenv("ADDRESS_VALIDATION_ALLOW_FALLBACK"), default=False
    )

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _as_bool(os.getenv("SESSION_COOKIE_SECURE"), default=False)
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
