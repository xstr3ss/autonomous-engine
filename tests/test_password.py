import pytest
from backend.password import validate_password
from backend.main import app
from fastapi.testclient import TestClient

def test_valid_password():
    assert validate_password("Password123") == True
    assert validate_password("Password12") == False
    assert validate_password("password123") == False
    assert validate_password("PASSWORD123") == False
    assert validate_password("password") == False
    assert validate_password("P") == False
    assert validate_password("12345678") == False
    assert validate_password("P@ssw0rd") == True

def test_password_too_short():
    assert validate_password("Pass") == False

def test_no_uppercase():
    # No uppercase letter
    assert not validate_password("password123"), "Failed on password without uppercase"

def test_no_digit():
    assert validate_password("Password") == False

def test_valid_password_with_special_char():
    assert validate_password("Password!123") == True

def test_valid_password_with_whitespace():
    assert validate_password("Password 123") == True

def test_valid_password_with_mixed_case():
    assert validate_password("pASSWORD123") == True

def test_valid_password_with_numbers_only():
    assert validate_password("12345678") == False

def test_valid_password_with_uppercase_only():
    assert validate_password("PASSWORD") == False

def test_valid_password_with_digit_only():
    assert validate_password("12345678") == False

def test_valid_password_with_special_char_only():
    assert validate_password("!@#$%^&*()") == False

def test_valid_password_with_whitespace_only():
    assert validate_password("   ") == False

def test_valid_password_with_empty_string():
    assert validate_password("") == False


def test_validate_password():
    client = TestClient(app)

    # Test valid passwords
    valid_passwords = [
        "Password123",
        "P@ssw0rd",
        "12345678",
        "ValidPassword1",
        "AnotherValid123"
    ]

    for password in valid_passwords:
        response = client.post("/validate_password", json={"password": password})
        assert response.status_code == 200
        assert response.json() == {"message": "Password is valid"}

    # Test invalid passwords
    invalid_passwords = [
        "short",
        "noUpper",
        "noNum",
        "1234567",
        "password",
        "P@ssw0rd!",
        "1234567890"
    ]

    for password in invalid_passwords:
        response = client.post("/validate_password", json={"password": password})
        assert response.status_code == 400
        assert response.json() == {"message": "Password is invalid"}


def test_valid_passwords():
    # Valid passwords
    valid_passwords = [
        "Password123",
        "P@ssw0rd",
        "12345678",
        "A1B2C3D4",
        "Password1234567890"
    ]

    for password in valid_passwords:
        assert validate_password(password), f"Failed on valid password: {password}"


def test_invalid_passwords():
    # Invalid passwords
    invalid_passwords = [
        "pass",
        "1234567",
        "Password",
        "P@ssw0rd1",
        "A1B2C3D45"
    ]

    for password in invalid_passwords:
        assert not validate_password(password), f"Failed on invalid password: {password}"


def test_empty_password():
    # Empty password
    assert not validate_password(""), "Failed on empty password"


def test_short_password():
    # Short password
    assert not validate_password("abc"), "Failed on short password"


def test_no_number():
    # No number
    assert not validate_password("Password"), "Failed on password without number"


def test_no_special_characters():
    # No special characters
    assert not validate_password("Password123"), "Failed on password without special characters"


def test_invalid_password_too_short():
    with pytest.raises(ValueError):
        validate_password("Pass")


def test_invalid_password_no_uppercase():
    with pytest.raises(ValueError):
        validate_password("password123")


def test_invalid_password_no_number():
    with pytest.raises(ValueError):
        validate_password("Password")


def test_invalid_password_no_special_characters():
    response = client.post("/validate_password", json={"password": "Password123"})
    assert response.status_code == 400
    assert response.json() == {"message": "Password must contain at least one special character"}


def test_invalid_password_only_whitespace():
    response = client.post("/validate_password", json={"password": "   "})
    assert response.status_code == 400
    assert response.json() == {"message": "Password must be at least 8 characters long"}


def test_invalid_password_empty_string():
    response = client.post("/validate_password", json={"password": ""})
    assert response.status_code == 400
    assert response.json() == {"message": "Password must be at least 8 characters long"}


def test_invalid_password_no_special_char():
    with pytest.raises(ValueError):
        validate_password("Password123")


def test_invalid_password_no_lowercase():
    with pytest.raises(ValueError):
        validate_password("PASSWORD123")


def test_edge_cases():
    assert validate_password("") == False
    assert validate_password("a") == False
    assert validate_password("A") == False
    assert validate_password("1") == False
    assert validate_password("1234567") == False
    assert validate_password("Password123!") == True
    assert validate_password("Password123@") == True
    assert validate_password("Password123#") == True
    assert validate_password("Password123$") == True
    assert validate_password("Password123%") == True
    assert validate_password("Password123^") == True
    assert validate_password("Password123&") == True
    assert validate_password("Password123*") == True
    assert validate_password("Password123+") == True
    assert validate_password("Password123=") == True
    assert validate_password("Password123-") == True
    assert validate_password("Password123_") == True
    assert validate_password("Password123.") == True
    assert validate_password("Password123,") == True
    assert validate_password("Password123/") == True
    assert validate_password("Password123\\") == True
    assert validate_password("Password123|") == True
    assert validate_password("Password123;") == True
    assert validate_password("Password123:") == True
    assert validate_password("Password123\"") == True
    assert validate_password("Password123\'") == True
    assert validate_password("Password123`") == True
    assert validate_password("Password123~") == True
