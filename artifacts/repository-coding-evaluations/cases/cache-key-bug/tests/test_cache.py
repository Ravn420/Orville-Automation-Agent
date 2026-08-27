import unittest

from case_app.cache import get, put


class CacheTests(unittest.TestCase):
    def test_same_namespace_round_trip(self) -> None:
        cache: dict[str, str] = {}
        put(cache, "alpha", "item", "value")
        self.assertEqual(get(cache, "alpha", "item"), "value")

    def test_namespaces_do_not_collide(self) -> None:
        cache: dict[str, str] = {}
        put(cache, "alpha", "item", "alpha-value")
        put(cache, "beta", "item", "beta-value")
        self.assertEqual(get(cache, "alpha", "item"), "alpha-value")
        self.assertEqual(get(cache, "beta", "item"), "beta-value")


if __name__ == "__main__":
    unittest.main()
