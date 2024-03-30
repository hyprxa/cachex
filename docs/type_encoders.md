# Type Encoders
Cachex can natively encode built in types (int, float, str, dict, list, etc.) when creating a hash. However, for custom types, Cachex doesn't know how to produce a stable hash. In those cases there are two options.

1. Name the unhashable argument with a leading underscore. Cachex will ignore this object when producing the input argument hash. This option should only be used where it doesn't make sense for an argument to be considered part of the hash such as an HTTP or database connection.

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

2. Use a type encoder to convert the custom type into a native type that can be encoded by Cachex. This is the preferred method in most cases. A type encoder is a mapping of type to a callable that returns an encodeable object. You can have multiple type encoders in a single decorated function.

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