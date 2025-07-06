import jwt.exceptions
import pytest

from src.auth.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hash():
    plain_pass = "test_password"
    hashed_pass = get_password_hash(plain_pass)
    wrong_hashed_pass = get_password_hash(plain_pass + "test")

    assert plain_pass != hashed_pass
    assert verify_password(plain_pass, hashed_pass) is True
    assert verify_password(plain_pass, wrong_hashed_pass) is False


def test_access_token():
    user_id = 1
    data = {"user_id": user_id}

    access_token = create_access_token(data)
    decode_data = decode_access_token(access_token)

    assert type(access_token) is str
    assert decode_data.get("user_id") == user_id

    with pytest.raises(jwt.exceptions.DecodeError):
        decode_access_token(access_token + "test")
