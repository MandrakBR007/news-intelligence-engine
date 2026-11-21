# Security Policy

## Reporting a vulnerability

Please do not open a public issue containing sensitive details. Contact the
maintainers through a private channel (for example, the repository's private
security advisory feature) and include:

- a short description of the issue;
- steps to reproduce;
- affected version or commit;
- any suggested mitigation.

We will acknowledge the report and coordinate a fix before public disclosure.

## Scope and design

- The project is local-first and read-only by default.
- No credentials, tokens, operational databases, logs or third-party content are
  shipped in the repository.
- Network access occurs only when the collector is run with configured public
  feeds, or when the optional integration is explicitly enabled.
- The local interface binds to `127.0.0.1` by default and rejects write requests.
- Example configuration uses placeholders; never commit real credentials.

## Secrets

- `.env` files are ignored. Only `.env.example` (with empty values) is included.
- Do not include real keys, tokens, passwords, or private endpoints in issues,
  pull requests, tests, examples or documentation.
- If a secret is accidentally committed, revoke it first and then rewrite the
  history before publishing.

## Dependencies

The core uses only the Python standard library. Optional integrations must be
opt-in and documented. Review new dependencies before adding them.
