# Service Level Objectives (SLOs)

This document defines the target performance and reliability goals for the ai‑code‑review‑squad service.  Meeting these SLOs ensures a good user experience while balancing engineering effort and resource cost.

## API Latency

| Metric                             | Target   |
|------------------------------------|----------|
| p95 latency for read requests      | < 300ms  |
| p95 latency for write requests     | < 800ms  |

Read requests include `GET /api/reviews` and `GET /api/reviews/{id}`, while write requests include webhooks and review creation.

## Task Success Rate

Celery tasks should succeed at least 99.5% of the time over a rolling 24‑hour window.  Retries count as a failure if all retries are exhausted.

## Availability

The API and worker tier should be available 99.9% of the time per calendar month.  Availability is measured by the proportion of time the `/health` endpoint returns 200 and Celery workers report as up.

## Error Budget Policy

We allocate an error budget equal to 0.1% unavailability or failure.  When the error budget is exhausted, releases that could impact stability are frozen until the budget is replenished.  This encourages balancing velocity with reliability.

## Alerting

Example PromQL alerts are provided in `docs/OBSERVABILITY.md` and the `grafana/` directory.  Alerts fire when metrics exceed their thresholds and page on‑call engineers via your organisation’s incident management tool.