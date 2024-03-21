# Data Caching
Typically, when using Cachex, you will be caching data - HTTP response data, database query results, ML model outputs etc. are common datasets that you would want to cache. In those cases you will be using the `cache_value` and `async_cache_value` API's for sync and async contexts respectively.

Cachex uses `pickle` to serialize the return value of a deorated function. This has a few implications, though none more important than this...

**Only ever use Cachex in trusted environments. The `pickle` module is not secure and you should only ever unpickle data you trust**

Security concerns aside, using `pickle` also has some advantages...
- The data is stored in a binary format which means that **any storage service** can be used to store cached data, even ones not officially supported by Cachex
- Every cache hit returns a **copy** of the original data. This means multiple handlers can mutate the data without side effects
```python
import asyncio
import time

from cachex import async_cache_value, cache_value


class Result:
    def __init__(self) -> None:
        self.id = id(self)


@cache_value()
def sim_long_op(n: int) -> Result:
    """Simulate a long operation by sleeping and return a result."""
    time.sleep(n)
    return Result()



```