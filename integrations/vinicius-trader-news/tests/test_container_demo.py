"""Static offline policy checks for the optional Docker demonstration.

These checks don't replace an actual Docker build or security review.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ContainerDemoTests(unittest.TestCase):
    def test_dockerfile_is_nonroot_one_shot_demo(self):
        content = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("USER 65532:65532", content)
        self.assertIn('ENTRYPOINT ["python", "-B", "-m", "news_engine"]', content)
        self.assertIn('CMD ["demo", "--data-dir", "/tmp/news-data"]', content)
        self.assertNotIn("EXPOSE ", content)
        self.assertNotIn("COPY . ", content)
        self.assertNotIn("pip install", content.lower())

    def test_compose_disables_network_and_persistent_service(self):
        content = (ROOT / "compose.offline.yml").read_text(encoding="utf-8")
        for value in ('network_mode: "none"', "read_only: true",
                      "no-new-privileges:true", "cap_drop:", "restart: \"no\"",
                      'command: ["demo", "--data-dir", "/tmp/news-data"]'):
            self.assertIn(value, content)
        self.assertNotIn("\n    ports:", content)
        self.assertNotIn("\n    volumes:", content)

    def test_build_context_excludes_private_artifacts(self):
        ignored = set((ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines())
        for name in (".git", ".env", "config.json", "data", "logs", "reports",
                     "*.db", "*.key", "*.pem", "dist"):
            self.assertIn(name, ignored)


if __name__ == "__main__":
    unittest.main()
