import pytest
from fibonacci import fibonacci, fibonacci_recursive

def test_fibonacci_iterative():
    """
    Tests the iterative fibonacci function with a few base cases and a small input.
    """
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(10) == 55
    assert fibonacci(20) == 6765

def test_fibonacci_recursive_performance():
    """
    Tests that the recursive fibonacci function raises a RecursionError for large inputs.
    """
    with pytest.raises(RecursionError):
        fibonacci_recursive(1000)
