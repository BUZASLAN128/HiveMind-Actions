#!/usr/bin/env python3
"""Unit tests for AI Providers in ai_utils.py using Mocks"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, '.')

# Mock google.genai and openai modules before importing ai_utils
# We use a single mock object for genai to ensure consistency
mock_genai_module = MagicMock()
sys.modules["google.genai"] = mock_genai_module

mock_google = MagicMock()
mock_google.genai = mock_genai_module
sys.modules["google"] = mock_google

sys.modules["openai"] = MagicMock()

from ai_utils import GLMProvider, GeminiProvider, get_provider

class TestGLMProvider(unittest.TestCase):
    def setUp(self):
        self.mock_openai_class = sys.modules["openai"].OpenAI
        self.mock_client = self.mock_openai_class.return_value
        self.mock_chat = self.mock_client.chat
        self.mock_completions = self.mock_chat.completions

        # Setup mock response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "GLM Response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        self.mock_completions.create.return_value = mock_response

        # Set env var
        os.environ['GLM_API_KEY'] = 'fake_glm_key'
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']

    def tearDown(self):
        if 'GLM_API_KEY' in os.environ:
            del os.environ['GLM_API_KEY']

    def test_init(self):
        provider = GLMProvider()
        self.mock_openai_class.assert_called_with(
            api_key='fake_glm_key',
            base_url='https://api.z.ai/api/coding/paas/v4/'
        )
        self.assertEqual(provider.model, 'glm-4.7')

    def test_generate_no_system_prompt(self):
        provider = GLMProvider()
        response = provider.generate("Hello")
        self.assertEqual(response, "GLM Response")

        self.mock_completions.create.assert_called_with(
            model='glm-4.7',
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=4096
        )

    def test_generate_with_system_prompt(self):
        provider = GLMProvider()
        response = provider.generate("Hello", system_prompt="Be helpful")
        self.assertEqual(response, "GLM Response")

        self.mock_completions.create.assert_called_with(
            model='glm-4.7',
            messages=[
                {"role": "system", "content": "Be helpful"},
                {"role": "user", "content": "Hello"}
            ],
            temperature=0.7,
            max_tokens=4096
        )


class TestGeminiProvider(unittest.TestCase):
    def setUp(self):
        # We need to grab the same mock object that was used during import
        self.mock_genai = sys.modules["google.genai"]
        self.mock_client_class = self.mock_genai.Client
        self.mock_client_instance = self.mock_client_class.return_value
        self.mock_models = self.mock_client_instance.models

        # Setup mock response
        mock_response = MagicMock()
        # Mock .text property
        type(mock_response).text = unittest.mock.PropertyMock(return_value="Gemini Response")
        self.mock_models.generate_content.return_value = mock_response

        # Set env var
        os.environ['GEMINI_API_KEY'] = 'fake_gemini_key'

    def tearDown(self):
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']

    def test_init(self):
        provider = GeminiProvider()
        self.mock_client_class.assert_called_with(api_key='fake_gemini_key')
        self.assertEqual(provider.model, 'gemini-2.0-flash')

    def test_generate_no_system_prompt(self):
        provider = GeminiProvider()
        response = provider.generate("Hello")
        self.assertEqual(response, "Gemini Response")

        call_args = self.mock_models.generate_content.call_args
        kwargs = call_args.kwargs
        self.assertEqual(kwargs['model'], 'gemini-2.0-flash')
        self.assertEqual(kwargs['contents'], 'Hello')

    def test_generate_with_system_prompt(self):
        provider = GeminiProvider()

        # Mock types.GenerateContentConfig
        # Ensure we set it on the shared module mock
        mock_types = MagicMock()
        self.mock_genai.types = mock_types

        response = provider.generate("Hello", system_prompt="Be helpful")
        self.assertEqual(response, "Gemini Response")

        call_args = self.mock_models.generate_content.call_args
        kwargs = call_args.kwargs
        self.assertEqual(kwargs['model'], 'gemini-2.0-flash')

        # Check if config was passed
        self.assertIn('config', kwargs)
        self.assertIsNotNone(kwargs['config'])


class TestGetProvider(unittest.TestCase):
    def setUp(self):
        # Reset env
        if 'SWARM_MODEL_PROVIDER' in os.environ:
            del os.environ['SWARM_MODEL_PROVIDER']
        os.environ['GLM_API_KEY'] = 'fake'
        os.environ['GEMINI_API_KEY'] = 'fake'

        # Reset mocks
        sys.modules["openai"].OpenAI.reset_mock()
        sys.modules["google.genai"].Client.reset_mock()

    def test_default_provider(self):
        provider = get_provider()
        self.assertIsInstance(provider, GLMProvider)

    def test_glm_provider(self):
        os.environ['SWARM_MODEL_PROVIDER'] = 'glm'
        provider = get_provider()
        self.assertIsInstance(provider, GLMProvider)

    def test_gemini_provider(self):
        os.environ['SWARM_MODEL_PROVIDER'] = 'gemini'
        provider = get_provider()
        self.assertIsInstance(provider, GeminiProvider)

    def test_fallback(self):
        os.environ['SWARM_MODEL_PROVIDER'] = 'unknown'
        provider = get_provider()
        self.assertIsInstance(provider, GLMProvider)

if __name__ == '__main__':
    unittest.main()
