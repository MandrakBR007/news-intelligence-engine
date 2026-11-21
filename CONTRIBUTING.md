# Contributing

**Languages:** English (this guide) · [Português (Brasil)](CONTRIBUTING.pt-BR.md)

Thanks for your interest. This project is intentionally small and local-first.

## Before you start

- Run the test suite: `python -m unittest discover -s tests -v`.
- Do not add real credentials, tokens, private data, or third-party content.
- Examples and tests must use synthetic data only.
- Keep the core dependency-free; optional integrations must be opt-in.

## Pull requests

By submitting a contribution, you agree that your contribution may be distributed under the project MIT License. Only submit material you have the right to license.


1. Fork the project and create a topic branch.
2. Add or update tests for your change.
3. Keep changes focused and documented.
4. Confirm the tests pass and no secrets are present.
5. Open a pull request describing the problem, the change, and how you tested it.

## What makes a good first contribution

- Improve documentation or translate a user-facing explanation.
- Add tests for malformed public RSS, Atom or JSON feeds using synthetic examples.
- Improve error handling or explain metadata provenance without changing existing timestamps.
- Suggest a feature in an Issue before starting substantial changes.

## Style

- Follow the existing structure and naming.
- Keep functions small and readable.
- Prefer the standard library for the core.
- Avoid network calls in tests.

## Security

If you believe you found a security issue, please follow `SECURITY.md` instead of
opening a public issue with sensitive details.
