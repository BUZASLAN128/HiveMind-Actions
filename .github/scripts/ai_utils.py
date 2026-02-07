#!/usr/bin/env python3
"""
HiveMind AI Utilities - Multi-Model Provider Architecture
Supports: GLM-4, Gemini, OpenAI-compatible APIs

This module provides a unified interface for different AI model providers.
"""

import os
import sys
import json
import logging
import random
import time
import re
import functools
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Iterator, TypeVar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

T = TypeVar("T")

class ModelProvider(ABC):
    """Abstract base class for AI model providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response from the model."""

    @abstractmethod
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[str]:
        """Generate a streaming response from the model."""

    @abstractmethod
    def get_name(self) -> str:
        """Return the provider name."""

    def _validate_input(self, prompt: str) -> None:
        """Validates the input prompt."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")
        if len(prompt) > 100000:  # Arbitrary limit for safety
            raise ValueError("Prompt exceeds maximum length of 100,000 characters.")


class GLMProvider(ModelProvider):
    """GLM-4 Provider using OpenAI-compatible API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[Any] = None
    ) -> None:
        """
        Initialize the GLM Provider.

        Args:
            api_key: API Key for the service. Defaults to env var GLM_API_KEY.
            base_url: Base URL for the API. Defaults to env var GLM_BASE_URL.
            model: Model name to use. Defaults to env var GLM_MODEL.
            client: Pre-configured OpenAI client instance (optional).
        """
        try:
            # pylint: disable=import-outside-toplevel
            from openai import OpenAI
        except ImportError as exc:
            logger.error("openai package not installed. Run: pip install openai")
            raise exc

        self.api_key = api_key or os.getenv('GLM_API_KEY') or os.getenv('ZHIPUAI_API_KEY')
        if not self.api_key and not client:
            logger.error("GLM_API_KEY or ZHIPUAI_API_KEY not found!")
            raise ValueError("GLM API Key not configured")

        # Base URL - z.ai Coding Plan endpoint (with trailing slash)
        self.base_url = base_url or os.getenv('GLM_BASE_URL', 'https://api.z.ai/api/coding/paas/v4/')
        self.model = model or os.getenv('GLM_MODEL', 'glm-4.7')

        if client:
            self.client = client
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

        logger.info("GLM Provider initialized: model=%s, base_url=%s", self.model, self.base_url)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self._validate_input(prompt)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096
        )
        return response.choices[0].message.content

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[str]:
        self._validate_input(prompt)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def get_name(self) -> str:
        return f"GLM ({self.model})"


class GeminiProvider(ModelProvider):
    """Google Gemini Provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[Any] = None
    ) -> None:
        """
        Initialize the Gemini Provider.

        Args:
            api_key: API Key for the service. Defaults to env var GEMINI_API_KEY.
            model: Model name to use. Defaults to env var GEMINI_MODEL.
            client: Pre-configured Gemini client instance (optional).
        """
        try:
            # pylint: disable=import-outside-toplevel
            from google import genai
        except ImportError as exc:
            logger.error("google-genai package not installed. Run: pip install google-genai")
            raise exc

        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not self.api_key and not client:
            logger.error("GEMINI_API_KEY not found!")
            raise ValueError("Gemini API Key not configured")

        self.model = model or os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

        if client:
            self.client = client
        else:
            self.client = genai.Client(api_key=self.api_key)

        logger.info("Gemini Provider initialized with model: %s", self.model)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self._validate_input(prompt)
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt
        )
        return response.text.strip()

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[str]:
        """Streaming implementation for Gemini."""
        self._validate_input(prompt)
        # Placeholder for Gemini streaming implementation
        # pylint: disable=unused-argument
        raise NotImplementedError("Streaming not yet implemented for Gemini Provider")

    def get_name(self) -> str:
        return f"Gemini ({self.model})"


def get_provider() -> ModelProvider:
    """
    Factory function to get the configured model provider.

    Environment Variables:
        SWARM_MODEL_PROVIDER: 'glm' or 'gemini' (default: 'glm')
    """
    provider_name = os.getenv('SWARM_MODEL_PROVIDER', 'glm').lower()

    if provider_name == 'glm':
        return GLMProvider()
    if provider_name == 'gemini':
        return GeminiProvider()

    logger.warning("Unknown provider '%s', falling back to GLM", provider_name)
    return GLMProvider()


def setup_generative_ai() -> Any:
    """
    Legacy function for backward compatibility.
    Returns the Gemini client directly.

    DEPRECATED: Use get_provider() instead.
    """
    # pylint: disable=import-outside-toplevel
    from google import genai

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("Critical Error: GEMINI_API_KEY not found!")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    logger.info("Gemini AI client configured successfully (legacy mode).")
    return client


def with_retry(
    func: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 1.0
) -> Any:
    """
    Execute a function with exponential backoff retry logic.

    Args:
        func: Callable to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds

    Returns:
        Result of the function call

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e

            if attempt == max_retries:
                msg = f"All {max_retries + 1} attempts failed. Last error: {e}"
                logger.error(redact_sensitive_data(msg))
                raise

            # Exponential backoff: 1s, 2s, 4s...
            delay = base_delay * (2 ** attempt)
            # Jitter: +/- 25%
            jitter = delay * 0.25 * (random.random() * 2 - 1)
            sleep_time = max(0.1, delay + jitter)

            msg = f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f}s..."
            logger.warning(redact_sensitive_data(msg))
            time.sleep(sleep_time)

    raise last_exception  # Should be unreachable if max_retries >= 0


def parse_json_response(text: str) -> Dict[str, Any]:
    """
    Robust JSON parsing with multiple fallback methods.

    Methods:
        1. Direct parse
        2. Markdown code block extraction
        3. json_repair library
        4. Regex extraction + repair

    Args:
        text: Raw response text from AI model

    Returns:
        Parsed JSON as dictionary

    Raises:
        ValueError: If all parsing methods fail
    """
    # Clean the text
    text = text.strip()

    # Method 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Method 2: Markdown extraction
    json_text = text
    if '```json' in text:
        try:
            json_text = text.split('```json')[1].split('```')[0].strip()
            return json.loads(json_text)
        except (IndexError, json.JSONDecodeError):
            pass
    elif '```' in text:
        try:
            json_text = text.split('```')[1].split('```')[0].strip()
            return json.loads(json_text)
        except (IndexError, json.JSONDecodeError):
            pass

    # Method 3: Try json_repair if available
    try:
        # pylint: disable=import-outside-toplevel
        import json_repair  # type: ignore
        repaired = json_repair.repair_json(text, return_objects=True)
        if isinstance(repaired, dict):
            return repaired
    except ImportError:
        logger.debug("json_repair not available, skipping")
    except Exception:
        pass

    # Method 4: Regex extraction
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        extracted = match.group(0)
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            # Try repair on extracted JSON
            try:
                # pylint: disable=import-outside-toplevel
                import json_repair  # type: ignore
                repaired = json_repair.repair_json(extracted, return_objects=True)
                if isinstance(repaired, dict):
                    return repaired
            except (ImportError, Exception):
                pass

    # All methods failed
    raise ValueError(f"Could not parse JSON from response. First 500 chars: {text[:500]}")


def redact_sensitive_data(text: str) -> str:
    """
    Redacts potentially sensitive data from text.

    Detects and masks:
        - API keys (OpenAI, Google, GitHub, Slack)
        - Passwords and secrets
        - Database credentials in URLs
    """
    patterns = [
        (r'sk-[a-zA-Z0-9]{20,}', '[REDACTED_OPENAI_KEY]'),
        (r'AIza[a-zA-Z0-9_-]{35}', '[REDACTED_GOOGLE_KEY]'),
        (r'ghp_[a-zA-Z0-9]{36}', '[REDACTED_GITHUB_TOKEN]'),
        (r'gho_[a-zA-Z0-9]{36}', '[REDACTED_GITHUB_OAUTH]'),
        (r'xox[bap]-[a-zA-Z0-9-]{10,}', '[REDACTED_SLACK_TOKEN]'),
        (r'(?i)(password|secret|key|token|auth)\s*[=:]\s*["\']?[a-zA-Z0-9_.@/-]{3,}["\']?', r'\1=[REDACTED]'),
        (r'[a-zA-Z0-9._%+-]+:[a-zA-Z0-9._%+-]+@', '[REDACTED_CREDS]@'),
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)

    return result


def load_prompt_template(prompt_path: Path) -> str:
    """
    Reads a prompt template file from the specified path.

    Args:
        prompt_path (Path): Path to the prompt template file.

    Returns:
        str: Content of the file.

    Raises:
        FileNotFoundError: If the file is not found.
        IOError: If an error occurs while reading.
    """
    try:
        logger.info("Reading prompt template: %s", prompt_path)
        return prompt_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        logger.error("Prompt file not found: %s", prompt_path)
        raise
    except IOError as e:
        logger.error("Error reading prompt file: %s - %s", prompt_path, e)
        raise


def ttl_cache(ttl: int = 3600) -> Callable:
    """
    Decorator to cache function results with a Time-To-Live (TTL).

    Args:
        ttl: Time in seconds to keep the result in cache.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: Dict[str, Any] = {}

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create a key based on arguments
            key = str(args) + str(kwargs)
            now = time.time()

            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl:
                    logger.debug("Cache hit for %s", func.__name__)
                    return result

            result = func(*args, **kwargs)
            cache[key] = (result, now)
            logger.debug("Cache miss for %s", func.__name__)
            return result

        return wrapper
    return decorator
