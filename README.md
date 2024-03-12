# Modern Python Caching
`cachex` is a modern caching library for Python 3. It has built in Redis, MongoDB and Memcached support and provides both sync and async APIs for all storage backends.

## Installation
`pip install cachex`

### Redis Dependencies:
`pip install cachex[redis]`

### MongoDB Dependencies:
`pip install cachex[mongo]`

`cachex` is a decorator based, functional API. It is heavily inspired by the caching semantics in [Streamlit](https://docs.streamlit.io/library/advanced-features/caching) and can be used as an alternative in Streamlit applications with minimal code changes.

