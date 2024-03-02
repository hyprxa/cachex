`cachex` is a modern caching library for Python 3. It has built in Redis and MongoDB support and provides both sync and async APIs for all storage backends. Memcached is not currently supported but may be added in the future.

## Installation

### Install using pip:
`pip install cachex`

### For Redis support:
`pip install cachex[redis]`

### For MongoDB support:
`pip install cachex[mongo]`

## Basic Example
```python
import time
import timeit

from cachex import cache_value


@cache_value()
def simulate_long_op(n: int) -> None:
    time.sleep(n)

s = timeit.default_timer()
simulate_long_op(1)
simulate_long_op(1) # This wont sleep, the cached result is used
simulate_long_op(2) # This will run becuase the input is different
e = timeit.default_timer()

# If the second statement executed, e-s would be over 4 seconds
assert e-s < 4
print(f"Excuted in {e-s} seconds")
```

`cachex` is a decorator based, functional API that suppoprts two different caching patterns: by value and by reference. It is heavily inspired by the semantics in [Streamlit](https://docs.streamlit.io/library/advanced-features/caching) and can be used as an alternative in Streamlit applications with minimal code changes.

## Cache By Value
Cache by value stores the results of computations that return serializable data. Think database query results, API responses, NumPy array transformations, dataframe aggregations, etc. Every call to the cached function returns a copy of the data preventing unexepected results from mutation. Cached data can be stored in any storage backend that implements the methods for the cachex.storage.Storage or cachex.storage.AsyncStorage abstract classes.

## Cache By Reference
Cache by reference is intended for object storage in memory. It enables a functional interface to implement the singleton pattern, where only one instance of an object exists in the application state. This is useful for shared global objects like HTTP clients.