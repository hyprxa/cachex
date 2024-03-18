# Modern Python Caching
Cachex is a modern caching library for Python 3 built from the ground up to support type hints. It has built in Redis, MongoDB and Memcached support and provides both sync and async APIs for all storage backends.

## Installation
`pip install cachex`

### Redis Dependencies:
`pip install cachex[redis]`

### MongoDB Dependencies:
`pip install cachex[mongo]`

### Memcached Dependencies:
No additional dependencies are required for Memcached support. Unlike Redis and MongoDB, there is not a single client library supported by the core dev team and most libraries do not support both sync and async API's. For that reason, the Memcached storage backend is implemented as an interface based API. You bring your own client, and as long as that client adheres to the `MemcachedClient` or `AsyncMemcachedClient` interfaces it will work with Cachex.

## Basic Usage
Cachex is a decorator based, functional API. Built with typing in mind along with built in Redis support, it is a great choice as a caching layer in popular web framworks like [FastAPI](https://fastapi.tiangolo.com/)

```python
from enum import Enum
from typing import Annotated

import pandas as pd
from cachex import cache_value
from fastapi import Depends, FastAPI, Response
from pydantic import AnyHttpUrl
from pydantic_core import Url


app = FastAPI()

class DataSet(Enum):
    UBER1 = "uber1"
    UBER2 = "uber2"
    UBER3 = "uber3"

URLS: dict[DataSet, AnyHttpUrl] = {
    DataSet.UBER1: AnyHttpUrl("https://github.com/plotly/datasets/raw/master/uber-rides-data1.csv"),
    DataSet.UBER2: AnyHttpUrl("https://github.com/plotly/datasets/raw/master/uber-rides-data2.csv"),
    DataSet.UBER3: AnyHttpUrl("https://github.com/plotly/datasets/raw/master/uber-rides-data3.csv"),
}


def get_url(dataset: DataSet) -> AnyHttpUrl:
    """Get the dataset URL from the global mapping."""
    return URLS[dataset]


@cache_value(type_encoders={Url: lambda t: t.unicode_string()})
def download_csv_data(url: Annotated[AnyHttpUrl, Depends(get_url)]) -> pd.DataFrame:
    """Download a CSV file from the given URL and convert it to a DataFrame."""
    return pd.read_csv(url.unicode_string())


@app.get("/datasets/{dataset}")
def get_dataset(df: Annotated[pd.DataFrame, Depends(download_csv_data)]):
    """Download a CSV dataset from the web and return the data in JSON form."""
    data = df.iloc[0:1000, :].to_json(orient="records", indent=2)
    return Response(content=data, media_type="application/json")
```

Save the script, call it `main.py`. Run the app with `uvicorn main:app` and head to the docs (`/docs`). The swagger docs show the correct API arguments and types through the dependency chain

![Alt text](/docs/img/simple_app_docs.png)

Then hit the `/datasets/uber1` endpoint. Depending on your internet connection, this may take 2-30 seconds to run. After it runs once, hit a again, it should load almost instantly! You can then repeat this with the `/datasets/uber2` and `datasets/uber3` endpoints.

## Typing Support
Cachex was built to work with Python 3.6+ type declarations. This means it offers great editor support for decorated functions. It also means that Cachex plays nicely with other popular libraries that rely heavily on typing. [FastAPI](https://fastapi.tiangolo.com/tutorial/dependencies/) and [Litestar](https://docs.litestar.dev/2/usage/dependency-injection.html) are two popular ASGI web frameworks that offer powerful dependency injection systems which rely on type hints (via [Pydantic](https://docs.pydantic.dev/latest/)). Cachex can be inserted anywhere in a dedendency chain and it will "just work". This offers tremendous flexibility to the developer when designing applications.

## Data Caching
`cachex.cache_value` and `cachex.async_cache_value` are designed for caching data-whether DataFrames, NumPy arrays, HTTP response data, str, int, float, or any other serializable types. They can decorate any sync or async function/method respectively. Cachex uses [pickle](https://docs.python.org/3/library/pickle.html) to serialize Python objects so always be sure you're writing/reading cached data to/from a secure and trusted source.

## Object Caching
`cachex.cache_reference` is an easy way to cache unhashable objects and make them available globally throughout an application (think DB connections, HTTP clients, ML models, etc.). It is a very easy way to implement the singleton design pattern. Both sync and async functions are supported and this allows for lazy initialization of objects as well as dynamic configuration of client-like objects based user input.

## How It Works
When a decorated method is called, Cachex creates a hash from all the inputs and checks the storage backend for the computed hash. If there is hit, the cached value is returned. If there is a miss, the called function executes and the return value is cached.

### Type Encoders
Cachex can natively encode built in types (int, float, str, dict, list, etc.) when creating a hash. However, for custom types, Cachex doesn't know how to produce a stable hash. In those case there are two options.

1. Name the unhashable argument with a leading underscore. Cachex will ignore this object when producing the input argument hash. This option should only be used where it doesn't make sense for an argument to considered part of the hash such as an HTTP or database connection.

```python
from http.client import HTTPSConnection
from cachex import cache_value


@cache_value()
def get_something(_conn: HTTPSConnection, path: str):
    # _conn has a leading underscore so it will be ignored by cachex.
    # Only path will be used to compute the hash
    ...


def main():
    conn = HTTPSConnection("github.com")
    do_something(conn, "/hyprxa")
```

2. Use a type encoder to convert the custom type into a native type that can be encoded by Cachex. This is the preferred method in most cases. A type encoder is a mapping of type to a callable that returns an encodeable object. You can have multiple type enccoders in a single decorated function.

```python
from pydantic import AnyHttpUrl
from pydantic_core import Url


@cache_value(type_encoders={Url: lambda t: t.unicode_string()})
def download_data(url: AnyHttpUrl):
    # The type encoder converts the Url type to string which cachex can convert
    # to a stable hash

    # The type for a type encoder must support `isinstance`. AnyHttpUrl is
    # actually a subscripted generic so it doesn't support `isinstance`. Its
    # type is pydantic_core.Url so thats why we use Url instead of
    # AnyHttpUrl in the decorator
    ...
```

### Storage Factories and Factory Keys
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

