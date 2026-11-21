import unittest

from news_engine import api


class ApiSafetyTests(unittest.TestCase):
    def test_reject_remote_bind(self):
        for host in ("0.0.0.0", "192.168.1.5", "example.org", "::"):
            with self.subTest(host=host), self.assertRaises(ValueError):
                api.make_server(":memory:", host, 0)


if __name__ == "__main__":
    unittest.main()
