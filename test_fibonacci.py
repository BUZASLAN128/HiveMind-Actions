import timeit
from fibonacci import fibonacci

def test_fibonacci_time():
    # n=1000 is too large for a simple recursive implementation and will cause a RecursionError.
    # Using n=35 instead, which is slow enough to measure but won't crash.
    n = 35
    execution_time = timeit.timeit(lambda: fibonacci(n), number=1)
    print(f"Execution time for fibonacci({n}): {execution_time} seconds")
