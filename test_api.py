import unittest
import os

class TestApi(unittest.TestCase):
    def test_api_key(self):
        api_key = os.environ.get('API_KEY')
        self.assertIsNotNone(api_key)

if __name__ == '__main__':
    unittest.main()
