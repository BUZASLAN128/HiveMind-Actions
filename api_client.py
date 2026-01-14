import os

def get_api_key_from_env() -> str | None:
    """Retrieves the API key from the environment variable 'TEST_API_KEY'."""
    return os.environ.get("TEST_API_KEY")
