import unittest

class TestApi(unittest.TestCase):
    def test_api_key(self):
        # WARNING: Storing API keys directly in code is a security risk!
        api_key = '321893289214213asd231789'
        self.assertIsInstance(api_key, str)

if __name__ == '__main__':
    unittest.main()
