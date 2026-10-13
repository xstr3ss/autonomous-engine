import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from safe_math import divide_elements


class TestDivideElements:
    """Test suite for the divide_elements function."""

    def test_divide_positive_numbers(self):
        """Test dividing two positive numbers."""
        result = divide_elements(10.0, 2.0)
        assert result == 5.0

    def test_divide_negative_numbers(self):
        """Test dividing two negative numbers."""
        result = divide_elements(-10.0, -2.0)
        assert result == 5.0

    def test_divide_mixed_signs(self):
        """Test dividing numbers with different signs."""
        result = divide_elements(10.0, -2.0)
        assert result == -5.0
        result = divide_elements(-10.0, 2.0)
        assert result == -5.0

    def test_divide_by_one(self):
        """Test dividing by one."""
        result = divide_elements(5.0, 1.0)
        assert result == 5.0

    def test_divide_zero_by_number(self):
        """Test dividing zero by a non-zero number."""
        result = divide_elements(0.0, 5.0)
        assert result == 0.0

    def test_divide_by_zero_raises_error(self):
        """Test that dividing by zero raises ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError, match="Cannot divide by zero."):
            divide_elements(5.0, 0.0)

    def test_divide_zero_by_zero_raises_error(self):
        """Test that dividing zero by zero raises ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError, match="Cannot divide by zero."):
            divide_elements(0.0, 0.0)

    def test_divide_float_precision(self):
        """Test division with floating point precision."""
        result = divide_elements(1.0, 3.0)
        assert result == pytest.approx(0.3333333333333333)

    def test_divide_large_numbers(self):
        """Test dividing large numbers."""
        result = divide_elements(1e10, 1e5)
        assert result == pytest.approx(1e5)

    def test_divide_small_numbers(self):
        """Test dividing very small numbers."""
        result = divide_elements(1e-10, 1e-5)
        assert result == pytest.approx(1e-5)