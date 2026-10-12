import pytest
from string_utils import is_palindrome

class TestIsPalindrome:
    def test_simple_palindrome(self):
        assert is_palindrome("racecar") is True

    def test_simple_non_palindrome(self):
        assert is_palindrome("hello") is False

    def test_palindrome_with_spaces(self):
        assert is_palindrome("a man a plan a canal panama") is True

    def test_non_palindrome_with_spaces(self):
        assert is_palindrome("hello world") is False

    def test_case_insensitive_palindrome(self):
        assert is_palindrome("RaceCar") is True

    def test_case_insensitive_non_palindrome(self):
        assert is_palindrome("Hello") is False

    def test_single_character(self):
        assert is_palindrome("a") is True

    def test_empty_string(self):
        assert is_palindrome("") is True

    def test_two_same_characters(self):
        assert is_palindrome("aa") is True

    def test_two_different_characters(self):
        assert is_palindrome("ab") is False

    def test_mixed_case_and_spaces(self):
        assert is_palindrome("A Santa at NASA") is True

    def test_numeric_palindrome(self):
        assert is_palindrome("12321") is True

    def test_numeric_non_palindrome(self):
        assert is_palindrome("12345") is False

    def test_only_spaces(self):
        assert is_palindrome("   ") is True

    def test_palindrome_with_multiple_spaces(self):
        assert is_palindrome("  race  car  ") is True
