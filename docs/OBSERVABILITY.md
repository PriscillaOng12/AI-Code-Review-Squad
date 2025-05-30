# Observability

ai‑code‑review‑squad embraces the principle that you can’t improve what you can’t measure.  The platform ships with tracing, metrics and structured logging built in and provides example Service Level Objectives (SLOs), alerting rules and dashboard definitions.

## Tracing

The backend and workers are instrumented with OpenTelemetry.  Every incoming HTTP request, database query and Celery task emits spans with relevant attributes (tenant, project, agent, severity).  These spans are exported via OTLP to a collector defined by `OTEL_EXPORTER_OTLP_ENDPOINT`.

Example instrumentation of a FastAPI endpoint:

```python
from opentelemetry import trace
from fastapi import APIRouter

router = APIRouter()
tracer = trace.get_tracer(__name__)

@router.get("/health")
async def health():
    with tracer.start_as_current_span("health-check"):
        return {"status": "ok"}
```

## Metrics

Prometheus metrics are exposed at `/metrics` on the backend.  Key metrics include:

* `http_request_duration_seconds{method,endpoint}` – histogram of request latencies.
* `celery_task_duration_seconds{task_name,status}` – histogram of Celery task durations.
* `celery_task_total{task_name,status}` – counter of total tasks processed and their outcomes.
* `queue_depth{queue}` – gauge of the number of pending messages in each Celery queue.
* `llm_provider_calls_total{provider,outcome}` – counter for external LLM API calls.

These metrics can be scraped by Prometheus and visualised in Grafana.  See `docs/SLOs.md` for SLO definitions and example PromQL queries.

## Logging

All services emit JSON logs with correlation IDs, timestamps, log levels and structured fields.  By default, logs are printed to stdout, making them easy to collect with tools like Fluent Bit or Loki.  Example log entry:

```json
{
  "ts": "2025-08-10T12:00:00Z",
  "level": "INFO",
  "service": "api",
  "correlation_id": "b1f9...",
  "method": "GET",
  "path": "/api/reviews",
  "status_code": 200,
  "duration_ms": 23
}
```

## Dashboards & Alerts

The repository includes Grafana dashboard definitions in JSON format (`grafana/` directory) and Prometheus alert rules (`alerts/alert_rules.yml`).  Key panels show request and task latency percentiles, error rates, queue depths and LLM provider health.  Alert examples:

```yaml
groups:
  - name: api-latency
    rules:
      - alert: HighApiLatency
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{endpoint!="/metrics"}[5m])) by (le,endpoint)) > 0.8
        for: 10m
        labels:
          severity: page
        annotations:
          summary: "High API latency (p95)"
          description: "The p95 latency of API requests has been above 800ms for 10 minutes."
```

Refer to `docs/SLOs.md` for SLO targets and error budgets.