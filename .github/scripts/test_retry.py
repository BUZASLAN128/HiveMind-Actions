import sys
import os
import time
import pytest
from unittest.mock import MagicMock, patch

# Add script dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_utils import with_retry

def test_retry_success():
    mock_func = MagicMock(return_value="success")
    result = with_retry(mock_func)
    assert result == "success"
    assert mock_func.call_count == 1

def test_retry_fail_then_success():
    mock_func = MagicMock(side_effect=[Exception("fail"), "success"])
    result = with_retry(mock_func, max_retries=2, base_delay=0.01)
    assert result == "success"
    assert mock_func.call_count == 2

def test_retry_max_retries_exceeded():
    mock_func = MagicMock(side_effect=Exception("fail"))
    with pytest.raises(Exception):
        with_retry(mock_func, max_retries=2, base_delay=0.01)
    assert mock_func.call_count == 3

@patch('time.sleep')
def test_rate_limit_backoff(mock_sleep):
    # Simulate 429 error
    rate_limit_error = Exception("Error 429: Too Many Requests")
    mock_func = MagicMock(side_effect=[rate_limit_error, "success"])

    with_retry(mock_func, max_retries=1, base_delay=0.1)

    # Verify sleep was called
    assert mock_sleep.called
    sleep_time = mock_sleep.call_args[0][0]

    # With penalty of 5.0, delay is 5.0. Jitter is +/- 1.25. Min sleep is 3.75.
    print(f"Sleep time: {sleep_time}")
    assert sleep_time >= 3.5, f"Sleep time {sleep_time} should be > 3.5s for rate limit"
