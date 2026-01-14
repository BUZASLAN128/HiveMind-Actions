import pytest
from api_client import get_api_key_from_env

def test_get_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Tests that the get_api_key_from_env function correctly retrieves
    the API key from the environment variable.
    """
    fake_api_key = "test_key_12345"
    monkeypatch.setenv("TEST_API_KEY", fake_api_key)
    retrieved_key = get_api_key_from_env()
    assert retrieved_key == fake_api_key

def test_get_api_key_from_env_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Tests that the get_api_key_from_env function returns None
    when the environment variable is not set.
    """
    # Ensure the environment variable is not set
    monkeypatch.delenv("TEST_API_KEY", raising=False)
    retrieved_key = get_api_key_from_env()
    assert retrieved_key is None
