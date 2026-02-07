import time
import os
from pathlib import Path
import gc

# Create a large dummy file (e.g., 50MB)
FILE_SIZE = 50 * 1024 * 1024
FILENAME = "large_test_file.txt"
READ_LIMIT = 2000
ITERATIONS = 5

def create_large_file():
    with open(FILENAME, "w", encoding="utf-8") as f:
        f.write("A" * FILE_SIZE)

def benchmark_read_text_slice():
    start_time = time.time()
    for _ in range(ITERATIONS):
        content = Path(FILENAME).read_text(encoding="utf-8")[:READ_LIMIT]
    end_time = time.time()
    return (end_time - start_time) / ITERATIONS

def benchmark_open_read_limit():
    start_time = time.time()
    for _ in range(ITERATIONS):
        with open(FILENAME, "r", encoding="utf-8") as f:
            content = f.read(READ_LIMIT)
    end_time = time.time()
    return (end_time - start_time) / ITERATIONS

if __name__ == "__main__":
    create_large_file()
    try:
        print(f"Benchmarking file read methods on a {FILE_SIZE/1024/1024:.0f}MB file with read limit {READ_LIMIT} chars")

        # Test Unoptimized
        gc.collect()
        time_unopt = benchmark_read_text_slice()
        print(f"Unoptimized (read_text()[:limit]): {time_unopt:.6f}s")

        # Test Optimized
        gc.collect()
        time_opt = benchmark_open_read_limit()
        print(f"Optimized (open().read(limit)):   {time_opt:.6f}s")

        # Comparison
        print(f"\nSpeedup: {time_unopt / time_opt:.2f}x")

    finally:
        if os.path.exists(FILENAME):
            os.remove(FILENAME)
