# Analytics

ai‑code‑review‑squad includes an analytics module that exports review and finding data to Parquet or Delta formats, validates schema contracts with Great Expectations and provides a PySpark notebook for KPI computation.  This document explains how to use the analytics features and the data model.

## Data Export

The backend exposes a task or admin API to export daily snapshots of three tables: `findings`, `reviews` and `agent_runs`.  Exported files are written to `analytics/data/{format}/{table}/dt=YYYY-MM-DD/*.parquet`.  The format is determined by the `ANALYTICS_FORMAT` environment variable (PARQUET or DELTA).  If `ANALYTICS_SINK` is set to an S3 or DBFS URI, files will be written there instead of the local filesystem.

Each export writes a manifest file to `analytics/data/_manifests/{table}/{date}.json` containing the output file paths and a hash of the data.  The `/api/exports/analytics/latest-manifest` endpoint returns the newest manifests across all tables.

## Table Schemas

| Table       | Columns                                                                                                           |
|-------------|-------------------------------------------------------------------------------------------------------------------|
| `findings`  | tenant_slug, project, repo, pr_number, review_id, agent_name, rule_id, file_path, start_line, end_line, severity, title, description, suggested_fix, confidence (double), created_at (timestamp) |
| `reviews`   | tenant_slug, project, repo, pr_number, review_id, status, stats_json (stringified JSON), created_at (timestamp), updated_at (timestamp) |
| `agent_runs`| review_id, agent_run_id, agent_name, status, duration_ms (int), metrics_json (stringified JSON), started_at (timestamp), finished_at (timestamp) |

See the Great Expectations suites in `analytics/gx/` for column type contracts and allowed values.

## Computing KPIs

The provided PySpark notebook `analytics/notebooks/OrgRiskTrends.py` computes several KPIs:

* **Time‑to‑First‑Critical (TTFC):** median minutes between review creation and the first critical or high severity finding.
* **Critical Surfacing Rate:** percentage of reviews with at least one critical finding.
* **False‑Positive Proxy:** share of findings dismissed within 24 hours (simulated via repeat findings in the demo).  A proxy for precision.
* **Triage Completion:** ratio of findings with a suggested fix that are clicked or exported.  In the absence of real click data, this is simulated from `stats_json`.

The notebook produces weekly time series and exports summarised KPIs to `analytics/outputs/kpis/weekly/*.parquet`.  It also saves static figures in `analytics/outputs/figures/` using Matplotlib.

### Example Spark SQL

You can run SQL directly against the Parquet or Delta files using Spark SQL.  Here is an example to compute the number of critical findings per agent in the last 7 days:

```sql
SELECT agent_name,
       COUNT(*) AS critical_count
FROM findings
WHERE severity = 'critical'
  AND created_at >= date_sub(current_date(), 7)
GROUP BY agent_name
ORDER BY critical_count DESC;
```

## Dashboards

The `grafana/` directory contains an example dashboard JSON with panels such as “Critical Findings by Agent (7d)” and “TTFC (p50/p90)”.  Import these panels into Grafana and configure your Prometheus datasource accordingly.

## Running Locally vs. Databricks

To run the PySpark notebook locally:

```bash
make analytics-export DATE=$(date -u +%F)
make spark-notebook
```

The `make spark-notebook` target prints instructions for launching a local Spark session and executing the notebook.  If you set `ANALYTICS_SINK=dbfs:/mnt/analytics`, the same code will run unchanged on Databricks, provided the cluster has access to the DBFS mount.

For Databricks SQL, mount your S3 bucket or DBFS path and run the provided SQL snippets using the built‑in editor.