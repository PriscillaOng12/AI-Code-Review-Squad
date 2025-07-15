"""Export analytics tables to Parquet or Delta format."""

import argparse
import os
from datetime import datetime, date
import pandas as pd
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..models.finding import Finding
from ..models.review import Review
from ..models.agent_run import AgentRun
from ..core.config import settings
import json


def export_table(df: pd.DataFrame, table: str, export_date: date) -> list[str]:
    fmt = settings.analytics_format.upper()
    sink = settings.analytics_sink
    base_path = sink if sink else os.path.join(os.getcwd(), "analytics", "data")
    path = os.path.join(base_path, fmt.lower(), table, f"dt={export_date.isoformat()}")
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, f"{table}-{export_date}.parquet")
    df.to_parquet(file_path, index=False)
    return [file_path]


def write_manifest(table: str, export_date: date, files: list[str]) -> None:
    base_path = os.path.join(os.getcwd(), "analytics", "data", "_manifests", table)
    os.makedirs(base_path, exist_ok=True)
    manifest_path = os.path.join(base_path, export_date.isoformat())
    with open(manifest_path, "w") as f:
        json.dump({"date": export_date.isoformat(), "files": files}, f)


def run_export(export_date: date) -> None:
    db: Session = SessionLocal()
    # Findings
    f_query = db.query(Finding)
    f_df = pd.read_sql(f_query.statement, db.bind)
    f_files = export_table(f_df, "findings", export_date)
    write_manifest("findings", export_date, f_files)
    # Reviews
    r_query = db.query(Review)
    r_df = pd.read_sql(r_query.statement, db.bind)
    r_files = export_table(r_df, "reviews", export_date)
    write_manifest("reviews", export_date, r_files)
    # Agent runs
    a_query = db.query(AgentRun)
    a_df = pd.read_sql(a_query.statement, db.bind)
    a_files = export_table(a_df, "agent_runs", export_date)
    write_manifest("agent_runs", export_date, a_files)
    db.close()
    print(f"Export complete for {export_date}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export analytics data")
    parser.add_argument("--date", type=str, required=True, help="Date to export (YYYY-MM-DD)")
    args = parser.parse_args()
    export_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    run_export(export_date)