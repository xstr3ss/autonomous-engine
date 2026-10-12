import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from array_utils import calculate_median


def test_calculate_median_odd_length():
    assert calculate_median([1, 3, 5, 7, 9]) == 5.0


def test_calculate_median_even_length():
    assert calculate_median([1, 2, 3, 4, 5, 6]) == 3.5


def test_calculate_median_single_element():
    assert calculate_median([100]) == 100.0


def test_calculate_median_unsorted_input():
    assert calculate_median([5, 3, 1, 4, 2]) == 3.0


def test_calculate_median_negative_numbers():
    assert calculate_median([-5, -1, -3]) == -3.0


def test_calculate_median_floats():
    assert calculate_median([1.5, 2.5, 3.5]) == 2.5


def test_calculate_median_empty_list_raises():
    with pytest.raises(ValueError):
        calculate_median([])