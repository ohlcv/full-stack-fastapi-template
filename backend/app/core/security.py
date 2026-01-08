import warnings
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Suppress bcrypt version warning from passlib
# This is a known issue: passlib tries to read bcrypt.__about__.__version__
# but bcrypt 4.3.0 doesn't have this attribute. It doesn't affect functionality.
# We suppress warnings when creating CryptContext
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=".*bcrypt.*__about__.*")
    warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")
    warnings.filterwarnings("ignore", message=".*trapped.*error reading bcrypt version.*")
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
