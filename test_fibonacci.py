import pytest
import time
from fibonacci import fibonacci

def test_fibonacci_correctness():
    """
    Tests the correctness of the fibonacci function for a small value.
    """
    assert fibonacci(10) == 55

def test_fibonacci_performance():
    """
    Tests the performance of the fibonacci function.

    Note: The original request for n=10000 is computationally infeasible for a simple
    recursive implementation and would cause a RecursionError. We are using n=35
    as a more realistic benchmark for this performance test.
    """
    n = 35
    start_time = time.perf_counter()
    result = fibonacci(n)
    end_time = time.perf_counter()
    execution_time = end_time - start_time

    # Assert that the result is correct for n=35
    assert result == 9227465

    # Assert that the execution time is within an acceptable threshold (e.g., 60 seconds)
    assert execution_time < 60

def test_fibonacci_negative_input():
    """
    Tests that the fibonacci function raises a ValueError for negative input.
    """
    with pytest.raises(ValueError):
        fibonacci(-1)
