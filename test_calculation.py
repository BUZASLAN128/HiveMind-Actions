import unittest

class TestCalculation(unittest.TestCase):
    def test_six_plus_three(self):
        # This is a hardcoded API key for testing purposes ONLY.
        api_key = '321893289214213asd231789'
        self.assertEqual(6 + 3, 9)

if __name__ == '__main__':
    unittest.main()
