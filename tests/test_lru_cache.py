import pytest

from asyncio_cache.asyncio_cache import lru_cache


class CallsCounter:
    def __init__(self):
        self.count = 0

    @lru_cache
    async def call(self, arg):
        self.count += 1
        return 'called'


@pytest.mark.asyncio
async def test_caching():
    counter = CallsCounter()
    assert await counter.call(3) == 'called'
    assert await counter.call(3) == 'called'
    assert counter.count == 1


@pytest.mark.asyncio
async def test_invalidate_cache():
    counter = CallsCounter()
    cache_info = counter.call.cache_info()
    # Fill all blocks of the cache.
    for i in range(cache_info.maxsize):
        assert await counter.call(i) == 'called'
        assert counter.count == i + 1
    # Check that the first filled block is cached.
    assert await counter.call(0) == 'called'
    assert counter.count == cache_info.maxsize
    # Check that a new block is not cached.
    assert await counter.call(cache_info.maxsize) == 'called'
    assert counter.count == cache_info.maxsize + 1
    # Check that the block least used is not cached.
    assert await counter.call(1) == 'called'
    assert counter.count == cache_info.maxsize + 2
    # Check that a recently used block is cached.
    assert await counter.call(0) == 'called'
    assert counter.count == cache_info.maxsize + 2
