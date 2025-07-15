"""PySpark notebook for computing KPIs and trends.

This script can be executed as a standalone program using `spark-submit` or within a notebook environment.  It reads exported analytics data (Parquet or Delta) from `analytics/data/{format}` and computes several KPIs, writing results to `analytics/outputs`.
"""

from pyspark.sql import SparkSession, functions as F
import os
from datetime import datetime, timedelta


def load_table(spark: SparkSession, table: str, fmt: str) -> 'pyspark.sql.DataFrame':
    path = os.path.join("analytics", "data", fmt.lower(), table)
    return spark.read.parquet(path)


def compute_kpis(spark: SparkSession, fmt: str):
    findings = load_table(spark, "findings", fmt)
    reviews = load_table(spark, "reviews", fmt)
    # TTFC: time from review created to first critical or high
    critical = findings.filter(findings.severity.isin("critical", "high"))
    first_crit = critical.groupBy("review_id").agg(F.min("created_at").alias("first_crit"))
    merged = reviews.join(first_crit, reviews.id == first_crit.review_id, how="left").select(
        reviews.id, reviews.created_at.alias("review_created"), "first_crit"
    )
    ttfc = merged.withColumn(
        "minutes",
        F.when(
            F.col("first_crit").isNotNull(),
            (F.unix_timestamp("first_crit") - F.unix_timestamp("review_created")) / 60.0,
        ),
    )
    ttfc_stats = ttfc.agg(
        F.expr("percentile(minutes, 0.5)").alias("p50"),
        F.expr("percentile(minutes, 0.9)").alias("p90"),
    ).collect()[0]
    # Critical surfacing rate
    crit_reviews = critical.select("review_id").distinct().count()
    total_reviews = reviews.count()
    csr = crit_reviews / total_reviews if total_reviews else 0
    # False positive proxy (repeat findings within 24h).  Since we have no dismissals, simulate by duplicate rule_id/file_path/line.
    duplicates = findings.groupBy("review_id", "file_path", "start_line", "rule_id").count().filter("count > 1").count()
    fp_rate = duplicates / findings.count() if findings.count() else 0
    # Compile KPI dataframe
    kpi_df = spark.createDataFrame([
        (datetime.utcnow().date().isoformat(), float(ttfc_stats.p50 or 0), float(ttfc_stats.p90 or 0), float(csr), float(fp_rate))
    ], schema=["date", "ttfc_p50_minutes", "ttfc_p90_minutes", "critical_surfacing_rate", "false_positive_rate"])
    out_dir = os.path.join("analytics", "outputs", "kpis", "weekly")
    os.makedirs(out_dir, exist_ok=True)
    kpi_df.toPandas().to_parquet(os.path.join(out_dir, f"kpis-{datetime.utcnow().date().isoformat()}.parquet"), index=False)
    print("KPIs computed and saved.")


def weekly_trends(spark: SparkSession, fmt: str):
    findings = load_table(spark, "findings", fmt)
    findings = findings.withColumn("week", F.date_trunc("week", F.col("created_at")))
    weekly = findings.groupBy("week", "severity", "agent_run_id").count()
    out_dir = os.path.join("analytics", "outputs", "figures")
    os.makedirs(out_dir, exist_ok=True)
    # Example: write aggregated data as CSV for plotting externally
    weekly.toPandas().to_csv(os.path.join(out_dir, "weekly_trends.csv"), index=False)
    print("Weekly trend data saved.")


def main():
    spark = SparkSession.builder.appName("OrgRiskTrends").master("local[*]").getOrCreate()
    fmt = os.environ.get("ANALYTICS_FORMAT", "PARQUET").upper()
    compute_kpis(spark, fmt)
    weekly_trends(spark, fmt)
    spark.stop()


if __name__ == "__main__":
    main()