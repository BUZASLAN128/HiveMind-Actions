import pytest
import timeit
from fibonacci import fibonacci

def test_fibonacci_zero():
    """Test the base case for n=0."""
    assert fibonacci(0) == 0

def test_fibonacci_one():
    """Test the base case for n=1."""
    assert fibonacci(1) == 1

def test_fibonacci_small_number():
    """Test a small value of n."""
    assert fibonacci(10) == 55

def test_fibonacci_large_number():
    """Test a larger value of n."""
    assert fibonacci(35) == 9227465

def test_fibonacci_negative_input():
    """Test that a negative input raises a ValueError."""
    with pytest.raises(ValueError):
        fibonacci(-1)

def test_fibonacci_performance():
    """
    Test the performance of the fibonacci function.
    Ensures that calculating fibonacci(35) is reasonably fast.
    """
    execution_time = timeit.timeit(lambda: fibonacci(35), number=10)
    assert execution_time < 1.0 # Should be well under 1 second
