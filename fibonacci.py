
import sys

# Adjust the recursion limit to handle deeper recursions, e.g., for fibonacci(35)
# Note: The theoretical limit is platform-dependent, but this is a practical increase.
sys.setrecursionlimit(2000)

def fibonacci(n: int) -> int:
    """
    Calculates the nth Fibonacci number using a recursive approach.

    Args:
        n: The non-negative integer input.

    Returns:
        The nth Fibonacci number.

    Raises:
        ValueError: If the input n is negative.
    """
    if n < 0:
        raise ValueError("Input must be a non-negative integer")
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)
