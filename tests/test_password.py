from password import validate_password

def test_valid_password():
    assert validate_password("StrongPass1") == True

def test_too_short():
    assert validate_password("Short1a") == False

def test_no_uppercase():
    assert validate_password("lowercase1") == False

def test_no_digit():
    assert validate_password("NoDigitsHere") == False
