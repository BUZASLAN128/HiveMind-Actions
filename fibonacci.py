def fibonacci(n: int) -> int:
    """
    Calculates the nth Fibonacci number using an iterative approach.

    Args:
        n: The index of the Fibonacci number to calculate.

    Returns:
        The nth Fibonacci number.
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

def fibonacci_recursive(n: int) -> int:
    """
    Calculates the nth Fibonacci number using a recursive approach.

    Args:
        n: The index of the Fibonacci number to calculate.

    Returns:
        The nth Fibonacci number.
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)
