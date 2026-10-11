import pandas as pd
import numpy as np
import talib
from __future__ import annotations
from dataclasses import dataclass
from typing import Union
import pytest
from compound_interest import compound_interest
import re
from backend.password import validate_password
from password import validate_password

def generate_signals(df: pd.DataFrame) -> pd.Series:
    """
    Takes a DataFrame with OHLCV data.
    Returns a pandas Series of positions: 1 (Long) or 0 (Flat).
    """
    # Calculate EMA for 12 and 26 periods
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    
    # Implement the crossover logic
    # Long signal when EMA_12 crosses above EMA_26
    crossover_up = (df['EMA_12'] > df['EMA_26']) & (df['EMA_12'].shift(1) <= df['EMA_26'].shift(1))
    
    # Calculate RSI
    df['RSI'] = talib.RSI(df['Close'], timeperiod=14)
    
    # RSI threshold check: RSI must be below 65
    rsi_condition = df['RSI'] < 65
    
    # Combine conditions: Crossover up AND RSI < 65
    signals = np.where(crossover_up & rsi_condition, 1, 0)
    
    return pd.Series(signals, index=df.index)


def compound_interest(
    principal: Number,
    rate: Number,
    times_compounded: int,
    years: Number,
) -> float:
    """
    Calculate the future value of an investment using compound interest.

    Parameters
    ----------
    principal : float
        Initial amount of money. Must be non‑negative.
    rate : float
        Annual interest rate expressed as a decimal (e.g. 0.05 for 5%).
        Must be non‑negative.
    times_compounded : int
        Number of times the interest is compounded per year.
        Must be a positive integer.
    years : float
        Number of years the money is invested or borrowed for.
        Must be non‑negative.

    Returns
    -------
    float
        The amount of money accumulated after the given number of years,
        including interest.

    Raises
    ------
    ValueError
        If any of the input constraints are violated.
    """
    # Input validation
    if principal < 0:
        raise ValueError("Principal must be non‑negative.")
    if rate < 0:
        raise ValueError("Rate must be non‑negative.")
    if times_compounded <= 0:
        raise ValueError("Times compounded must be a positive integer.")
    if years < 0:
        raise ValueError("Years must be non‑negative.")

    # Core formula
    amount = principal * (1 + rate / times_compounded) ** (times_compounded * years)
    return float(amount)


def test_zero_principal():
    """Zero principal should always return zero, regardless of other parameters."""
    assert compound_interest(0, 0.05, 12, 5) == 0.0
    assert compound_interest(0, 0.0, 1, 10) == 0.0


def test_zero_rate():
    """Zero rate should return the principal unchanged."""
    assert compound_interest(1000, 0.0, 12, 5) == 1000.0
    assert compound_interest(500, 0.0, 4, 2) == 500.0


def test_negative_rate():
    """Negative rate is not allowed."""
    with pytest.raises(ValueError, match="Rate must be non‑negative"):
        compound_interest(1000, -0.05, 12, 5)


def test_negative_principal():
    """Negative principal is not allowed."""
    with pytest.raises(ValueError, match="Principal must be non‑negative"):
        compound_interest(-1000, 0.05, 12, 5)


def test_zero_times_compounded():
    """Times compounded must be a positive integer."""
    with pytest.raises(ValueError, match="Times compounded must be a positive integer"):
        compound_interest(1000, 0.05, 0, 5)


def test_negative_years():
    """Negative years is not allowed."""
    with pytest.raises(ValueError, match="Years must be non‑negative"):
        compound_interest(1000, 0.05, 12, -1)


def test_normal_case():
    """Sanity check for a typical scenario."""
    principal = 1000.0
    rate = 0.05          # 5%
    times = 12           # monthly compounding
    years = 5

    expected = principal * (1 + rate / times) ** (times * years)
    result = compound_interest(principal, rate, times, years)
    assert pytest.approx(result, rel=1e-9) == expected


def validate_password(password: str) -> bool:
    """
    Validate a password according to the following rules:
    * At least 8 characters long
    * Contains at least one uppercase letter
    * Contains at least one digit

    Parameters
    ----------
    password : str
        The password string to validate.

    Returns
    -------
    bool
        True if the password satisfies all rules, False otherwise.

    Raises
    ------
    TypeError
        If *password* is not a string.
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    if len(password) < 8:
        return False

    if not re.search(r"[A-Z]", password):
        return False

    if not re.search(r"\d", password):
        return False

    return True


def test_valid_passwords():
    assert validate_password("Password1") is True
    assert validate_password("A1b2c3d4") is True
    assert validate_password("LongPassword123") is True


def test_invalid_passwords():
    """All passwords in INVALID_PASSWORDS should validate to False."""
    for pwd, reason in INVALID_PASSWORDS:
        assert validate_password(pwd) is False, (
            f"Password '{pwd}' should be invalid ({reason})"
        )


def test_non_string_inputs():
    """Passing non-string types should raise TypeError."""
    for bad_input in NON_STRING_INPUTS:
        with pytest.raises(TypeError, match="Password must be a string or bytes instance"):
            validate_password(bad_input)


def test_bytes_input():
    """Bytes input should be decoded and validated correctly."""
    # Valid bytes
    assert validate_password(b"Abcdef12") is True
    # Invalid bytes (no digit)
    assert validate_password(b"Abcdefgh") is False


def test_boundary_length():
    """Password of exactly 8 characters should be accepted if it meets other rules."""
    assert validate_password("Abcdef12") is True
    assert validate_password("Abcdef1") is False  # 7 chars


def test_whitespace_handling():
    """Leading/trailing whitespace should be counted as part of the password."""
    assert validate_password("  Password1") is True  # 10 chars including spaces
    assert validate_password("Password1  ") is True
    assert validate_password("  Password") is False  # no digit


def test_special_characters():
    """Special characters are allowed but not required."""
    assert validate_password("Passw0rd!") is True
    assert validate_password("!@#A1B2") is True
    assert validate_password("!@#abcd") is False  # no uppercase, no digit


def test_edge_case_exact_length():
    """Password exactly 8 characters long with all requirements passes."""
    assert validate_password("A1b2C3d4") is True


def test_edge_case_missing_uppercase_and_digit():
    """Password missing both uppercase and digit fails."""
    assert validate_password("abcdefgh") is False


def test_edge_case_special_characters():
    """Special characters are allowed as long as other rules are met."""
    assert validate_password("A1!@#$%^") is True


def test_invalid_length():
    assert validate_password("Pass1") is False          # 5 chars
    assert validate_password("1234567") is False        # 7 chars


def test_missing_uppercase():
    assert validate_password("password1") is False      # no uppercase
    assert validate_password("12345678") is False       # no letters at all


def test_missing_number():
    assert validate_password("Password") is False       # no digit
    assert validate_password("ABCDEFGH") is False       # no digit


def test_edge_cases():
    # Exactly 8 chars, meets all rules
    assert validate_password("Abcdef12") is True

    # Exactly 8 chars, missing digit
    assert validate_password("Abcdefgh") is False

    # Exactly 8 chars, missing uppercase
    assert validate_password("abcdef12") is False


def test_non_string_input():
    with pytest.raises(TypeError):
        validate_password(12345678)
    with pytest.raises(TypeError):
        validate_password(None)
