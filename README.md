[![Python application](https://github.com/matan1008/asyncio-cache/workflows/Python%20application/badge.svg)](https://github.com/matan1008/asyncio-cache/actions/workflows/python-app.yml "Python application action")
[![Pypi version](https://img.shields.io/pypi/v/asyncio-cache.svg)](https://pypi.org/project/asyncio-cache/ "PyPi package")
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/matan1008/asyncio-cache.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/matan1008/asyncio-cache/context:python)


# asyncio-cache

A python library for asyncio caches (like functools cache and lru_cache)

# Installation

Install the last released version using `pip`:

```shell
python3 -m pip install --user -U asyncio-cache
```

Or install the latest version from sources:

```shell
git clone git@github.com:matan1008/asyncio-cache.git
cd asyncio-cache
python3 -m pip install --user -U -e .
```

# Usage

The usage is similar to `functools.cache` and `functools.lru_cache` usage:

```python
from asyncio_cache import cache


@cache
async def cached_read(reader):
    return await reader.read(100)
```