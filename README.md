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
Cachex is a decorator based, functional API. It's typing support and flexible storage backend options make it a great choice as a caching layer in popular modern web framworks like [FastAPI](https://fastapi.tiangolo.com/)

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

Save the script, call it `main.py`. Run the app with `uvicorn main:app` and head to the docs (`/docs`).

![The swagger docs show the correct API arguments and types through the dependency chain](/docs/img/simple_app_docs.png)

Then hit the `/datasets/uber1` endpoint. Depending on your internet connection, this may take 2-30 seconds to run. After it runs once, hit a again, it should load almost instantly! You can then repeat this with the `/datasets/uber2` and `datasets/uber3` endpoints.

## Typing Support
The flagship feature of cachex is its typing support. This means it offers great editor support. It also means that cachex plays nicely with other popular libraries that rely heavily on type hints. [FastAPI](https://fastapi.tiangolo.com/tutorial/dependencies/) and [Litestar](https://docs.litestar.dev/2/usage/dependency-injection.html) are two popular ASGI web frameworks that offer powerful dependency injection systems which rely on type hints. Cachex can be inserted anywhere in the dedendency chain and it will "just work". This offers tremendous flexibility to the developer.

## Data Caching
`cachex.cache_value` and `cachex.async_cache_value` are designed for caching data-whether DataFrames, NumPy arrays, HTTP response data, str, int, float, or any other serializable types. They can decorate any sync or async function/method respectively.

## Object Caching
`cachex.cache_reference` is an easy way to cache unhashable objects and make them available globally throughout an application (think DB connections, HTTP clients, ML models, etc.). It is a very easy way to implement the singleton design pattern. Both sync and async functions are supported and this allows for lazy initialization of objects.

