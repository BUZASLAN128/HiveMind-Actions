
#!/usr/bin/env python3
"""
This module contains shared utility functions and configurations for the
HiveMind project's AI agent scripts. It provides a centralized structure
to prevent code duplication and facilitate maintenance.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

from google import genai

# Proje genelinde kullanılacak standart logger yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def setup_generative_ai() -> genai.Client:
    """
    Configures and initializes the Gemini AI client using the API key.

    Reads the API key from the 'GEMINI_API_KEY' environment variable.
    If the key is not found, the program exits.

    Returns:
        genai.Client: An initialized and ready-to-use Gemini AI client.

    Raises:
        SystemExit: If the 'GEMINI_API_KEY' environment variable is not set.
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("Critical Error: GEMINI_API_KEY not found in environment variables!")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    logger.info("✅ Gemini AI client configured successfully.")
    return client


def load_prompt_template(prompt_path: Path) -> str:
    """
    Reads a prompt template file from the specified path.

    Args:
        prompt_path (Path): Path to the prompt template file.

    Returns:
        str: Content of the file.

    Raises:
        FileNotFoundError: If the file is not found at the specified path.
        IOError: If an error occurs while reading the file.
    """
    try:
        logger.info(f"📄 Reading prompt template: {prompt_path}")
        return prompt_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        logger.error(f"Error: Prompt file not found: {prompt_path}")
        raise
    except IOError as e:
        logger.error(f"Error: An error occurred while reading the prompt file: {prompt_path} - {e}")
        raise
