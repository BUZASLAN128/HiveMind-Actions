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
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# --- Observability & Logging ---

class JsonFormatter(logging.Formatter):
    """Formatter for JSON structured logging."""
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    """Configures logging based on environment variables."""
    log_format = os.getenv('LOG_FORMAT', 'text').lower()
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    if log_format == 'json':
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # Remove existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers = []

    root_logger.addHandler(handler)
    return logging.getLogger(__name__)

logger = setup_logging()

@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0

class TokenUsageTracker:
    """Tracks token usage and estimates costs."""

    # Simple cost estimation (per 1M tokens) - default to GLM-4 rates
    COST_RATES = {
        'glm-4': {'input': 10.0, 'output': 10.0}, # Placeholder
        'gemini-2.0-flash': {'input': 0.10, 'output': 0.40},
        'default': {'input': 5.0, 'output': 15.0}
    }

    def __init__(self):
        self.usage = TokenUsage()
        self._lock = False # Not needed for sync scripts but good practice

    def track(self, model: str, input_tokens: int, output_tokens: int):
        """Records usage and updates cost."""
        self.usage.input_tokens += input_tokens
        self.usage.output_tokens += output_tokens

        # Estimate cost
        rates = self.COST_RATES.get(model, self.COST_RATES['default'])
        cost = (input_tokens / 1_000_000 * rates['input']) + \
               (output_tokens / 1_000_000 * rates['output'])
        self.usage.cost_usd += cost

        logger.info(f"Token Usage: +{input_tokens} in, +{output_tokens} out. Est. Cost: ${cost:.6f}")

    def get_summary(self) -> str:
        return (f"Total Token Usage: {self.usage.input_tokens} In, "
                f"{self.usage.output_tokens} Out. "
                f"Est. Cost: ${self.usage.cost_usd:.4f}")

# Global tracker instance
usage_tracker = TokenUsageTracker()


# --- Core AI Logic ---

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
        
        # Base URL - z.ai Coding Plan endpoint
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
        
        # Rough estimation of input tokens (char / 4)
        input_est = len(json.dumps(messages)) // 4

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096
        )
        content = response.choices[0].message.content

        # Track usage
        if hasattr(response, 'usage') and response.usage:
            usage_tracker.track(self.model, response.usage.prompt_tokens, response.usage.completion_tokens)
        else:
            output_est = len(content) // 4
            usage_tracker.track(self.model, input_est, output_est)

        return content
    
    def get_name(self) -> str:
        return f"GLM ({self.model})"


class GeminiProvider(ModelProvider):
    """Google Gemini Provider."""
    
    def __init__(self):
        try:
            from google import genai
            from google.genai import types
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
        
        config = None
        if system_prompt:
             # Use system_instruction if supported, or prepend
            config = {'system_instruction': system_prompt}

        # Estimate input
        input_est = (len(prompt) + len(system_prompt or "")) // 4

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )

        text_response = response.text.strip()

        # Track usage (Gemini API might provide usage metadata, but sticking to estimation for now or checking response object)
        # response.usage_metadata exists in some versions
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
             usage_tracker.track(self.model, response.usage_metadata.prompt_token_count, response.usage_metadata.candidates_token_count)
        else:
             output_est = len(text_response) // 4
             usage_tracker.track(self.model, input_est, output_est)

        return text_response
    
    def get_name(self) -> str:
        return f"Gemini ({self.model})"


class MockProvider(ModelProvider):
    """Mock Provider for testing without API keys."""

    def __init__(self):
        logger.info("Mock Provider initialized")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        logger.info("Mock Provider generating response...")
        usage_tracker.track("mock-model", len(prompt)//4, 50)
        return json.dumps({
            "mock_response": True,
            "analysis": "This is a mock analysis.",
            "should_proceed": True,
            "issue_type": "feature_request",
            "files_to_change": ["mock_file.py"],
            "plan": ["Mock step 1", "Mock step 2"],
            "approved": True,
            "score": 10,
            "security_ok": True
        })

    def get_name(self) -> str:
        return "Mock Provider"


class CachedProvider(ModelProvider):
    """Wrapper that adds file-based caching to any provider."""

    def __init__(self, provider: ModelProvider, cache_dir: str = ".swarm_cache"):
        self.provider = provider
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"Caching enabled in {self.cache_dir}")

    def _get_cache_key(self, prompt: str, system_prompt: Optional[str]) -> str:
        content = f"{self.provider.get_name()}:{system_prompt}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        key = self._get_cache_key(prompt, system_prompt)
        cache_file = self.cache_dir / f"{key}.json"

        if cache_file.exists():
            logger.info(f"Cache hit for {key[:8]}")
            try:
                data = json.loads(cache_file.read_text(encoding='utf-8'))
                # update usage? Maybe not for cache hits, or track as 0 cost.
                return data['content']
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")

        logger.info(f"Cache miss for {key[:8]}")
        content = self.provider.generate(prompt, system_prompt)

        try:
            cache_file.write_text(json.dumps({'content': content}), encoding='utf-8')
        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")

        return content

    def get_name(self) -> str:
        return f"Cached({self.provider.get_name()})"


def get_provider() -> ModelProvider:
    """
    Factory function to get the configured model provider.
    
    Environment Variables:
        SWARM_MODEL_PROVIDER: 'glm', 'gemini', 'mock' (default: 'glm')
        SWARM_CACHE: 'true'/'false' (default: 'false')
    """
    provider_name = os.getenv('SWARM_MODEL_PROVIDER', 'glm').lower()
    
    if provider_name == 'mock':
        provider = MockProvider()
    elif provider_name == 'glm':
        provider = GLMProvider()
    elif provider_name == 'gemini':
        provider = GeminiProvider()
    else:
        logger.warning(f"Unknown provider '{provider_name}', falling back to GLM")
        provider = GLMProvider()

    if os.getenv('SWARM_CACHE', 'false').lower() == 'true':
        provider = CachedProvider(provider)

    return provider


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
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            if attempt == max_retries:
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
        import json_repair
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
                import json_repair
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
        - JWT tokens
        - Internal IP addresses
    """
    patterns = [
        (r'sk-[a-zA-Z0-9]{20,}', '[REDACTED_OPENAI_KEY]'),
        (r'AIza[a-zA-Z0-9_-]{35}', '[REDACTED_GOOGLE_KEY]'),
        (r'ghp_[a-zA-Z0-9]{36}', '[REDACTED_GITHUB_TOKEN]'),
        (r'gho_[a-zA-Z0-9]{36}', '[REDACTED_GITHUB_OAUTH]'),
        (r'xox[bap]-[a-zA-Z0-9-]{10,}', '[REDACTED_SLACK_TOKEN]'),
        # JWT pattern: header.payload.signature (base64url)
        (r'eyJ[a-zA-Z0-9-_]{10,}\.eyJ[a-zA-Z0-9-_]{10,}\.[a-zA-Z0-9-_]{10,}', '[REDACTED_JWT]'),
        # Internal IP (10.x.x.x, 192.168.x.x, 172.16-31.x.x)
        (r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b', '[REDACTED_INTERNAL_IP]'),
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
        content = Path(filepath).read_text(encoding="utf-8")
        logger.info(f"Loaded project rules from {filepath}")
        return content
    except FileNotFoundError:
        logger.warning(f"No project rules found at {filepath}, using defaults")
        return "No project rules found. Apply general Clean Code principles."
