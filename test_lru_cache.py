import time
import threading
from lru_cache import LRUCache

def test_set_and_get():
    cache = LRUCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1
    assert cache.get("b") == 2

def test_lru_eviction():
    cache = LRUCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3

def test_delete():
    cache = LRUCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.delete("a")
    assert cache.get("a") is None
    assert cache.get("b") == 2

def test_ttl_expiration():
    cache = LRUCache(max_size=2, ttl=0.1)
    cache.set("a", 1)
    assert cache.get("a") == 1
    time.sleep(0.2)
    assert cache.get("a") is None

def test_thread_safety():
    cache = LRUCache(max_size=50)
    num_threads = 10
    items_per_thread = 10

    def worker(thread_id):
        for i in range(items_per_thread):
            key = f"key-{thread_id}-{i}"
            value = f"value-{thread_id}-{i}"
            cache.set(key, value)
            retrieved_value = cache.get(key)
            assert retrieved_value == value

    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # After all threads, the cache size should be at its max_size
    assert cache.size() == cache.max_size
