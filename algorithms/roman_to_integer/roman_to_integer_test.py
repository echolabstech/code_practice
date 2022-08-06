import unittest
from roman_to_integer import Solution

class TestOutput(unittest.TestCase):
    # Symbol       Value
    # I             1
    # V             5
    # X             10
    # L             50
    # C             100
    # D             500
    # M             1000

    def setUp(self):
        self.solution = Solution();

    def test_addition_same_chars(self):
        output = self.solution.romanToInt('III');
        self.assertEqual(output, 3)

    def test_addition_diff_chars(self):
        output = self.solution.romanToInt('LVIII');
        self.assertEqual(output, 58)

    def test_subtraction(self):
        output = self.solution.romanToInt('MCMXCIV');
        self.assertEqual(output, 1994)
        output = self.solution.romanToInt('DCXXI');
        self.assertEqual(output, 621)

if __name__ == '__main__':
    unittest.main()
