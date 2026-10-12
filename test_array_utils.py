import pytest
from array_utils import max_difference


class TestMaxDifference:
    def test_two_elements(self):
        assert max_difference([1, 2]) == 1.0

    def test_multiple_elements(self):
        assert max_difference([1, 5, 3, 2, 4]) == 4.0

    def test_negative_numbers(self):
        assert max_difference([-5, -1, -3]) == 4.0

    def test_mixed_positive_negative(self):
        assert max_difference([-10, 0, 10]) == 20.0

    def test_all_same_elements(self):
        assert max_difference([5, 5, 5, 5]) == 0.0

    def test_floats(self):
        assert max_difference([1.1, 2.2, 3.3]) == pytest.approx(2.2)

    def test_single_element_raises(self):
        with pytest.raises(ValueError, match="List must have at least 2 items"):
            max_difference([1])

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="List must have at least 2 items"):
            max_difference([])

    def test_returns_float(self):
        result = max_difference([1, 2])
        assert isinstance(result, float)