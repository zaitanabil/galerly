"""
Production-grade in-memory cache for API responses
Reduces DynamoDB read costs and improves response times

This module provides a thread-safe, TTL-based caching layer with:
- Automatic expiration of stale entries
- Pattern-based cache invalidation
- Deterministic key generation from complex objects
- Performance monitoring and logging
"""
import time
from functools import wraps
import hashlib
import json
from threading import Lock
from typing import Any, Optional, Dict, Tuple


class TTLCache:
    """
    Thread-safe in-memory cache with Time-To-Live (TTL) expiration.
    
    Features:
    - Automatic cleanup of expired entries
    - Pattern-based bulk invalidation
    - Thread-safe operations
    - Configurable TTL per entry
    
    Usage:
        cache = TTLCache()
        cache.store('user:123', user_data, ttl=300)
        data = cache.retrieve('user:123')
        cache.invalidate_pattern('user:')
    """
    
    def __init__(self):
        """Initialize cache with empty storage and thread lock."""
        self._storage: Dict[str, Any] = {}
        self._expiration_times: Dict[str, float] = {}
        self._lock = Lock()
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache if not expired.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        with self._lock:
            if key in self._storage:
                if self._expiration_times[key] > time.time():
                    return self._storage[key]
                else:
                    # Entry expired, remove it
                    self._remove_entry(key)
            return None
    
    def store(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        Store value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (default: 300 = 5 minutes)
        """
        with self._lock:
            self._storage[key] = value
            self._expiration_times[key] = time.time() + ttl
    
    def remove(self, key: str) -> None:
        """
        Remove specific key from cache.
        
        Args:
            key: Cache key to remove
        """
        with self._lock:
            self._remove_entry(key)
    
    def _remove_entry(self, key: str) -> None:
        """
        Internal method to remove entry without lock.
        Must be called within locked context.
        
        Args:
            key: Cache key to remove
        """
        if key in self._storage:
            del self._storage[key]
            del self._expiration_times[key]
    
    def clear_all(self) -> None:
        """Clear entire cache."""
        with self._lock:
            self._storage.clear()
            self._expiration_times.clear()
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching pattern (substring match).
        
        Args:
            pattern: Pattern to match against cache keys
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_remove = [k for k in self._storage.keys() if pattern in k]
            for key in keys_to_remove:
                self._remove_entry(key)
            return len(keys_to_remove)
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache metrics
        """
        with self._lock:
            total_entries = len(self._storage)
            expired_entries = sum(
                1 for exp_time in self._expiration_times.values() 
                if exp_time <= time.time()
            )
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries
            }


# Global cache instance for application-wide use
application_cache = TTLCache()


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate deterministic cache key from function arguments.
    
    Handles complex data types (dicts, lists) by hashing their JSON representation.
    Ensures consistent key generation regardless of argument order.
    
    Args:
        prefix: Cache key prefix (e.g., 'gallery_list', 'photo_details')
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Colon-separated cache key string
        
    Example:
        >>> generate_cache_key('user', 'user123', role='admin')
        'user:user123:role=admin'
    """
    key_components = [prefix]
    
    # Process positional arguments
    for argument in args:
        if isinstance(argument, (dict, list)):
            # Hash complex objects for deterministic keys
            serialized = json.dumps(argument, sort_keys=True)
            hash_digest = hashlib.md5(serialized.encode()).hexdigest()[:8]
            key_components.append(hash_digest)
        else:
            key_components.append(str(argument))
    
    # Process keyword arguments (sorted for determinism)
    for param_name, param_value in sorted(kwargs.items()):
        if isinstance(param_value, (dict, list)):
            serialized = json.dumps(param_value, sort_keys=True)
            hash_digest = hashlib.md5(serialized.encode()).hexdigest()[:8]
            key_components.append(f"{param_name}={hash_digest}")
        else:
            key_components.append(f"{param_name}={param_value}")
    
    return ':'.join(key_components)


def cache_response(ttl: int = 300, key_prefix: str = 'default'):
    """
    Decorator to cache function results with automatic key generation.
    
    This decorator is suitable for pure functions with simple parameters.
    For complex handler functions, use manual caching with retrieve/store.
    
    Args:
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)
        key_prefix: Prefix for cache key generation
        
    Returns:
        Decorated function with caching behavior
        
    Example:
        @cache_response(ttl=600, key_prefix='user_profile')
        def get_user_profile(user_id: str) -> dict:
            return query_database(user_id)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate deterministic cache key
            cache_key = generate_cache_key(key_prefix, *args, **kwargs)
            
            # Attempt cache retrieval
            cached_value = application_cache.retrieve(cache_key)
            if cached_value is not None:
                print(f"✅ Cache HIT: {cache_key}")
                return cached_value
            
            # Cache miss - execute function
            print(f"⚠️  Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            
            # Store result in cache
            application_cache.store(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def invalidate_cache_entries(pattern: str) -> None:
    """
    Invalidate cache entries matching the specified pattern.
    
    Uses substring matching to clear related cache entries.
    Logs the invalidation for monitoring purposes.
    
    Args:
        pattern: Pattern to match against cache keys (substring)
        
    Example:
        # Invalidate all gallery caches for a user
        invalidate_cache_entries('gallery_list:user123')
        
        # Invalidate specific gallery
        invalidate_cache_entries('gallery:abc123')
    """
    count = application_cache.invalidate_pattern(pattern)
    print(f"🗑️  Cache invalidated: pattern='{pattern}', entries={count}")


# Domain-specific cache invalidation helpers
def invalidate_user_gallery_caches(user_id: str) -> None:
    """
    Invalidate all gallery list caches for a specific user.
    
    Called when user's galleries are modified (created, updated, deleted).
    
    Args:
        user_id: User identifier
    """
    invalidate_cache_entries(f'gallery_list:{user_id}')


def invalidate_gallery_caches(gallery_id: str) -> None:
    """
    Invalidate all caches related to a specific gallery.
    
    Called when gallery or its photos are modified.
    
    Args:
        gallery_id: Gallery identifier
    """
    invalidate_cache_entries(f'gallery:{gallery_id}')
    invalidate_cache_entries(f'gallery_photos:{gallery_id}')


def invalidate_photo_caches(photo_id: str) -> None:
    """
    Invalidate all caches related to a specific photo.
    
    Called when photo is modified or deleted.
    
    Args:
        photo_id: Photo identifier
    """
    invalidate_cache_entries(f'photo:{photo_id}')


# Backwards compatibility aliases (deprecated but maintained for existing code)
cache = application_cache
cache_key = generate_cache_key
cached = cache_response
invalidate_cache = invalidate_cache_entries
invalidate_user_galleries = invalidate_user_gallery_caches
invalidate_gallery = invalidate_gallery_caches
invalidate_photo = invalidate_photo_caches
