# ai-code-review-squad

**ai‑code‑review‑squad** is a multi‑tenant Software‑as‑a‑Service platform for automated code reviews and security scanning.  It integrates tightly with GitHub, receiving pull request webhooks through a GitHub App, orchestrating multiple AI‑powered agents to review changes, and surfacing actionable feedback via the GitHub Checks API and the Security tab.  The system is designed from the ground up for scalability, reliability and observability, and ships with infrastructure as code, CI/CD pipelines, and a rich analytics module.

## Features

* **GitHub App integration** – implements the App manifest flow, validates webhook signatures, fetches pull request diffs and posts review comments.  Supports SARIF uploads to GitHub’s security tab.
* **Multi‑agent orchestration** – pluggable agents (security, style, logic, performance, architecture) execute concurrently using Celery with per‑queue back pressure and dead‑letter queues.
* **Multi‑tenant SaaS** – tenants manage projects and repositories.  Roles include Owner, Maintainer, Reviewer and Viewer with fine‑grained RBAC enforced both on the backend and the frontend.
* **Full API** – versioned REST API built with FastAPI and documented via OpenAPI.  Includes idempotent webhook endpoints, review/list endpoints, and export endpoints for SARIF and analytics.
* **Observability** – out of the box OpenTelemetry tracing, Prometheus metrics and structured JSON logging.  SLOs and alerting examples are documented in `docs/OBSERVABILITY.md`.
* **Security & compliance** – OAuth login with GitHub OIDC, per‑tenant API keys, CSRF/CORS protections, audit logging, RBAC, dependency scanning, static analysis and runtime hardening.  See `SECURITY.md` for details.
* **Infrastructure** – Kubernetes Helm chart, optional Terraform module for a single‑region baseline, and docker‑compose for local development with a deterministic mock LLM mode.
* **Analytics** – daily exports of review and finding data to Parquet or Delta Lake, validated with Great Expectations and consumable via a PySpark notebook.  Includes example Grafana panels and Spark SQL snippets in `docs/ANALYTICS.md`.

## Quickstart

1. **Clone and configure.**  Copy `.env.example` to `.env` and customise values if necessary.  No secrets are required to start in mock mode.
2. **Bring up the stack.**  Run `make up` to build images, apply database migrations and start the backend, frontend, PostgreSQL and Redis via docker‑compose.  Navigate to http://localhost:5173 to use the demo UI.
3. **Run a demo review.**  Use the demo UI to trigger a “Run Demo Review” against the sample repository.  Findings will appear within a few seconds and can be browsed, filtered and exported.
4. **Run tests.**  The repository includes a complete test suite.  Execute `make test` to run backend unit and integration tests, frontend unit tests and a simple end‑to‑end smoke test.  All tests should pass.
5. **Explore analytics.**  To export analytics data, run `make analytics-export DATE=$(date -u +%F)` and then `make spark-notebook` to run the provided PySpark notebook locally.  Documentation lives in `docs/ANALYTICS.md`.

For detailed architecture diagrams, API reference, runbooks, product rationale and more, browse the `docs/` directory.
