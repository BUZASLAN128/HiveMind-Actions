import shutil
from pathlib import Path
import unittest
import tempfile
from swarm_analyzer import get_codebase_context

class TestSwarmAnalyzer(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.priority_dirs = ['src']
        (self.test_dir / 'src').mkdir()
        (self.test_dir / 'other').mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, path, content="content"):
        p = self.test_dir / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
        return p

    def test_basic_scan(self):
        self.create_file("src/main.py", "print('hello')")
        self.create_file("src/utils.js", "console.log('hello')")
        self.create_file("other/ignore.py", "ignored")

        context = get_codebase_context(
            self.test_dir,
            max_files=10,
            priority_dirs=['src'],
            extensions={'.py', '.js'}
        )

        self.assertIn("src/main.py", context)
        self.assertIn("src/utils.js", context)
        self.assertNotIn("other/ignore.py", context)

    def test_max_files(self):
        for i in range(5):
            self.create_file(f"src/file{i}.py", f"content {i}")

        context = get_codebase_context(
            self.test_dir,
            max_files=3,
            priority_dirs=['src'],
            extensions={'.py'}
        )

        count = context.count("### src/file")
        self.assertEqual(count, 3)

    def test_extensions(self):
        self.create_file("src/test.py", "python")
        self.create_file("src/test.txt", "text")
        self.create_file("src/test.js", "javascript")

        context = get_codebase_context(
            self.test_dir,
            max_files=10,
            priority_dirs=['src'],
            extensions={'.py'}
        )

        self.assertIn("src/test.py", context)
        self.assertNotIn("src/test.txt", context)
        self.assertNotIn("src/test.js", context)

    def test_nested_dirs(self):
        self.create_file("src/deep/nested/file.py", "deep")

        context = get_codebase_context(
            self.test_dir,
            max_files=10,
            priority_dirs=['src'],
            extensions={'.py'}
        )

        self.assertIn("src/deep/nested/file.py", context)

    def test_context_truncation(self):
        limit = 100
        content = "a" * (limit + 50)
        self.create_file("src/large_file.py", content)

        with self.assertLogs(level='WARNING') as cm:
            context = get_codebase_context(
                self.test_dir,
                max_files=10,
                max_len=limit,
                priority_dirs=['src'],
                extensions={'.py'}
            )

        # Check truncation
        self.assertIn("src/large_file.py", context)
        expected_content = "a" * limit + "\n... [TRUNCATED]"
        self.assertIn(expected_content, context)

        # Check warning
        self.assertTrue(any("truncated" in log for log in cm.output))

if __name__ == '__main__':
    unittest.main()
