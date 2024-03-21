# Storage Factories and Factory Keys
Multiple storage backends and multiple instances of a backend can be used by leveraging storage factories and factory keys. A storage factory is a callable that returns either a `cachex.storage.Storage` or `cachex.storage.AsyncStorage` object. It must be a zero argument callable. Cachex has storage factories for all variants of its supported backends.

```python
from typing import Any

from cachex import (
    async_cache_value,
    async_redis_storage_factory,
    cache_value,
    redis_storage_factory,
)


REDIS_URL = "redis://localhost:6379/


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

The implementation of storage factories can lead to some unintuitive results. Cachex uses `cachex.cache_reference` internally to turn any storage factory into a singleton. And, because storage factories reduce down to zero argument callables, you can only ever end up with 1 storage instance for any factory function even though it looks like the two factories are configured differently. For example...

```python
from cachex import cache_value, file_storage_factory


# file_storage_factory is not actually a storage factory. It is more like a
# a storage factory configuration: it returns a zero argument callable (i.e a
# storage factory)
storage_factory = file_storage_factory("/test")
print(storage_factory)
storage_instance = storage_factory() # zero args
print(storage_instance)
print(storage_instance.path)

# Lets configure a new storage factory for a different path
storage_factory_2 = file_storage_factory("/test_other_path")
print(storage_factory_2)
storage_instance_2 = storage_factory_2()
print(storage_instance_2)
print(storage_instance_2.path)


# So lets try and use our two different storage factories in
```