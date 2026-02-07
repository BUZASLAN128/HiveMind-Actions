import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add root to sys.path to import main
sys.path.insert(0, os.getcwd())

import main

class TestMain(unittest.TestCase):

    def setUp(self):
        # Save original environ
        self.original_environ = os.environ.copy()

    def tearDown(self):
        # Restore environ
        os.environ.clear()
        os.environ.update(self.original_environ)

    @patch('main.get_provider')
    def test_missing_jules_api_key(self, mock_get_provider):
        """Test that main raises EnvironmentError if provider raises ValueError for missing key."""
        mock_get_provider.side_effect = ValueError("API Key not configured")

        with self.assertRaises(EnvironmentError) as cm:
            main.main()
        self.assertIn("JULES_API_KEY not found", str(cm.exception))

    @patch('main.get_provider')
    def test_max_prompt_len(self, mock_get_provider):
        """Test that main raises ValueError if prompt is too long."""
        # Mock provider so key check passes if we reach it
        mock_provider_instance = MagicMock()
        mock_get_provider.return_value = mock_provider_instance

        long_prompt = "a" * (main.MAX_PROMPT_LEN + 1)
        with patch.object(sys, 'argv', ['main.py', long_prompt]):
            with self.assertRaises(ValueError) as cm:
                main.main()
            self.assertIn("exceeds limit", str(cm.exception))

    @patch('main.get_provider')
    def test_successful_run(self, mock_get_provider):
        """Test a successful run of main."""

        # Mock provider
        mock_provider_instance = MagicMock()
        mock_provider_instance.generate.return_value = "Test response"
        mock_get_provider.return_value = mock_provider_instance

        # We also need to mock with_retry since main uses it
        with patch('main.with_retry', side_effect=lambda func: func()) as mock_retry:
            with patch.object(sys, 'argv', ['main.py', 'test prompt']):
                # Should not raise exception
                try:
                    main.main()
                except Exception as e:
                    self.fail(f"main() raised {e} unexpectedly!")

            mock_provider_instance.generate.assert_called_with('test prompt')

if __name__ == '__main__':
    unittest.main()
