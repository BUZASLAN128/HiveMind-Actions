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
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


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
            # Jitter: +/- 25%
            jitter = delay * 0.25 * (random.random() * 2 - 1)
            sleep_time = max(0.1, delay + jitter)
            
            # Smart Rate Limit Detection
            is_rate_limit = False
            # Check string representation for common rate limit indicators
            err_str = str(e).lower()
            if "429" in err_str or "rate limit" in err_str or "too many requests" in err_str:
                is_rate_limit = True

            # Check explicit type if openai is available
            if not is_rate_limit:
                try:
                    import openai
                    if isinstance(e, openai.RateLimitError):
                        is_rate_limit = True
                except ImportError:
                    pass

            if is_rate_limit:
                # Enforce a stricter delay for rate limits: at least 5s, scaling up
                min_rate_limit_delay = 5.0 * (attempt + 1)
                if sleep_time < min_rate_limit_delay:
                    sleep_time = min_rate_limit_delay
                logger.warning(f"Rate limit detected. Increased delay to {sleep_time:.2f}s")

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
