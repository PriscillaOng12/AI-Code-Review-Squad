# Security Policy

Security is paramount for ai‑code‑review‑squad.  This document outlines our approach to secure development, vulnerability reporting and compliance.

## Supported Versions

We maintain the current `main` branch and the most recent minor release.  Security fixes are backported as necessary.

## Reporting a Vulnerability

If you believe you have found a security vulnerability in this repository, please report it to `security@your_org.com` with as much detail as possible.  Do **not** open a public issue.  We will acknowledge receipt within 48 hours and provide updates as we investigate.

## Secure Development Practices

- All secrets must be provided via environment variables or secret stores.  Never commit secrets or credentials to the repository.
- The `.env.example` file enumerates all configuration variables with reasonable defaults for local development.
- OAuth flows, API key generation and JWT sessions are implemented with strong cryptography (via `python-jose`).
- RBAC is enforced both server‑side and client‑side.  API responses are filtered based on the requesting user’s role.
- Input validation is performed using Pydantic models and JSON schemas.  All outgoing content is HTML encoded to prevent XSS.
- Dependency and container image scanning are run in CI via Trivy/Grype and pip‑audit/npm audit.  See `.github/workflows/security.yml`.
- SAST/DAST tools (Bandit, OWASP ZAP baseline) run automatically in CI.

For more details on our threat model, data retention policies and compliance posture, refer to `docs/SECURITY.md` and `docs/DATA_RETENTION.md`.