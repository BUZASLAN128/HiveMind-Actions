import time
from collections import OrderedDict
from threading import Lock

class LRUCache:
    """
    A thread-safe LRU cache with TTL support.
    """

    def __init__(self, max_size=128, ttl=60):
        """
        Initialize the cache.
        Args:
            max_size (int): The maximum number of items in the cache.
            ttl (int): The time-to-live for cache items in seconds.
        """
        self.max_size = max_size
        self.ttl = ttl
        self.lock = Lock()
        self.cache = OrderedDict()
        self.expirations = {}

    def get(self, key):
        """
        Get an item from the cache.
        Args:
            key: The key of the item to get.
        Returns:
            The value of the item, or None if the item is not in the cache or has expired.
        """
        with self.lock:
            if key not in self.cache:
                return None

            if self._is_expired(key):
                self._delete_internal(key)
                return None

            self.cache.move_to_end(key)
            return self.cache[key]

    def set(self, key, value):
        """
        Set an item in the cache.
        Args:
            key: The key of the item to set.
            value: The value of the item to set.
        """
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)

            self.cache[key] = value
            self.expirations[key] = time.time() + self.ttl

            if len(self.cache) > self.max_size:
                # Pop the least recently used item
                oldest_key, _ = self.cache.popitem(last=False)
                del self.expirations[oldest_key]


    def delete(self, key):
        """
        Delete an item from the cache.
        Args:
            key: The key of the item to delete.
        """
        with self.lock:
            self._delete_internal(key)

    def _delete_internal(self, key):
        """
        Internal delete method that does not acquire a lock.
        """
        if key in self.cache:
            del self.cache[key]
            del self.expirations[key]

    def _is_expired(self, key):
        """
        Check if an item has expired.
        Args:
            key: The key of the item to check.
        Returns:
            True if the item has expired, False otherwise.
        """
        return time.time() > self.expirations.get(key, 0)

    def size(self):
        """
        Return the current size of the cache.
        """
        with self.lock:
            return len(self.cache)
