import sys
import os
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# Add the directory containing the module to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_utils import load_prompt_template

class TestAIUtils(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_prompt_template_success(self):
        # Use real prompt file from the repo
        prompt_path = Path(__file__).parent.parent / "prompts" / "swarm_analyzer.prompt"
        result = load_prompt_template(prompt_path)

        # Verify content matches what we expect
        self.assertIn("HiveMind Analyst Agent", result)
        self.assertIn("Project Rules:", result)

    def test_load_prompt_template_not_found(self):
        prompt_file = self.test_dir / "non_existent.txt"
        with self.assertRaises(FileNotFoundError):
            load_prompt_template(prompt_file)

    def test_load_prompt_template_empty(self):
        prompt_file = self.test_dir / "empty_prompt.txt"
        prompt_file.write_text("", encoding="utf-8")

        result = load_prompt_template(prompt_file)
        self.assertEqual(result, "")

    def test_load_prompt_template_unicode(self):
        prompt_file = self.test_dir / "unicode_prompt.txt"
        content = "Test prompt with unicode: 🧪✨"
        prompt_file.write_text(content, encoding="utf-8")

        result = load_prompt_template(prompt_file)
        self.assertEqual(result, content)

    def test_load_prompt_template_io_error(self):
        # Create a mock Path object that raises IOError when read_text is called
        mock_path = MagicMock(spec=Path)
        mock_path.read_text.side_effect = IOError("Mock IO Error")
        # Ensure it behaves like a path in f-strings for logging
        mock_path.__str__.return_value = "/mock/path/to/error"

        with self.assertRaises(IOError):
            load_prompt_template(mock_path)

if __name__ == '__main__':
    unittest.main()
