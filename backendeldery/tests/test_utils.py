# test_utils.py
from backendeldery.utils import hash_password, obj_to_dict
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
