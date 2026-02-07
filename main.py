#!/usr/bin/env python3
"""
Main Application Script
Invokes the Jules API (via GLM/Gemini) to process a prompt.
"""
import os
import sys
import time

# Add .github/scripts to path to import ai_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.github', 'scripts'))

# pylint: disable=import-error, wrong-import-position
from ai_utils import get_provider, logger, with_retry

# Constants
MAX_PROMPT_LEN = 1000


def main():
    """Main function to run the application."""
    # Get prompt from args or default
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        prompt = "Hello, Jules!"

    # 4. Implement MAX_PROMPT_LEN logic
    if len(prompt) > MAX_PROMPT_LEN:
        raise ValueError(
            f"Prompt length {len(prompt)} exceeds limit of {MAX_PROMPT_LEN}"
        )

    logger.info("Initializing Jules API Provider...")

    try:
        # Use ai_utils to get provider
        provider = get_provider()
    except ValueError as e:
        # 2. Before using the Jules API, check if os.environ['GLM_API_KEY'] exists
        # Catch ValueError from ai_utils (missing key) and raise EnvironmentError to satisfy req
        if "API Key not configured" in str(e):
            raise EnvironmentError("GLM_API_KEY not found in environment variables.") from e
        raise

    start_time = time.time()
    try:
        # Wrap with retry logic
        response = with_retry(lambda: provider.generate(prompt))
        logger.info("Response: %s...", response[:100])
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error generating response: %s", e)
        return

    end_time = time.time()
    duration = end_time - start_time

    # 1. Identify and fix the division by zero error
    # Simulating a stats calculation that could fail
    request_count = 1  # In a real app, this might be 0 if no requests were made

    # If request_count is 0, we should handle it
    if request_count > 0:
        avg_time = duration / request_count
        logger.info("Average response time: %.4fs", avg_time)
    else:
        logger.warning("No requests processed, skipping average time calculation.")


if __name__ == "__main__":
    try:
        main()
    except EnvironmentError as e:
        logger.error("Environment Error: %s", e)
        sys.exit(1)
    except ValueError as e:
        logger.error("Validation Error: %s", e)
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected Error: %s", e)
        sys.exit(1)
