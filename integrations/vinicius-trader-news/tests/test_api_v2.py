import unittest

from news_engine import api


class ApiSafetyTests(unittest.TestCase):
    def test_reject_remote_bind(self):
        for host in ("0.0.0.0", "192.168.1.5", "example.org", "::"):
            with self.subTest(host=host), self.assertRaises(ValueError):
                api.make_server(":memory:", host, 0)

    def test_container_wildcard_bind_requires_explicit_opt_in(self):
        with self.assertRaises(ValueError):
            api.make_server(":memory:", "0.0.0.0", 0)

        server = api.make_server(":memory:", "0.0.0.0", 0, allow_container_bind=True)
        try:
            self.assertEqual(server.server_address[0], "0.0.0.0")
        finally:
            server.server_close()


if __name__ == "__main__":
    unittest.main()
