def calculate_discount(price, discount_percent):
    # BUG: Typo in the variable name!
    return price * (1 - discount_percent)

def test_discount():
    assert calculate_discount(100, 0.20) == 80