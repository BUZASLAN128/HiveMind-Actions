#!/usr/bin/env python3
"""
Tests for new AI features: TokenUsageTracker, MockProvider, Caching, Security.
"""

import os
import sys
import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add script directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_utils import (
    TokenUsageTracker,
    MockProvider,
    CachedProvider,
    redact_sensitive_data,
    get_provider,
    usage_tracker
)

class TestTokenUsageTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = TokenUsageTracker()

    def test_track_usage(self):
        self.tracker.track('glm-4', 1000, 1000)
        # GLM-4 rates: $10/M input, $10/M output
        # 1000/1M * 10 + 1000/1M * 10 = 0.01 + 0.01 = 0.02
        self.assertAlmostEqual(self.tracker.usage.cost_usd, 0.02)

        self.tracker.track('gemini-2.0-flash', 1000, 1000)
        # Gemini rates: $0.10/M input, $0.40/M output
        # 0.0001 + 0.0004 = 0.0005
        # Total: 0.02 + 0.0005 = 0.0205
        self.assertAlmostEqual(self.tracker.usage.cost_usd, 0.0205)

    def test_summary(self):
        self.tracker.track('glm-4', 1000, 1000)
        summary = self.tracker.get_summary()
        # self.assertIn("2000", summary) # Total tokens (input+output) ? No, tracker splits them
        self.assertIn("1000 In", summary)
        self.assertIn("1000 Out", summary)

class TestMockProvider(unittest.TestCase):
    def test_mock_generation(self):
        provider = MockProvider()
        response = provider.generate("test prompt")
        data = json.loads(response)
        self.assertTrue(data.get("mock_response"))
        self.assertEqual(provider.get_name(), "Mock Provider")

class TestCachedProvider(unittest.TestCase):
    def setUp(self):
        self.cache_dir = Path(".test_cache")
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)

        self.mock_inner = MagicMock()
        self.mock_inner.generate.return_value = "Generated Content"
        self.mock_inner.get_name.return_value = "TestProvider"

        self.cached_provider = CachedProvider(self.mock_inner, str(self.cache_dir))

    def tearDown(self):
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)

    def test_caching_logic(self):
        # First call - should hit provider
        resp1 = self.cached_provider.generate("prompt1")
        self.assertEqual(resp1, "Generated Content")
        self.mock_inner.generate.assert_called_once()

        # Second call - should hit cache
        resp2 = self.cached_provider.generate("prompt1")
        self.assertEqual(resp2, "Generated Content")
        # Call count should still be 1
        self.mock_inner.generate.assert_called_once()

        # Different prompt - should hit provider again
        resp3 = self.cached_provider.generate("prompt2")
        self.assertEqual(resp3, "Generated Content")
        self.assertEqual(self.mock_inner.generate.call_count, 2)

class TestSecurity(unittest.TestCase):
    def test_redact_jwt(self):
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        redacted = redact_sensitive_data(f"Token: {jwt}")
        self.assertIn("[REDACTED_JWT]", redacted)
        self.assertNotIn(jwt, redacted)

    def test_redact_internal_ip(self):
        text = "Connect to 192.168.1.50 and 10.0.0.1"
        redacted = redact_sensitive_data(text)
        self.assertIn("[REDACTED_INTERNAL_IP]", redacted)
        self.assertNotIn("192.168.1.50", redacted)
        self.assertNotIn("10.0.0.1", redacted)

        # Should not redact public IPs generally (simple regex check)
        # The regex I added was specific to private ranges.
        # Let's check 8.8.8.8
        redacted_public = redact_sensitive_data("Ping 8.8.8.8")
        self.assertIn("8.8.8.8", redacted_public)

class TestGetProvider(unittest.TestCase):
    @patch.dict(os.environ, {'SWARM_MODEL_PROVIDER': 'mock', 'SWARM_CACHE': 'true'})
    def test_get_provider_mock_cached(self):
        provider = get_provider()
        self.assertTrue(isinstance(provider, CachedProvider))
        self.assertTrue(isinstance(provider.provider, MockProvider))

    @patch.dict(os.environ, {'SWARM_MODEL_PROVIDER': 'mock', 'SWARM_CACHE': 'false'})
    def test_get_provider_mock_no_cache(self):
        provider = get_provider()
        self.assertTrue(isinstance(provider, MockProvider))
        self.assertFalse(isinstance(provider, CachedProvider))

if __name__ == '__main__':
    unittest.main()
