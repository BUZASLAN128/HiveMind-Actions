import unittest

class TestCalculation(unittest.TestCase):
    """A collection of tests for basic calculations."""

    def test_six_plus_three(self) -> None:
        """Tests that the sum of 6 and 3 is equal to 9."""
        self.assertEqual(6 + 3, 9)

if __name__ == '__main__':
    unittest.main()
