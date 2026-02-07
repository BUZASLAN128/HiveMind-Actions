import sys
import unittest
sys.path.insert(0, '.')

from swarm_reviewer import calculate_approval

class TestApproval(unittest.TestCase):
    def test_happy_path(self):
        # Perfect score
        data = {"score": 10, "security_ok": True}
        approved, reason = calculate_approval(data)
        self.assertTrue(approved)
        self.assertIn("Approved", reason)

    def test_security_failure(self):
        # High score but security issues
        data = {"score": 10, "security_ok": False}
        approved, reason = calculate_approval(data)
        self.assertFalse(approved)
        self.assertIn("Security issues", reason)

    def test_conditional_approval(self):
        # Score 7, compliant, few issues
        data = {
            "score": 7,
            "security_ok": True,
            "project_compliance": True,
            "issues": ["one", "two"]
        }
        approved, reason = calculate_approval(data)
        self.assertTrue(approved)
        self.assertIn("Approved with 2 minor issues", reason)

    def test_conditional_rejection_too_many_issues(self):
        # Score 7, compliant, too many issues
        data = {
            "score": 7,
            "security_ok": True,
            "project_compliance": True,
            "issues": ["one", "two", "three"]
        }
        approved, reason = calculate_approval(data)
        self.assertFalse(approved)
        self.assertIn("Score 7/10 with 3 issues", reason)

    def test_conditional_rejection_not_compliant(self):
        # Score 7, not compliant
        data = {
            "score": 7,
            "security_ok": True,
            "project_compliance": False,
            "issues": []
        }
        approved, reason = calculate_approval(data)
        self.assertFalse(approved)
        self.assertIn("Score 7/10", reason)

    def test_low_score(self):
        # Score < 6
        data = {"score": 5, "security_ok": True}
        approved, reason = calculate_approval(data)
        self.assertFalse(approved)
        self.assertIn("Score 5/10", reason)

    def test_missing_fields_defaults(self):
        # Empty dict should result in rejection (score 0, security False)
        data = {}
        approved, reason = calculate_approval(data)
        self.assertFalse(approved)
        self.assertIn("Security issues", reason)

    def test_none_values_short_circuit(self):
        # Explicit None values where security fails first
        data = {
            "score": None,
            "security_ok": None,
            "project_compliance": None,
            "issues": None
        }
        approved, reason = calculate_approval(data)
        self.assertFalse(approved)
        self.assertIn("Security issues", reason)

    def test_none_score_passed_security(self):
        # Security passed, but score is None
        data = {"score": None, "security_ok": True}
        try:
            approved, reason = calculate_approval(data)
            self.assertFalse(approved)
        except TypeError as e:
            self.fail(f"calculate_approval crashed with score=None: {e}")

    def test_none_issues_passed_security_and_score(self):
        # Security passed, score passed conditional, but issues is None
        data = {
            "score": 7,
            "security_ok": True,
            "project_compliance": True,
            "issues": None
        }
        try:
            approved, reason = calculate_approval(data)
            # Should treat None issues as empty list? Or fail safely?
            # Assuming we want it to be robust: treat as empty list -> Approved
            self.assertTrue(approved)
            self.assertIn("Approved", reason)
        except TypeError as e:
            self.fail(f"calculate_approval crashed with issues=None: {e}")

    def test_malformed_values(self):
        # Unexpected types
        data = {
            "score": "ten", # String instead of int
            "security_ok": "yes", # String instead of bool
            "issues": "many" # String instead of list
        }
        # This test ensures we don't crash
        try:
            approved, reason = calculate_approval(data)
            self.assertFalse(approved)
        except Exception as e:
            self.fail(f"calculate_approval raised exception with malformed data: {e}")

if __name__ == '__main__':
    unittest.main()
