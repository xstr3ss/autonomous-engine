import pytest
from password import check_password_strength

def test_check_password_strength():
    assert check_password_strength("password") == "Weak"
    assert check_password_strength("Password123!") == "Strong"
    assert check_password_strength("123456") == "Weak"
    assert check_password_strength("Password123") == "Medium"
    assert check_password_strength("Password1234567890") == "Strong"
