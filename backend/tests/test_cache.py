"""
Tests for cache.py utility.
Tests cover: TTLCache class, cache operations, invalidation, thread safety, statistics.
"""
import pytest
import time
import threading
from unittest.mock import Mock, patch

# Test: TTLCache basic operations
class TestTTLCacheBasicOperations:
    """Tests for basic cache operations (retrieve, store, remove)."""
    
    def test_cache_store_and_retrieve(self):
        """Store and retrieve value from cache."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        cache.store('test_key', 'test_value', ttl=60)
        
        result = cache.retrieve('test_key')
        assert result == 'test_value'
    
    def test_cache_retrieve_nonexistent(self):
        """Retrieve nonexistent key returns None."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        result = cache.retrieve('nonexistent')
        
        assert result is None
    
    def test_cache_ttl_expiration(self):
        """Cache entry expires after TTL."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        cache.store('test_key', 'test_value', ttl=1)  # 1 second TTL
        
        # Should exist immediately
        assert cache.retrieve('test_key') == 'test_value'
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.retrieve('test_key') is None
    
    def test_cache_remove(self):
        """Remove entry from cache."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        cache.store('test_key', 'test_value', ttl=60)
        
        # Entry exists
        assert cache.retrieve('test_key') == 'test_value'
        
        # Remove entry
        cache.remove('test_key')
        
        # Entry should not exist
        assert cache.retrieve('test_key') is None
    
    def test_cache_clear(self):
        """Clear all cache entries."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        cache.store('key1', 'value1', ttl=60)
        cache.store('key2', 'value2', ttl=60)
        cache.store('key3', 'value3', ttl=60)
        
        # All entries exist
        assert cache.retrieve('key1') == 'value1'
        assert cache.retrieve('key2') == 'value2'
        assert cache.retrieve('key3') == 'value3'
        
        # Clear cache
        cache.clear()
        
        # All entries should be gone
        assert cache.retrieve('key1') is None
        assert cache.retrieve('key2') is None
        assert cache.retrieve('key3') is None

# Test: Cache key generation
class TestCacheKeyGeneration:
    """Tests for generate_cache_key function."""
    
    def test_generate_cache_key_simple(self):
        """Generate cache key with simple parameters."""
        from utils.cache import generate_cache_key
        
        key = generate_cache_key('resource', 'id123')
        
        assert 'resource' in key
        assert 'id123' in key
    
    def test_generate_cache_key_with_kwargs(self):
        """Generate cache key with keyword arguments."""
        from utils.cache import generate_cache_key
        
        key = generate_cache_key('gallery', 'user123', page=1, size=50)
        
        assert 'gallery' in key
        assert 'user123' in key
        assert 'page' in key or '1' in key
        assert 'size' in key or '50' in key
    
    def test_generate_cache_key_deterministic(self):
        """Cache key generation is deterministic."""
        from utils.cache import generate_cache_key
        
        key1 = generate_cache_key('resource', 'id', param='value')
        key2 = generate_cache_key('resource', 'id', param='value')
        
        assert key1 == key2
    
    def test_generate_cache_key_different_params(self):
        """Different parameters generate different keys."""
        from utils.cache import generate_cache_key
        
        key1 = generate_cache_key('resource', 'id1')
        key2 = generate_cache_key('resource', 'id2')
        
        assert key1 != key2

# Test: Pattern-based invalidation
class TestCacheInvalidation:
    """Tests for invalidate_pattern function."""
    
    def test_invalidate_pattern_removes_matching(self):
        """Invalidate pattern removes matching keys."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        cache.store('user:123:profile', 'data1', ttl=60)
        cache.store('user:123:settings', 'data2', ttl=60)
        cache.store('user:456:profile', 'data3', ttl=60)
        
        # Invalidate user:123 keys
        count = cache.invalidate_pattern('user:123')
        
        assert count == 2
        assert cache.retrieve('user:123:profile') is None
        assert cache.retrieve('user:123:settings') is None
        assert cache.retrieve('user:456:profile') == 'data3'  # Not invalidated
    
    def test_invalidate_pattern_returns_count(self):
        """Invalidate pattern returns count of invalidated entries."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        cache.store('gallery:abc:photo1', 'data1', ttl=60)
        cache.store('gallery:abc:photo2', 'data2', ttl=60)
        cache.store('gallery:abc:photo3', 'data3', ttl=60)
        
        count = cache.invalidate_pattern('gallery:abc')
        
        assert count == 3
    
    def test_invalidate_pattern_no_matches(self):
        """Invalidate pattern with no matches returns 0."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        cache.store('key1', 'value1', ttl=60)
        
        count = cache.invalidate_pattern('nomatch')
        
        assert count == 0
        assert cache.retrieve('key1') == 'value1'  # Unaffected

# Test: Helper invalidation functions
class TestInvalidationHelpers:
    """Tests for invalidate_user_gallery_caches and invalidate_gallery_caches."""
    
    def test_invalidate_user_gallery_caches(self):
        """Invalidate user gallery caches."""
        from utils.cache import application_cache, invalidate_user_gallery_caches, generate_cache_key
        
        # Store some user gallery caches
        user_id = 'user123'
        key = generate_cache_key('gallery_list', user_id)
        application_cache.store(key, {'galleries': []}, ttl=60)
        
        # Invalidate
        invalidate_user_gallery_caches(user_id)
        
        # Should be invalidated
        assert application_cache.retrieve(key) is None
    
    def test_invalidate_gallery_caches(self):
        """Invalidate specific gallery caches."""
        from utils.cache import application_cache, invalidate_gallery_caches, generate_cache_key
        
        # Store gallery cache
        gallery_id = 'gallery123'
        key = generate_cache_key('gallery', gallery_id)
        application_cache.store(key, {'gallery': 'data'}, ttl=60)
        
        # Invalidate
        invalidate_gallery_caches(gallery_id)
        
        # Should be invalidated
        assert application_cache.retrieve(key) is None

# Test: Cache decorator
class TestCacheDecorator:
    """Tests for cache_response decorator."""
    
    def test_cache_response_decorator_caches_result(self):
        """cache_response decorator caches function result."""
        from utils.cache import cache_response, application_cache
        
        call_count = {'count': 0}
        
        @cache_response(ttl=60)
        def expensive_function(user_id):
            call_count['count'] += 1
            return {'user_id': user_id, 'data': 'expensive'}
        
        # First call
        result1 = expensive_function('user123')
        assert result1['user_id'] == 'user123'
        assert call_count['count'] == 1
        
        # Second call should use cache
        result2 = expensive_function('user123')
        assert result2['user_id'] == 'user123'
        assert call_count['count'] == 1  # Not called again
    
    def test_cache_response_different_args(self):
        """cache_response decorator uses different cache for different args."""
        from utils.cache import cache_response
        
        call_count = {'count': 0}
        
        @cache_response(ttl=60)
        def fetch_data(resource_id):
            call_count['count'] += 1
            return {'id': resource_id}
        
        # Different arguments should not share cache
        result1 = fetch_data('id1')
        result2 = fetch_data('id2')
        
        assert result1['id'] == 'id1'
        assert result2['id'] == 'id2'
        assert call_count['count'] == 2  # Called twice

# Test: Thread safety
class TestCacheThreadSafety:
    """Tests for thread-safe cache operations."""
    
    def test_concurrent_store_and_retrieve(self):
        """Cache handles concurrent store and retrieve operations."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        errors = []
        
        def store_values(start, end):
            try:
                for i in range(start, end):
                    cache.store(f'key{i}', f'value{i}', ttl=60)
            except Exception as e:
                errors.append(e)
        
        def retrieve_values(start, end):
            try:
                for i in range(start, end):
                    cache.retrieve(f'key{i}')
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        threads.append(threading.Thread(target=store_values, args=(0, 50)))
        threads.append(threading.Thread(target=store_values, args=(50, 100)))
        threads.append(threading.Thread(target=retrieve_values, args=(0, 50)))
        threads.append(threading.Thread(target=retrieve_values, args=(50, 100)))
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # No errors should occur
        assert len(errors) == 0
    
    def test_concurrent_invalidation(self):
        """Cache handles concurrent invalidation safely."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        
        # Pre-populate cache
        for i in range(100):
            cache.store(f'resource:{i}', f'value{i}', ttl=60)
        
        errors = []
        
        def invalidate_pattern_thread(pattern):
            try:
                cache.invalidate_pattern(pattern)
            except Exception as e:
                errors.append(e)
        
        # Create multiple invalidation threads
        threads = []
        for i in range(10):
            threads.append(threading.Thread(target=invalidate_pattern_thread, args=(f'resource:{i}',)))
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # No errors should occur
        assert len(errors) == 0

# Test: Cache statistics
class TestCacheStatistics:
    """Tests for cache statistics tracking."""
    
    def test_statistics_track_hits_and_misses(self):
        """Cache statistics track hits and misses."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        
        # Store a value
        cache.store('key1', 'value1', ttl=60)
        
        # Hit
        cache.retrieve('key1')
        
        # Miss
        cache.retrieve('nonexistent')
        
        # Get statistics
        stats = cache.get_statistics()
        
        assert 'hits' in stats
        assert 'misses' in stats
        assert stats['hits'] >= 1
        assert stats['misses'] >= 1
    
    def test_statistics_calculate_hit_rate(self):
        """Cache statistics calculate hit rate."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        cache.store('key1', 'value1', ttl=60)
        
        # 2 hits
        cache.retrieve('key1')
        cache.retrieve('key1')
        
        # 1 miss
        cache.retrieve('nonexistent')
        
        stats = cache.get_statistics()
        
        assert 'hit_rate' in stats
        assert isinstance(stats['hit_rate'], float)
        assert 0 <= stats['hit_rate'] <= 100

# Test: Backwards compatibility
class TestBackwardsCompatibility:
    """Tests for backwards compatibility aliases."""
    
    def test_old_method_names_work(self):
        """Old method names (get, set, delete) still work."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        
        # Old method names should work
        cache.set('key1', 'value1', ttl=60)
        assert cache.get('key1') == 'value1'
        
        cache.delete('key1')
        assert cache.get('key1') is None
    
    def test_clear_pattern_alias(self):
        """clear_pattern alias works."""
        from utils.cache import TTLCache
        
        cache = TTLCache()
        cache.store('test:1', 'val1', ttl=60)
        cache.store('test:2', 'val2', ttl=60)
        
        # Old alias
        count = cache.clear_pattern('test')
        
        assert count == 2

