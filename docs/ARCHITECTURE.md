# Architecture

This document provides a high‑level overview of the ai‑code‑review‑squad architecture.  The system is designed as a cloud‑native, multi‑tenant SaaS with strong separation of concerns and clear boundaries between the frontend, backend, worker tier and infrastructure.

## Components

| Component      | Responsibility                                                                                                      |
|---------------|----------------------------------------------------------------------------------------------------------------------|
| **Frontend**  | A React application built with Vite and TypeScript.  It authenticates users via GitHub OIDC, displays reviews and findings, allows filtering and exporting, and enforces RBAC on the client side. |
| **API**       | A FastAPI server exposing a versioned REST API.  It handles authentication, authorisation, webhook ingestion, review orchestration, data access and export. |
| **Workers**   | Celery workers consuming tasks from Redis.  They perform computationally expensive work such as orchestrating agents, fetching diffs and executing AI models.  Each agent has its own queue, enabling granular scaling.  A dead‑letter queue stores failed tasks. |
| **Database**  | A PostgreSQL 15 instance storing tenants, users, projects, repositories, reviews, agent runs, findings, API keys and audit logs.  Schemas use foreign keys, indexes and partial indexes for performance. |
| **Cache/Queue** | Redis is used both as a Celery message broker and as a cache for short‑lived tokens and rate limits. |
| **GitHub App** | A registered GitHub App installed on repositories.  It emits webhooks to our `/api/webhooks/github` endpoint and uses JWT/installation tokens for API calls. |
| **Analytics** | A batch export job writes daily snapshots of reviews and findings to Parquet or Delta files.  A PySpark notebook and Great Expectations suites enable KPI computation and data validation. |

## Data Flow

1. **Webhook ingestion.**  When a pull request is opened or updated, GitHub sends a webhook to the `/api/webhooks/github` endpoint.  The backend validates the signature, looks up the associated tenant and repository, and creates a `Review` record.  An outbox entry is created to delegate work to the worker tier.
2. **Orchestration.**  Celery workers consume review tasks and fetch diffs via GitHub’s REST API.  For each enabled agent, a task is queued in the corresponding worker queue.  Agents analyse the diff using either deterministic mock rules (local development) or external LLM providers.  Findings are stored in the database.
3. **Reporting.**  Once all agents finish, the backend aggregates results, updates the review status, posts a check on the pull request summarising findings and optionally uploads a SARIF file to the Security tab.  Users can browse findings via the frontend, export them to PR comments, or download a SARIF bundle.
4. **Analytics.**  A daily batch job queries the database for reviews and findings from the previous day and writes Parquet/Delta snapshots into `analytics/data/...`.  KPIs are computed via Spark and surfaced in dashboards.

## Deployment

The repository ships with a Helm chart under `k8s/helm/ai-code-review-squad` for Kubernetes deployments.  The default values configure the backend, frontend, PostgreSQL and Redis with resource requests, liveness and readiness probes and autoscaling (via HPA or KEDA).  For local development, `docker-compose.yml` orchestrates the same services with a deterministic mock LLM.

For a detailed operational guide, see `docs/DEPLOYMENT.md` and the provided Terraform module in `infra/terraform` for single‑region EKS/GKE deployments.