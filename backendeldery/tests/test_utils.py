# test_utils.py
from backendeldery.utils import hash_password, obj_to_dict, verify_password
from backendeldery.models import User


def test_hash_password():
    password = "Strong@123"
    hashed_password = hash_password(password)
    assert hashed_password != password


def test_obj_to_dict():
    user = User(id=1, email="test@example.com")
    result = obj_to_dict(user)
    assert result["id"] == 1
    assert result["email"] == "test@example.com"


def test_verify_password_success():
    plain_password = "Strong@123"
    hashed_password = hash_password(plain_password)
    assert verify_password(plain_password, hashed_password) is True


def test_verify_password_failure():
    plain_password = "Strong@123"
    hashed_password = hash_password("DifferentPassword")
    assert verify_password(plain_password, hashed_password) is False


def test_verify_password_none_plain():
    hashed_password = hash_password("Strong@123")
    assert verify_password(None, hashed_password) is False


def test_verify_password_none_hashed():
    assert verify_password("Strong@123", None) is False


def test_verify_password_both_none():
    assert verify_password(None, None) is False


def test_hash_password_none():
    assert hash_password(None) is None