import string


def check_password_strength(password: str) -> str:
    """
    Evaluate the strength of a password.

    The algorithm is intentionally simple but covers the cases required by the
    test suite:

    * **Weak** – fewer than 8 characters or fewer than two of the required
      character categories (uppercase, lowercase, digit, special).
    * **Medium** – at least 8 characters and at least two categories.
    * **Strong** – at least 12 characters and at least three of the four
      categories.  A password that meets the length requirement and contains
      all four categories is also considered strong.

    Parameters
    ----------
    password: str
        The password to evaluate.

    Returns
    -------
    str
        One of ``"Weak"``, ``"Medium"``, or ``"Strong"``.
    """
    length = len(password)

    # Character category checks
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in string.punctuation for c in password)

    categories = [has_upper, has_lower, has_digit, has_special]
    category_count = sum(categories)

    # Weak passwords
    if length < 8 or category_count < 2:
        return "Weak"

    # Strong passwords – length >= 12 and at least three categories
    if length >= 12 and category_count >= 3:
        return "Strong"

    # Anything else that passed the weak check is medium
    return "Medium"
