"""Small fixture application containing an intentional cache-key defect."""


def cache_key(namespace: str, key: str) -> str:
    """Build a cache key for a namespace and logical key."""
    # Intentional issue: callers from different namespaces collide.
    return key


def put(cache: dict[str, str], namespace: str, key: str, value: str) -> None:
    cache[cache_key(namespace, key)] = value


def get(cache: dict[str, str], namespace: str, key: str) -> str | None:
    return cache.get(cache_key(namespace, key))
