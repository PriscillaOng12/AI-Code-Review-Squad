"""Validate exported analytics data using Great Expectations-like checks."""

import os
import sys
import pandas as pd
from datetime import datetime


SCHEMAS = {
    "findings": {
        "columns": [
            "id",
            "review_id",
            "agent_run_id",
            "file_path",
            "start_line",
            "end_line",
            "severity",
            "title",
            "description",
            "suggested_fix",
            "confidence",
            "rule_id",
            "created_at",
        ],
        "severity_values": {"critical", "high", "medium", "low", "info"},
    },
    "reviews": {
        "columns": [
            "id",
            "repo_id",
            "pr_number",
            "status",
            "stats_json",
            "created_at",
            "updated_at",
        ],
    },
    "agent_runs": {
        "columns": [
            "id",
            "review_id",
            "agent_name",
            "status",
            "duration_ms",
            "metrics_json",
            "started_at",
            "finished_at",
        ],
    },
}


def validate_table(table: str, path: str) -> None:
    partitions = [p for p in os.listdir(path) if p.startswith("dt=")]
    assert partitions, f"No partitions found for {table}"
    partitions.sort(reverse=True)
    latest = partitions[0]
    partition_path = os.path.join(path, latest)
    files = [os.path.join(partition_path, f) for f in os.listdir(partition_path) if f.endswith(".parquet")]
    assert files, f"No Parquet files found for {table} partition {latest}"
    df = pd.concat([pd.read_parquet(f) for f in files])
    # Check columns
    expected_cols = SCHEMAS[table]["columns"]
    assert set(expected_cols).issubset(df.columns), f"Missing columns in {table}: {set(expected_cols) - set(df.columns)}"
    # Specific validations
    if table == "findings":
        assert set(df["severity"].unique()).issubset(SCHEMAS[table]["severity_values"]), "Unexpected severities"
        assert df["confidence"].between(0.0, 1.0).all(), "Confidence values out of range"
    print(f"{table} validation passed for {latest}")


def main():
    if len(sys.argv) > 1:
        root = sys.argv[1]
    else:
        root = os.path.join(os.getcwd(), "analytics", "data", "parquet")
    for table in SCHEMAS:
        table_path = os.path.join(root, table)
        validate_table(table, table_path)


if __name__ == '__main__':
    main()