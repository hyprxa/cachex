from __future__ import annotations

import functools
import inspect
import logging
import pickle
import threading
from typing import Any, TypeVar, cast, TYPE_CHECKING

import anyio

from cacheplus.exceptions import (
    CacheError,
    ImproperlyConfiguredException,
    UnserializableReturnValueError,
)
from cacheplus.factories import async_memory_storage_factory, memory_storage_factory
from cacheplus.ref import cache_reference
from cacheplus.storage.base import AsyncStorage, Storage
from cacheplus._core import make_function_key, make_value_key


__all__ = ("cache_value", "async_cache_value")

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Mapping
    from datetime import timedelta
    from typing_extensions import ParamSpec

    P = ParamSpec("P")
    R = TypeVar("R")

_LOGGER = logging.getLogger("cacheplus.value")


def _wrap_factory(storage_factory: Callable[[], Storage]) -> Callable[[str], Storage]:
    """Wraps a storage factory and returns the factory but accepts an
    additional string argument as a unique key for different partials.
    """
    @functools.wraps(storage_factory)
    def wrapper(factory_key: str | None) -> Storage:
        storage = storage_factory()
        _LOGGER.debug("Created new storage instance for key: %s", factory_key)
        return storage
    return wrapper


def _wrap_async_factory(
    storage_factory: Callable[[], AsyncStorage | Awaitable[AsyncStorage]]
) -> Callable[[str], Awaitable[AsyncStorage]]:
    """Wraps a storage factory and returns the factory but accepts an
    additional string argument as a unique key for different partials.
    """
    @functools.wraps(storage_factory)
    async def wrapper(factory_key: str | None) -> Storage:
        if inspect.iscoroutinefunction(storage_factory):
            storage = await storage_factory()
        else:
            storage = storage_factory()
        _LOGGER.debug("Created new storage instance for key: %s", factory_key)
        return storage
    return wrapper
    

class _NullLock:
    def __enter__(self) -> None:
        pass

    def __exit__(self, *_: Any, **__: Any) -> None:
        pass

    async def __aenter__(self) -> None:
        pass

    async def __aexit__(self, *_: Any, **__: Any) -> None:
        pass


class cache_value:
    """Cache the return value of the decorated callable. The return value
    must be pickleable.

    Every caller gets its own copy of the cached value.

    This decorator works with sync functions.
    
    By default, calls can execute concurrently so it is possible for a function called
    concurrently with identical arguments to run more than once. If this behavior is not
    acceptable for your use case, you can force concurrent calls to be executed serially
    by setting ``allow_concurrent`` to ``False``.

    Args:
        storage_factory: A callable that returns a
            :class:`Storage <cacheplus.storage.base.Storage>` instance. The
            callable is wrapped in :func:`cache_reference <cacheplus.ref.cache_reference>`
            creating a singleton
        type_encoders: A mapping of types to callables that transform them
            into ``bytes``
        expires_in: Time in seconds before the data is considered expired
        allow_concurrent: If ``False`` force concurrent calls to be executed serially.
            Defaults to ``True``
        factory_key: Differentiate different storage factories across decorated functions.
            Factories have to be zero argument callables and these are wrapped in a call to
            :function: `cacheplus.cache_reference`. Because of this, partial functions with
            different arguments produce the same hash. The factory key is a way to explicitely
            differentiate the same factory function with different arguments. The factory key
            is not passed to the factory function, the factory function must still be a zero
            argument callable
    """

    def __init__(
        self,
        storage_factory: Callable[[], Storage] = memory_storage_factory(),
        type_encoders: Mapping[type, Callable[[Any], bytes]] | None = None,
        expires_in: int | timedelta | None = None,
        allow_concurrent: bool = True,
        factory_key: str | None = None,
    ) -> None:
        self._factory = cast(
            "Callable[[], Storage]", cache_reference()(_wrap_factory(storage_factory))
        )
        self._type_encoders = type_encoders
        self._expires_in = expires_in
        self._serialize = not allow_concurrent

        self._storage: Storage | None = None

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        if inspect.iscoroutinefunction(func):
            raise TypeError(
                "'cache_value' cannot wrap a coroutine. If this is an asyncronous "
                "function/method, use 'async_cache_value'"
            )
        function_key = make_function_key(func)
        if self._serialize:
            lock = threading.Lock()
        else:
            lock = _NullLock()  # type: ignore[assignment]

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # This ``None`` value check is faster than acquiring the two
            # locks required for ``cache_reference``
            if self._storage is None:
                storage = self._factory()
                self._storage = storage
            else:
                storage = self._storage

            with lock:
                key = make_value_key(
                    function_key, func, self._type_encoders, *args, **kwargs
                )
                try:
                    data = storage.get(key)
                except ImproperlyConfiguredException:
                    raise
                except Exception as e:
                    raise CacheError(
                        f"An error occurred while getting {key} from storage"
                    ) from e

                if data is not None:
                    _LOGGER.debug("Cache hit: %s", func)
                    try:
                        return pickle.loads(data)
                    except pickle.UnpicklingError as e:
                        raise CacheError(f"Failed to unpickle {key}") from e

                _LOGGER.debug("Cache miss: %s", func)
                value = func(*args, **kwargs)

                try:
                    data = pickle.dumps(value)
                except (TypeError, pickle.PicklingError) as e:
                    raise UnserializableReturnValueError(func=func, value=value) from e
                try:
                    storage.set(key, data, expires_in=self._expires_in)
                except Exception as e:
                    raise CacheError(
                        f"An error occurred while saving {key} to storage"
                    ) from e
                return value

        return wrapper


class async_cache_value:
    """Cache the return value of the decorated callable. The return value
    must be pickleable.

    Every caller gets its own copy of the cached value.

    This decorator works with async functions.

    By default, calls can execute concurrently so it is possible for a function called
    concurrently with identical arguments to run more than once. If this behavior is not
    acceptable for your use case, you can force concurrent calls to be executed serially
    by setting ``allow_concurrent`` to ``False``.

    Args:
        storage_factory: A callable that returns a
            :class:`AsyncStorage <cacheplus.storage.base.AsyncStorage>` instance. The
            callable is wrapped in :func:`cache_reference <cacheplus.ref.cache_reference>`
            creating a singleton
        type_encoders: A mapping of types to callables that transform them
            into ``bytes``
        expires_in: Time in seconds before the data is considered expired
        allow_concurrent: If ``False`` force concurrent calls to be executed serially.
            Defaults to ``True``
        factory_key: Differentiate different storage factories across decorated functions.
            Factories have to be zero argument callables and these are wrapped in a call to
            :function: `cacheplus.cache_reference`. Because of this, partial functions with
            different arguments produce the same hash. The factory key is a way to explicitely
            differentiate the same factory function with different arguments. The factory key
            is not passed to the factory function, the factory function must still be a zero
            argument callable
    """

    def __init__(
        self,
        storage_factory: Callable[
            [], AsyncStorage | Awaitable[AsyncStorage]
        ] = async_memory_storage_factory(),
        type_encoders: Mapping[type, Callable[[Any], bytes]] | None = None,
        expires_in: int | timedelta | None = None,
        allow_concurrent: bool = True,
    ) -> None:
        self._factory = cache_reference()(_wrap_async_factory(storage_factory))
        self._type_encoders = type_encoders
        self._expires_in = expires_in
        self._serialize = not allow_concurrent

        self._storage: AsyncStorage | None = None
        self._is_async = inspect.iscoroutinefunction(self._factory)

    def __call__(self, func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError(
                "'async_cache_value' must wrap a coroutine. If this is a syncronous "
                "function/method, use 'cache_value'"
            )
        function_key = make_function_key(func)
        if self._serialize:
            lock = anyio.Lock()
        else:
            lock = _NullLock()  # type: ignore[assignment]

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> R:
            # This ``None`` value check is faster than acquiring the two
            # locks required for ``cache_reference``
            if self._storage is None:
                if self._is_async:
                    storage = await self._factory()  # type: ignore[misc]
                else:
                    storage = self._factory()
                self._storage = cast("AsyncStorage", storage)
            else:
                storage = self._storage

            async with lock:
                key = make_value_key(
                    function_key, func, self._type_encoders, *args, **kwargs
                )
                try:
                    data = await storage.get(key)
                except ImproperlyConfiguredException:
                    raise
                except Exception as e:
                    raise CacheError(
                        f"An error occurred while getting {key} from storage"
                    ) from e

                if data is not None:
                    _LOGGER.debug("Cache hit: %s", func)
                    try:
                        return pickle.loads(data)
                    except pickle.UnpicklingError as e:
                        raise CacheError(f"Failed to unpickle {key}") from e

                _LOGGER.debug("Cache miss: %s", func)
                value = await func(*args, **kwargs)

                try:
                    data = pickle.dumps(value)
                except (TypeError, pickle.PicklingError) as e:
                    raise UnserializableReturnValueError(func=func, value=value) from e
                try:
                    await storage.set(key, data, expires_in=self._expires_in)
                except Exception as e:
                    raise CacheError(
                        f"An error occurred while saving {key} to storage"
                    ) from e
                return value

        return wrapper
