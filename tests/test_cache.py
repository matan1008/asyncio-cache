import pytest

from asyncio_cache import cache


class CallsCounter:
    def __init__(self):
        self.count = 0

    @cache
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
async def test_not_caching_different_args():
    counter = CallsCounter()
    assert await counter.call(3) == 'called'
    assert await counter.call(4) == 'called'
    assert counter.count == 2


@pytest.mark.asyncio
async def test_clear_caching():
    counter = CallsCounter()
    assert await counter.call(3) == 'called'
    counter.call.cache_clear()
    assert await counter.call(3) == 'called'
    assert counter.count == 2
