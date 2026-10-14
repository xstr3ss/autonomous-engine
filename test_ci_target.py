import unittest
from ci_target import calculate_discount

class TestDiscount(unittest.TestCase):
    def test_twenty_percent_discount(self):
        self.assertEqual(calculate_discount(100.0, 20.0), 80.0)

if __name__ == "__main__":
    unittest.main()
