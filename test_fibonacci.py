import time
from fibonacci import fibonacci

def test_fibonacci_performance():
    start_time = time.time()
    try:
        # This will cause a RecursionError, which is the intended behavior to demonstrate.
        result = fibonacci(1000)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Fibonacci(1000) result: {result}")
        print(f"Execution time for fibonacci(1000): {execution_time:.4f} seconds")
    except RecursionError:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"fibonacci(1000) exceeded the maximum recursion depth after {execution_time:.4f} seconds.")

if __name__ == "__main__":
    test_fibonacci_performance()
