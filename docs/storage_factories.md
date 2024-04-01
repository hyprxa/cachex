# Storage Factories
`cachex` supports multiple storage backends and can be extended to support many more. These backends can be mixed and matched throughout an application. For example, it is possible to have one function use system memory to cache a result while another function can use Redis.

```python
from typing import Any

from cachex import (
    async_cache_value,
    async_redis_storage_factory,
    cache_value,
    redis_storage_factory,
)


REDIS_URL = "redis://localhost:6379/"


@cache_value(storage_factory=redis_storage_factory(REDIS_URL))
def do_something(*args: Any, **kwargs: Any) -> Any:
    ...


@async_cache_value(storage_factory=async_redis_storage_factory(REDIS_URL))
async def do_something_else(*args: Any, **kwargs: Any) -> Any:
    ...


@cache_value() # If no storage factory is specified, the value is cached in memory
def cache_this_result_in_memory(*args: Any, **kwargs: Any) -> Any:
    ...
```

`cachex` uses the concept of *storage factories* to define which backend is used per function. A storage factory is a zero argument callable that returns a `Storage` or `AsyncStorage` object. The callables used in the example above are actually more like storage factory *factories*, they wrap the configuration of a storage backend and return a factory function (zero argument callable). This is best illustrated in the source code for `redis_storage_factory`...

```python
def redis_storage_factory(
    url: str,
    key_prefix: str | None = None,
    **client_kwargs: Any,
) -> Callable[[], RedisStorage]:
    """Storage factory for :class: `RedisStorage <cacachex.storage.redis.RedisStorage>`

    Args:
        url: Redis url to connect to
        key_prefix: Virtual key namespace to use in the db
        client_kwargs: Additional keyword arguments to pass to the
            :method:`redis.Redis.from_url` classmethod
    """
    from redis import Redis
    from cachex.storage.redis import RedisStorage

    def wrapper() -> RedisStorage:
        redis = Redis.from_url(url, **client_kwargs)
        return RedisStorage(redis, key_prefix=key_prefix)

    return wrapper
```

# Factory Keys
`Storage` and `AsyncStorage` implementations usually involve a client object (`RedisStorage` uses a `redis.Redis` client under the hood). It would be very inefficient to create a new storage backend on every call to a cached function. Instead, we want to reuse the backend (and its client connection(s)). Therefore, under the hood, storage factories are wrapped in a call to `cache_reference`. This ensures we only create a single storage instance (thus reusing the underlying client objects). However, this implementation also leads to some unintuitive side effects. For example...

```python
from cachex import cache_value, redis_storage_factory


REDIS_URL = "redis://localhost:6379/"


@cache_value(storage_factory=redis_storage_factory(REDIS_URL, key_prefix="called_first"))
def static(n: int) -> int:
    return 7


@cache_value(storage_factory=redis_storage_factory(REDIS_URL, key_prefix="called_second"))
def echo(n: int) -> int:
    return n


if __name__ == "__main__":
    print(static(1))
    print(echo(1))
```

If you run this, the output will be...
```
7
7
```

This is unintuitve because we defined a `key_prefix` which should partition the key spaces and the calls `static(1)` and `echo(1)` should generate cache keys like `called_first:hash(1)` and `called_second(hash(1))` respectively. Instead there is a cache hit so instead of getting `7` and `1` as outputs we get `7` and `7` because `echo(1)` returns the cached value from `static(1)`.

So why does this happen? Remember that a storage factory is a zero argument callable that returns a storage backend. And, in order to not create a new storage backend on every call, the factory function is wrapped in `cache_reference` under the hood. The signature looks like `cache_reference(Callable[[], Storage | AsyncStorage])()`. Do you see the issue? `cache_reference` doesn't know that the `key_prefix` argument is different because `redis_storage_factory` is just a wrapper that returns a callable. Utimately it looks like two different storage backends are being configured but only one is ever created and it will have the configuration of whichever function is called first. For example, if we switch the order in which we call `static` and `echo`...

```python
if __name__ == "__main__":
    print(echo(1))
    print(static(1))
```

The outut will be...
```
1
1
```

In order to differentiate the configurations we need to provide a *factory key*...

```python
from cachex import cache_value, redis_storage_factory


REDIS_URL = "redis://localhost:6379/"


@cache_value(storage_factory=redis_storage_factory(REDIS_URL, key_prefix="called_first"), factory_key="called_first")
def static(n: int) -> int:
    return 7


@cache_value(storage_factory=redis_storage_factory(REDIS_URL, key_prefix="called_second"), factory_key="called_first")
def echo(n: int) -> int:
    return n


if __name__ == "__main__":
    print(static(1))
    print(echo(1))
```

Now when we run this, we get the expected result...
```
7
1
```