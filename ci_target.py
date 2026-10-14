def calculate_discount(price: float, discount_percent: float) -> float:
    """Returns the final price after applying discount_percent."""
    # BUG: Adding the discount instead of subtracting it!
    return price + (price * (discount_percent / 100.0))
