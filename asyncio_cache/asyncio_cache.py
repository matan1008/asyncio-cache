from collections import namedtuple
from functools import update_wrapper
from typing import Union

################################################################################
# LRU Cache function decorator
################################################################################

_CacheInfo = namedtuple("CacheInfo", ["hits", "misses", "maxsize", "currsize"])
DEFAULT_FAST_TYPES = {int, str}


class _HashedSeq(list):
    """
    This class guarantees that hash() will be called no more than once
    per element.  This is important because the lru_cache() will hash
    the key multiple times on a cache miss.
    """

    __slots__ = 'hash_value'

    def __init__(self, tup):
        super().__init__()
        self[:] = tup
        self.hash_value = hash(tup)

    def __hash__(self):
        return self.hash_value

    def __eq__(self, other):
        return super().__eq__(other)


def _make_key(args, kwds, typed, kwd_mark=(object(),), fast_types=None):
    """Make a cache key from optionally typed positional and keyword arguments

    The key is constructed in a way that is flat as possible rather than
    as a nested structure that would take more memory.

    If there is only a single argument and its data type is known to cache
    its hash value, then that argument is returned without a wrapper.  This
    saves space and improves lookup speed.

    """
    # All of code below relies on kwds preserving the order input by the user.
    # Formerly, we sorted() the kwds before looping.  The new way is *much*
    # faster; however, it means that f(x=1, y=2) will now be treated as a
    # distinct call from f(y=2, x=1) which will be cached separately.
    if fast_types is None:
        fast_types = DEFAULT_FAST_TYPES
    key = args
    if kwds:
        key += kwd_mark
        for item in kwds.items():
            key += item
    if typed:
        key += tuple(type(v) for v in args)
        if kwds:
            key += tuple(type(v) for v in kwds.values())
    elif len(key) == 1 and type(key[0]) in fast_types:
        return key[0]
    return _HashedSeq(key)


def lru_cache(maxsize: Union[int, None] = 128, typed=False):
    """ Least-recently-used cache decorator.

    If *maxsize* is set to None, the LRU features are disabled and the cache
    can grow without bound.

    If *typed* is True, arguments of different types will be cached separately.
    For example, f(3.0) and f(3) will be treated as distinct calls with
    distinct results.

    Arguments to the cached function must be hashable.

    View the cache statistics named tuple (hits, misses, maxsize, currsize)
    with f.cache_info().  Clear the cache and statistics with f.cache_clear().
    Access the underlying function with f.__wrapped__.

    See:  http://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU)

    """

    # Users should only access the lru_cache through its public API:
    #       cache_info, cache_clear, and f.__wrapped__
    # The internals of the lru_cache are encapsulated for thread safety and
    # to allow the implementation to change (including a possible C version).

    if isinstance(maxsize, int):
        # Negative maxsize is treated as 0
        if maxsize < 0:
            maxsize = 0
    elif callable(maxsize) and isinstance(typed, bool):
        # The user_function was passed in directly via the maxsize argument
        user_function, maxsize = maxsize, 128
        wrapper = _lru_cache_wrapper(user_function, maxsize, typed)
        wrapper.cache_parameters = lambda: {'maxsize': maxsize, 'typed': typed}
        return update_wrapper(wrapper, user_function)
    elif maxsize is not None:
        raise TypeError('Expected first argument to be an integer, a callable, or None')

    def decorating_function(coroutine):
        lru_wrapper = _lru_cache_wrapper(coroutine, maxsize, typed)
        lru_wrapper.cache_parameters = lambda: {'maxsize': maxsize, 'typed': typed}
        return update_wrapper(lru_wrapper, coroutine)

    return decorating_function


def _lru_cache_wrapper(user_function, maxsize, typed):
    # Constants shared by all lru cache instances:
    sentinel = object()  # unique object used to signal cache misses
    link_prev_field, link_next_field, link_key_field, link_result_field = 0, 1, 2, 3  # names for the link fields

    local_cache = {}
    hits = misses = 0
    full = False
    root = []  # root of the circular doubly linked list
    root[:] = [root, root, None, None]  # initialize by pointing to self

    if maxsize == 0:
        async def wrapper(*args, **kwds):
            # No caching -- just a statistics update
            nonlocal misses
            misses += 1
            result = await user_function(*args, **kwds)
            return result

    elif maxsize is None:
        async def wrapper(*args, **kwds):
            # Simple caching without ordering or size limit
            nonlocal hits, misses
            key = _make_key(args, kwds, typed)
            result = local_cache.get(key, sentinel)
            if result is not sentinel:
                hits += 1
                return result
            misses += 1
            result = await user_function(*args, **kwds)
            local_cache[key] = result
            return result

    else:
        async def wrapper(*args, **kwds):
            # Size limited caching that tracks accesses by recency
            nonlocal root, hits, misses, full
            key = _make_key(args, kwds, typed)
            link = local_cache.get(key)
            if link is not None:
                # Move the link to the front of the circular queue
                link_prev, link_next, _key, result = link
                link_prev[link_next_field] = link_next
                link_next[link_prev_field] = link_prev
                last = root[link_prev_field]
                last[link_next_field] = root[link_prev_field] = link
                link[link_prev_field] = last
                link[link_next_field] = root
                hits += 1
                return result
            misses += 1
            result = await user_function(*args, **kwds)
            if key in local_cache:
                # Getting here means that this same key was added to the
                # cache while the lock was released.  Since the link
                # update is already done, we need only return the
                # computed result and update the count of misses.
                pass
            elif full:
                # Use the old root to store the new key and result.
                old_root = root
                old_root[link_key_field] = key
                old_root[link_result_field] = result
                # Empty the oldest link and make it the new root.
                # Keep a reference to the old key and old result to
                # prevent their ref counts from going to zero during the
                # update. That will prevent potentially arbitrary object
                # clean-up code (i.e. __del__) from running while we're
                # still adjusting the links.
                root = old_root[link_next_field]
                old_key = root[link_key_field]
                root[link_key_field] = root[link_result_field] = None
                # Now update the cache dictionary.
                del local_cache[old_key]
                # Save the potentially reentrant cache[key] assignment
                # for last, after the root and links have been put in
                # a consistent state.
                local_cache[key] = old_root
            else:
                # Put result in a new link at the front of the queue.
                last = root[link_prev_field]
                link = [last, root, key, result]
                last[link_next_field] = root[link_prev_field] = local_cache[key] = link
                # Use the cache_len bound method instead of the len() function
                # which could potentially be wrapped in an lru_cache itself.
                full = (len(local_cache) >= maxsize)
            return result

    def cache_info():
        """ Report cache statistics """
        return _CacheInfo(hits, misses, maxsize, len(local_cache))

    def cache_clear():
        """ Clear the cache and cache statistics """
        nonlocal hits, misses, full
        local_cache.clear()
        root[:] = [root, root, None, None]
        hits = misses = 0
        full = False

    wrapper.cache_info = cache_info
    wrapper.cache_clear = cache_clear
    return wrapper


################################################################################
# cache -- simplified access to the infinity cache
################################################################################

def cache(user_function):
    """Simple lightweight unbounded cache.  Sometimes called "memoize"."""
    return lru_cache(maxsize=None)(user_function)
