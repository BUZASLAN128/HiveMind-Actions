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
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Type

try:
    from pydantic import TypeAdapter, ValidationError
except ImportError:
    TypeAdapter = None
    ValidationError = None

# Constants
MAX_DIFF_READ_LIMIT = 30000
MAX_RULES_READ_LIMIT = 50000

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


# Metrics for tracking AI request performance
class RequestMetrics:
    """Tracks AI request metrics for observability."""
    
    def __init__(self):
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.total_duration: float = 0.0
        self.durations: List[float] = []
        self._max_durations: int = 1000  # Prevent memory leak
    
    def record(self, duration: float, success: bool) -> None:
        """Record a request result."""
        self.total_requests += 1
        self.total_duration += duration
        
        if len(self.durations) < self._max_durations:
            self.durations.append(duration)
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    @property
    def success_rate(self) -> float:
        """Return success rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests * 100
    
    @property
    def avg_duration(self) -> float:
        """Return average request duration."""
        if not self.durations:
            return 0.0
        return sum(self.durations) / len(self.durations)
    
    def summary(self) -> str:
        """Return human-readable summary."""
        return (
            f"Requests: {self.total_requests} | "
            f"Success: {self.success_rate:.1f}% | "
            f"Avg Time: {self.avg_duration:.2f}s"
        )
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_duration = 0.0
        self.durations = []


# Global metrics instance
metrics = RequestMetrics()


# Configuration management
_config_cache: Dict[str, Any] = {}

def load_config(config_path: str = '.github/config.json') -> Dict[str, Any]:
    """
    Load configuration from JSON file with caching.
    
    Args:
        config_path: Path to the config file
        
    Returns:
        Configuration dictionary
    """
    global _config_cache
    
    if _config_cache:
        return _config_cache
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            _config_cache = json.load(f)
        logger.info(f"Loaded config from {config_path}")
    except FileNotFoundError:
        logger.warning(f"Config not found at {config_path}, using defaults")
        _config_cache = {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        _config_cache = {}
    
    return _config_cache


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a config value by dot notation key.
    
    Args:
        key: Dot-separated key path (e.g., 'limits.max_diff_read')
        default: Default value if key not found
        
    Returns:
        Config value or default
    """
    config = load_config()
    keys = key.split('.')
    value = config
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


class ModelProvider(ABC):
    """Abstract base class for AI model providers."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response from the model."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the provider name."""
        pass
    
    def health_check(self) -> Tuple[bool, str]:
        """
        Check if provider is healthy and responsive.
        
        Returns:
            Tuple of (is_healthy: bool, message: str)
        """
        try:
            start = time.time()
            response = self.generate("Say OK")
            duration = time.time() - start
            if response and len(response) > 0:
                return True, f"Healthy ({duration:.2f}s)"
            return False, "Empty response"
        except Exception as e:
            return False, str(e)


class GLMProvider(ModelProvider):
    """GLM-4 Provider using OpenAI-compatible API."""
    
    def __init__(self):
        try:
            from openai import OpenAI
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
            raise
        
        api_key = os.getenv('GLM_API_KEY') or os.getenv('ZHIPUAI_API_KEY')
        if not api_key:
            logger.error("GLM_API_KEY or ZHIPUAI_API_KEY not found!")
            raise ValueError("GLM API Key not configured")
        
        # Base URL - z.ai Coding Plan endpoint (with trailing slash)
        base_url = os.getenv('GLM_BASE_URL', 'https://api.z.ai/api/coding/paas/v4/')
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = os.getenv('GLM_MODEL', 'glm-4.7')
        logger.info(f"GLM Provider initialized: model={self.model}, base_url={base_url}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
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
    
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None):
        """
        Stream response chunks for long responses.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Yields:
            Response chunks as strings
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
            stream=True
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def generate_with_stream(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate full response using streaming (more reliable for long responses).
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Complete response string
        """
        parts = []
        for chunk in self.generate_stream(prompt, system_prompt):
            parts.append(chunk)
        return "".join(parts)
    
    def get_name(self) -> str:
        return f"GLM ({self.model})"


class GeminiProvider(ModelProvider):
    """Google Gemini Provider."""
    
    def __init__(self):
        try:
            from google import genai
        except ImportError:
            logger.error("google-genai package not installed. Run: pip install google-genai")
            raise
        
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.error("GEMINI_API_KEY not found!")
            raise ValueError("Gemini API Key not configured")
        
        self.client = genai.Client(api_key=api_key)
        self.model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        logger.info(f"Gemini Provider initialized with model: {self.model}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt
        )
        return response.text.strip()
    
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
    elif provider_name == 'gemini':
        return GeminiProvider()
    else:
        logger.warning(f"Unknown provider '{provider_name}', falling back to GLM")
        return GLMProvider()


def setup_generative_ai():
    """
    Legacy function for backward compatibility.
    Returns the Gemini client directly.
    
    DEPRECATED: Use get_provider() instead.
    """
    from google import genai
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("Critical Error: GEMINI_API_KEY not found!")
        sys.exit(1)
    
    client = genai.Client(api_key=api_key)
    logger.info("Gemini AI client configured successfully (legacy mode).")
    return client


def with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
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
    start_time = time.time()
    
    for attempt in range(max_retries + 1):
        try:
            result = func()
            # Record successful request
            duration = time.time() - start_time
            metrics.record(duration, success=True)
            return result
        except Exception as e:
            last_exception = e
            
            if attempt == max_retries:
                # Record failed request
                duration = time.time() - start_time
                metrics.record(duration, success=False)
                logger.error(redact_sensitive_data(f"All {max_retries + 1} attempts failed. Last error: {e}"))
                raise
            
            # Exponential backoff: 1s, 2s, 4s...
            delay = base_delay * (2 ** attempt)

            # Special handling for Rate Limit (429) errors
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                delay = max(delay, 5.0)  # Force at least 5s wait for rate limits
                logger.warning(f"Rate limit detected. Increasing delay to {delay:.2f}s")
            # Jitter: +/- 25%
            jitter = delay * 0.25 * (random.random() * 2 - 1)
            sleep_time = max(0.1, delay + jitter)
            
            logger.warning(redact_sensitive_data(f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f}s..."))
            time.sleep(sleep_time)
    
    raise last_exception


def parse_json_response(text: str, schema: Optional[Any] = None) -> Dict[str, Any]:
    """
    Robust JSON parsing with multiple fallback methods and optional schema validation.
    
    Methods:
        1. Direct parse
        2. Markdown code block extraction
        3. json_repair library
        4. Regex extraction + repair
    
    Args:
        text: Raw response text from AI model
        schema: Optional schema for validation (Dict[str, Type] or Pydantic TypeAdapter/Model)
    
    Returns:
        Parsed JSON as dictionary
    
    Raises:
        ValueError: If parsing fails
        TypeError: If schema validation fails
    """
    # Clean the text
    text = text.strip()
    parsed_json = None
    
    # Method 1: Direct parse
    if parsed_json is None:
        try:
            parsed_json = json.loads(text)
        except json.JSONDecodeError:
            pass
    
    # Method 2: Markdown extraction
    if parsed_json is None:
        json_text = text
        if '```json' in text:
            try:
                json_text = text.split('```json')[1].split('```')[0].strip()
                parsed_json = json.loads(json_text)
            except (IndexError, json.JSONDecodeError):
                pass
        elif '```' in text:
            try:
                json_text = text.split('```')[1].split('```')[0].strip()
                parsed_json = json.loads(json_text)
            except (IndexError, json.JSONDecodeError):
                pass

    # Method 3: Try json_repair if available
    if parsed_json is None:
        try:
            import json_repair
            repaired = json_repair.repair_json(text, return_objects=True)
            if isinstance(repaired, dict):
                parsed_json = repaired
        except ImportError:
            logger.debug("json_repair not available, skipping")
        except Exception:
            pass
    
    # Method 4: Regex extraction
    if parsed_json is None:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            extracted = match.group(0)
            try:
                parsed_json = json.loads(extracted)
            except json.JSONDecodeError:
                # Try repair on extracted JSON
                try:
                    import json_repair
                    repaired = json_repair.repair_json(extracted, return_objects=True)
                    if isinstance(repaired, dict):
                        parsed_json = repaired
                except (ImportError, Exception):
                    pass
    
    if parsed_json is None:
        raise ValueError(f"Could not parse JSON from response. First 500 chars: {text[:500]}")

    # Validation Logic
    if schema:
        # Pydantic validation (preferred)
        if TypeAdapter and (isinstance(schema, type) or hasattr(schema, 'validate_python')):
            try:
                adapter = TypeAdapter(schema)
                # Validate and return as dict (if it's a model)
                validated = adapter.validate_python(parsed_json)
                if hasattr(validated, 'model_dump'):
                    return validated.model_dump()
                elif hasattr(validated, 'dict'):
                    return validated.dict()
                return validated # Return as is if it's a dict or other type
            except ValidationError as e:
                logger.warning(f"Schema validation failed (Pydantic): {e}")
                # Log warning but return parsed JSON to allow partial handling
                pass

        # Simple Dict[str, Type] validation
        elif isinstance(schema, dict):
            errors = []
            for key, expected_type in schema.items():
                if key not in parsed_json:
                    errors.append(f"Missing key: {key}")
                    continue

                # Handle generic types (basic support)
                check_type = expected_type
                if hasattr(expected_type, '__origin__'):
                    check_type = expected_type.__origin__

                if isinstance(check_type, type) and not isinstance(parsed_json[key], check_type):
                    # Allow int for float
                    if check_type == float and isinstance(parsed_json[key], int):
                        continue
                    errors.append(f"Key '{key}' expected {expected_type}, got {type(parsed_json[key])}")

            if errors:
                logger.warning(f"Schema validation failed: {'; '.join(errors)}")

    return parsed_json


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
        logger.info(f"Reading prompt template: {prompt_path}")
        return prompt_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        raise
    except IOError as e:
        logger.error(f"Error reading prompt file: {prompt_path} - {e}")
        raise

def load_rules(filepath: str = '.github/swarm_rules.md') -> str:
    """
    Reads project rules from the configuration file.

    Args:
        filepath (str): Path to the rules file.

    Returns:
        str: Content of the file or a default message if not found.
    """
    try:
        with open(filepath, 'r', encoding="utf-8") as f:
            content = f.read(MAX_RULES_READ_LIMIT + 1)

        if len(content) > MAX_RULES_READ_LIMIT:
            logger.warning(f"Rules file {filepath} truncated because it exceeds {MAX_RULES_READ_LIMIT} chars")
            content = content[:MAX_RULES_READ_LIMIT] + "\n\n... [RULES TRUNCATED] ..."

        logger.info(f"Loaded project rules from {filepath}")
        return content
    except FileNotFoundError:
        logger.warning(f"No project rules found at {filepath}, using defaults")
        return "No project rules found. Apply general Clean Code principles."
