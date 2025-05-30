# Data Retention Policy

ai‑code‑review‑squad treats customer data with care.  This document describes how long we retain different categories of data and the procedures for deletion and export.

## Categories of Data

| Category     | Examples                                      | Retention Period            |
|--------------|-----------------------------------------------|-----------------------------|
| **Application Data** | Tenants, users, projects, repositories, reviews, findings. | Retained indefinitely by default.  Tenants may request deletion of all data at any time. |
| **Audit Logs** | User actions such as login, data access, configuration changes. | Retained for 365 days for compliance and forensic investigations. |
| **Analytics Data** | Parquet/Delta exports of findings and reviews. | Retained for 730 days.  Old partitions may be automatically pruned. |
| **Secrets** | API keys, OAuth tokens, JWTs. | Stored encrypted at rest and rotated according to upstream provider policies.  Not persisted in analytics exports. |

## Deletion Requests

Tenants may request deletion of all data associated with their organisation.  Upon receipt of a validated request:

1. Suspend all active reviews and revoke API keys.
2. Delete records from the `reviews`, `agent_runs`, `findings`, `audit_log`, `api_keys` and related tables, scoped to the tenant.
3. Delete Parquet/Delta partitions under `analytics/data/*/tenant_slug=<slug>`.
4. Confirm deletion and provide a signed certificate of destruction.

## Automated Cleanup

A background job periodically purges data older than the retention period.  The retention windows can be configured via environment variables.  Deleted data is permanently removed and cannot be restored.

## Privacy

See `docs/PRIVACY.md` for details on how we collect, store and process personal data.