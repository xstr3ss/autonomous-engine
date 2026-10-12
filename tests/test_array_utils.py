import sys
import os
import pytest

# Add the parent directory to the path so we can import array_utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from array_utils import max_difference

def test_max_difference():
    assert max_difference([1, 2, 3, 4, 5]) == 4
    assert max_difference([5, 4, 3, 2, 1]) == 4
    assert max_difference([10, 20, 30, 40, 50]) == 40
    assert max_difference([-1, -2, -3, -4, -5]) == 4
    assert max_difference([100]) == 0
    assert max_difference([]) == 0
    assert max_difference([1]) == 0
    assert max_difference([1, 1]) == 0
