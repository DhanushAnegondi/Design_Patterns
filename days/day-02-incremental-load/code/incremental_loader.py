"""
Incremental Loader pattern (Chapter 2) — delta-column implementation against S3.

When the source has a column that marks "new" rows (here, event_time on immutable visit events),
you don't reload everything like the Full Loader. You remember the last value you ingested (the
watermark) and pull only rows beyond it. That's the Incremental Loader.

The book flags one sharp edge ("BE AWARE OF REAL-TIME ISSUES"): using event time as the delta
column is risky, because a producer that emits LATE data — an event whose event_time is older than
the watermark you already advanced past — will be silently skipped. This module makes that real:
run.py feeds in a late visit and asserts that it is missed.

Target layout on S3:
    bronze/visits/ingested_at=<run_id>/data.csv   one immutable partition per run
    bronze/visits/_WATERMARK                       the max event_time ingested so far

No real AWS: run.py wraps everything in moto. Point at LocalStack/real S3 via .env (see .env.example).
"""
from __future__ import annotations

import csv
import io
import os
import boto3

EPOCH = "1970-01-01T00:00:00"


def get_s3_client():
    """S3 client honoring AWS_ENDPOINT_URL (LocalStack/real); defaults to moto in-process."""
    endpoint = os.environ.get("AWS_ENDPOINT_URL") or None
    region = os.environ.get("AWS_REGION", "us-east-1")
    return boto3.client("s3", endpoint_url=endpoint, region_name=region)


def _rows_to_csv(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["visit_id", "event_time", "user_id", "page"])
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _count_csv_rows(raw: bytes) -> int:
    return max(0, len(list(csv.reader(io.StringIO(raw.decode("utf-8"))))) - 1)


class IncrementalLoader:
    def __init__(self, bucket: str, prefix: str = "bronze/visits"):
        self.s3 = get_s3_client()
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")
        self.watermark_key = f"{self.prefix}/_WATERMARK"

    def get_watermark(self) -> str:
        try:
            obj = self.s3.get_object(Bucket=self.bucket, Key=self.watermark_key)
            return obj["Body"].read().decode("utf-8").strip()
        except self.s3.exceptions.NoSuchKey:
            return EPOCH

    def _set_watermark(self, value: str):
        self.s3.put_object(Bucket=self.bucket, Key=self.watermark_key, Body=value.encode("utf-8"))

    def run(self, source_rows: list[dict], run_id: str) -> dict:
        """Ingest only source rows with event_time strictly greater than the current watermark.

        Returns stats: how many the source held, how many were new, and the watermark move.
        ISO-8601 timestamps compare correctly as strings, so we can filter lexically.
        """
        wm_before = self.get_watermark()
        new_rows = [r for r in source_rows if r["event_time"] > wm_before]

        if new_rows:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=f"{self.prefix}/ingested_at={run_id}/data.csv",
                Body=_rows_to_csv(new_rows),
            )
            wm_after = max(r["event_time"] for r in new_rows)
            # Advance the watermark only forward (never move it backward).
            if wm_after > wm_before:
                self._set_watermark(wm_after)
        else:
            wm_after = wm_before

        return {
            "run_id": run_id,
            "source_rows": len(source_rows),
            "ingested": len(new_rows),
            "skipped": len(source_rows) - len(new_rows),
            "watermark_before": wm_before,
            "watermark_after": wm_after,
        }

    def bronze_total(self) -> int:
        # NOTE: list_objects_v2 caps at 1000 keys per call. Fine here (few partitions); in
        # production paginate (IsTruncated / NextContinuationToken) or results silently truncate.
        listing = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=f"{self.prefix}/ingested_at=")
        total = 0
        for obj in listing.get("Contents", []):
            data = self.s3.get_object(Bucket=self.bucket, Key=obj["Key"])["Body"].read()
            total += _count_csv_rows(data)
        return total

    def list_partitions(self) -> list[str]:
        # Demo scale only — paginate in production (list_objects_v2 caps at 1000 keys per call).
        listing = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=f"{self.prefix}/ingested_at=")
        return sorted({obj["Key"].split("/")[-2] for obj in listing.get("Contents", [])})
