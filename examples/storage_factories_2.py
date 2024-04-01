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