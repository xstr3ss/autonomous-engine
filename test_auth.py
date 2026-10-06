import pytest
from auth_module import authenticate

def test_valid_string():
    assert authenticate("admin") is True, "authenticate() should accept a string"

def test_valid_list():
    assert authenticate(["admin"]) is True, "authenticate() should unpack a list and accept the string"

def test_invalid_type_integer():
    with pytest.raises(TypeError):
        authenticate(12345)
