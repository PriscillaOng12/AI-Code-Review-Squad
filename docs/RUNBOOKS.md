# Runbooks

This document outlines procedures for handling common operational scenarios and incidents.  Operators should follow these runbooks during production incidents to restore service quickly and minimise impact.

## Webhook Backlog

Symptoms:

* The queue depth of the `webhook` Celery queue grows continuously.
* Reviews take a long time to start processing.

Mitigation:

1. Confirm that Celery workers are healthy: `kubectl get pods -l app=ai-code-review-workers` and inspect logs for errors.
2. Scale the worker deployment horizontally via `kubectl scale deployment ai-code-review-workers --replicas=<n>` or adjust HPA/KEDA thresholds in Helm values.
3. Check for dead‑lettered messages in `redis:1` (DLQ) using the provided management script `scripts/replay_dlq.py`.  Requeue messages if they represent transient errors.
4. Investigate upstream network issues between the backend and GitHub API; verify that the `GITHUB_APP_PRIVATE_KEY` is valid.
5. Once the backlog drains, restore the original worker count.

## Worker Crash Loop

Symptoms:

* Worker pods repeatedly restart.
* Kubernetes events show OOMKilled or CrashLoopBackOff.

Mitigation:

1. Check resource usage via `kubectl top pod`.  If memory pressure is high, increase the worker container memory limit in `values.yaml`.
2. Inspect the worker logs to identify the failing task.  Common causes include unhandled exceptions in agents, misconfiguration of LLM providers or database connectivity issues.
3. Temporarily disable problematic agents using feature flags in the admin API or set `MOCK_LLM=true` to bypass external providers.
4. Apply a hotfix or rollback the offending change.  Redeploy once a fix is available.

## Database Bloat

Symptoms:

* Queries slow down; CPU utilisation on the database is high.
* Disk usage grows unexpectedly due to large numbers of findings.

Mitigation:

1. Verify that dead rows are being vacuumed.  Run `VACUUM ANALYZE` on the `findings` and `reviews` tables.  Consider increasing autovacuum frequency.
2. Archive old data according to the retention policy.  Use the analytics export to persist historical data and delete rows older than the retention period.
3. Add or adjust partial indexes on frequently queried columns, such as `(review_id, severity)` and `(tenant_id, created_at)`.
4. Monitor disk utilisation and provision additional storage if necessary.  Documented retention and deletion procedures are in `docs/DATA_RETENTION.md`.

## Rate Limit Spikes

Symptoms:

* API returns 429 Too Many Requests.
* Users report being unable to trigger new reviews.

Mitigation:

1. Review the rate limit configuration in `app/core/rate_limit.py`.  Increase the per‑tenant or per‑key quotas if the spikes are expected and within capacity.
2. Investigate abnormal traffic patterns for abuse.  Check audit logs in `audit_log` table for suspicious behaviour.
3. Communicate temporary rate limiting to affected tenants via status page or email.
4. Implement backpressure in the UI to queue actions client‑side when limits are reached.

These runbooks are a starting point; adapt them to your organisation’s processes and infrastructure.