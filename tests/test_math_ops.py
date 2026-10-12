import pytest
from math_ops import multiply_numbers


class TestMultiplyNumbers:
    def test_positive_numbers(self):
        assert multiply_numbers(2, 3) == 6

    def test_negative_numbers(self):
        assert multiply_numbers(-2, 3) == -6
        assert multiply_numbers(2, -3) == -6
        assert multiply_numbers(-2, -3) == 6

    def test_zero(self):
        assert multiply_numbers(0, 5) == 0
        assert multiply_numbers(5, 0) == 0
        assert multiply_numbers(0, 0) == 0

    def test_floats(self):
        assert multiply_numbers(1.5, 2) == 3.0
        assert multiply_numbers(0.1, 0.2) == pytest.approx(0.02)

    def test_large_numbers(self):
        assert multiply_numbers(1e6, 1e6) == 1e12

    def test_one_identity(self):
        assert multiply_numbers(1, 5) == 5
        assert multiply_numbers(5, 1) == 5
