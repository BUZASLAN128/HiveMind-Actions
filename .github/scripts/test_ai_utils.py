import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Ensure we can import ai_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_utils import get_provider, GLMProvider, GeminiProvider

@pytest.fixture
def mock_deps():
    """Mocks external dependencies to prevent ImportErrors."""
    with patch.dict(sys.modules, {
        'openai': MagicMock(),
        'google': MagicMock(),
        'google.genai': MagicMock()
    }):
        yield

def test_glm_missing_key(mock_deps):
    """Verify GLMProvider raises ValueError when API key is missing."""
    with patch.dict(os.environ, {'SWARM_MODEL_PROVIDER': 'glm'}, clear=True):
        # Ensure no other keys leak in
        if 'GLM_API_KEY' in os.environ: del os.environ['GLM_API_KEY']
        if 'ZHIPUAI_API_KEY' in os.environ: del os.environ['ZHIPUAI_API_KEY']

        with pytest.raises(ValueError, match="GLM API Key not configured"):
            get_provider()

def test_gemini_missing_key(mock_deps):
    """Verify GeminiProvider raises ValueError when API key is missing."""
    with patch.dict(os.environ, {'SWARM_MODEL_PROVIDER': 'gemini'}, clear=True):
        if 'GEMINI_API_KEY' in os.environ: del os.environ['GEMINI_API_KEY']
        if 'GOOGLE_API_KEY' in os.environ: del os.environ['GOOGLE_API_KEY']

        with pytest.raises(ValueError, match="Gemini API Key not configured"):
            get_provider()

def test_default_fallback_missing_key(mock_deps):
    """Verify default provider (GLM) raises ValueError when API key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        if 'GLM_API_KEY' in os.environ: del os.environ['GLM_API_KEY']
        if 'ZHIPUAI_API_KEY' in os.environ: del os.environ['ZHIPUAI_API_KEY']

        # Should fall back to GLM and raise ValueError
        with pytest.raises(ValueError, match="GLM API Key not configured"):
            get_provider()

def test_glm_valid_key(mock_deps):
    """Verify GLMProvider is returned when API key is present."""
    with patch.dict(os.environ, {'SWARM_MODEL_PROVIDER': 'glm', 'GLM_API_KEY': 'test_key'}, clear=True):
        provider = get_provider()
        assert isinstance(provider, GLMProvider)

def test_gemini_valid_key(mock_deps):
    """Verify GeminiProvider is returned when API key is present."""
    # We need to ensure google.genai.Client can be instantiated
    # The mock_deps fixture mocks the module, but we might need to mock the Client class specifically if the code uses it

    with patch.dict(os.environ, {'SWARM_MODEL_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'test_key'}, clear=True):
        provider = get_provider()
        assert isinstance(provider, GeminiProvider)
