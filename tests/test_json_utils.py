import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from json_utils import load_json

def test_load_json():
    test_json_string = '{"name": "John", "age": 30}'
    expected_output = {'name': "John", 'age': 30}
    assert load_json(test_json_string) == expected_output