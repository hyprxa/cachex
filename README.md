# Modern Python Caching
Cachex is a modern caching library for Python 3 built from the ground up to support type hints. It has built in Redis, MongoDB and Memcached support and provides both sync and async APIs for all storage backends.

## Installation
`pip install cachex`

### Redis Dependencies:
`pip install cachex[redis]`

### MongoDB Dependencies:
`pip install cachex[mongo]`

### Memcached Dependencies:
No additional dependencies are required for memcached support. Unlike Redis and MongoDB, there is not one client library that is well supported and supports both sync and async API's. For that reason, the Memcached storage backend is implemented as an interface based API. You bring your own client, and as long as that client adheres to the `MemcachedClient` or `AsyncMemcachedClient` interfaces it will work with Cachex.

## Basic Usage
Cachex is a decorator based, functional API. It is heavily inspired by the caching semantics in [Streamlit](https://docs.streamlit.io/library/advanced-features/caching). This example is derived from the Streamlit docs but adapted for Cachex.

```python
import pandas as pd
import streamlit as st
from cachex import cache_value


@cache_value() # The parentheses are required even with no arguments
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    return df

url = "https://github.com/plotly/datasets/raw/master/uber-rides-data1.csv"
df = load_data(url)
st.dataframe(df)
st.button("Rerun")
```

Run the app. You'll notice that the slow download only happens on the first run. Every subsequent rerun should be almost instant!

## Typing Support
The flagship feature of cachex is its typing support. This means it offers great editor support. It also means that cachex plays nicely with other popular libraries that rely heavily on type hints. [FastAPI](https://fastapi.tiangolo.com/tutorial/dependencies/) and [Litestar](https://docs.litestar.dev/2/usage/dependency-injection.html) are two popular ASGI web frameworks that offer powerful dependency injection systems which rely on type hints. Cachex can be inserted anywhere in the dedendency chain and it will "just work". This offers tremendous flexibility to the developer.

## Data Caching
`cachex.cache_value` and `cachex.async_cache_value` are designed for caching data-whether DataFrames, NumPy arrays, HTTP response data, str, int, float, or any other serializable types. They can decorate any sync or async function/method respectively.

## Object Caching
`cachex.cache_reference` is an easy way to cache unhashable objects and make them available globally throughout an application (think DB connections, HTTP clients, ML models, etc.). It is a very easy way to implement the singleton design pattern. Both sync and async functions are supported and this allows for lazy initialization of objects.

