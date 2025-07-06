from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext

from src.utils.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check hashed password
    :param plain_password:
    :param hashed_password:
    :return: bool True or False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate hashed password
    :param password:
    :return: string hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generate access token
    :param data: dict data
    :param expires_delta: Optional, timedelta for token life time
    :return: string token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    token = jwt.encode(
        to_encode, settings.secret_key.get_secret_value(), algorithm=settings.algorithm
    )
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode token to dict
    :param token:
    :return:
    """
    payload = jwt.decode(
        token, settings.secret_key.get_secret_value(), algorithms=[settings.algorithm]
    )
    return payload
