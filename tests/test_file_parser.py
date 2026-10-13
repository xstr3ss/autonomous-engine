import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from file_parser import count_lines
import pytest
import tempfile

def test_count_lines():
    # Create temporary files for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("line1\nline2\nline3\n")
        example_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("single line\n")
        single_path = f.name
    
    try:
        assert count_lines(example_path) == 3, "Test case 1 failed"
        assert count_lines('nonexistent.txt') == 0, "Test case 2 failed"
        assert count_lines('') == 0, "Test case 3 failed"
        assert count_lines(single_path) == 1, "Test case 4 failed"
    finally:
        os.unlink(example_path)
        os.unlink(single_path)
    
    print("All test cases passed!")