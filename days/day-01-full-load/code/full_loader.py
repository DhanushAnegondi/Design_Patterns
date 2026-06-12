"""
Full Loader pattern (Chapter 2) — implemented against an S3 object store.

The book's Full Loader has a simple two-step shape (extract + load) but two real pitfalls:
  1. Data volume  — you reload the WHOLE dataset every run.
  2. Data consistency — if you overwrite in place (drop-then-insert), a consumer that reads while
     you are mid-write sees partial data or nothing at all. The book's mitigation is to swap an
     abstraction (a view over two technical tables) and to keep the previous version for rollback.

This module shows both the WRONG and the RIGHT way on S3:

  NaiveFullLoader        — deletes the live prefix then writes the new snapshot. There is a window
                           where a reader sees an empty/partial dataset. This is the drop-insert trap.

  SafeVersionedFullLoader — writes the new snapshot under an immutable version prefix, then flips a
                           single `_CURRENT` pointer object. A reader always resolves `_CURRENT` to a
                           COMPLETE version. The pointer PUT is the atomic "view swap". Old versions
                           stay, so rollback / time-travel is one pointer write.

No real AWS needed: run.py wraps everything in moto's in-process S3 mock. The same code runs
against LocalStack or real S3 by setting AWS_ENDPOINT_URL / credentials (see .env.example).
"""
from __future__ import annotations

import csv
import io
import os
import boto3


def get_s3_client():
    """Build an S3 client. Honors AWS_ENDPOINT_URL (LocalStack/real); defaults to moto in-process."""
    endpoint = os.environ.get("AWS_ENDPOINT_URL") or None
    region = os.environ.get("AWS_REGION", "us-east-1")
    return boto3.client("s3", endpoint_url=endpoint, region_name=region)


def _count_csv_rows(raw: bytes) -> int:
    reader = csv.reader(io.StringIO(raw.decode("utf-8")))
    rows = list(reader)
    return max(0, len(rows) - 1)  # minus header


class NaiveFullLoader:
    """Overwrite-in-place. Demonstrates the consistency window. Do NOT use in production."""

    def __init__(self, bucket: str, prefix: str = "devices/naive"):
        self.s3 = get_s3_client()
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")
        self.live_key = f"{self.prefix}/current/data.csv"

    def _delete_live(self):
        listing = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=f"{self.prefix}/current/")
        for obj in listing.get("Contents", []):
            self.s3.delete_object(Bucket=self.bucket, Key=obj["Key"])

    def begin_overwrite(self):
        """Step 1 of drop-insert: remove the live data. (Split out to expose the bad window.)"""
        self._delete_live()

    def finish_overwrite(self, csv_bytes: bytes):
        """Step 2 of drop-insert: write the new snapshot."""
        self.s3.put_object(Bucket=self.bucket, Key=self.live_key, Body=csv_bytes)

    def load(self, csv_bytes: bytes):
        self.begin_overwrite()
        self.finish_overwrite(csv_bytes)

    def read_current_count(self) -> int:
        try:
            obj = self.s3.get_object(Bucket=self.bucket, Key=self.live_key)
            return _count_csv_rows(obj["Body"].read())
        except self.s3.exceptions.NoSuchKey:
            return 0


class SafeVersionedFullLoader:
    """Versioned write + atomic pointer swap. The correct Full Loader on an object store."""

    def __init__(self, bucket: str, prefix: str = "devices/safe"):
        self.s3 = get_s3_client()
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")
        self.pointer_key = f"{self.prefix}/_CURRENT"

    def _version_key(self, version: str) -> str:
        return f"{self.prefix}/versions/{version}/data.csv"

    def load(self, csv_bytes: bytes, version: str) -> str:
        """Write the full snapshot under an immutable version, then flip the pointer atomically."""
        # 1. Write the complete new snapshot to an immutable location. Consumers are NOT looking
        #    here yet, so a partial/in-progress write is invisible to them.
        self.s3.put_object(Bucket=self.bucket, Key=self._version_key(version), Body=csv_bytes)
        # 2. Atomically publish it. A single PUT of the pointer is the "view swap" — consumers
        #    either see the old version or the new one, never a half-written dataset.
        self.s3.put_object(Bucket=self.bucket, Key=self.pointer_key, Body=version.encode("utf-8"))
        return version

    def current_version(self) -> str | None:
        try:
            obj = self.s3.get_object(Bucket=self.bucket, Key=self.pointer_key)
            return obj["Body"].read().decode("utf-8").strip()
        except self.s3.exceptions.NoSuchKey:
            return None

    def read_current_count(self) -> int:
        version = self.current_version()
        if version is None:
            return 0
        obj = self.s3.get_object(Bucket=self.bucket, Key=self._version_key(version))
        return _count_csv_rows(obj["Body"].read())

    def list_versions(self) -> list[str]:
        listing = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=f"{self.prefix}/versions/")
        versions = set()
        for obj in listing.get("Contents", []):
            # key shape: <prefix>/versions/<version>/data.csv
            parts = obj["Key"].split("/")
            versions.add(parts[-2])
        return sorted(versions)

    def rollback(self, version: str):
        """Time-travel: re-point _CURRENT at an older, still-present version."""
        if version not in self.list_versions():
            raise ValueError(f"version {version!r} does not exist; cannot roll back")
        self.s3.put_object(Bucket=self.bucket, Key=self.pointer_key, Body=version.encode("utf-8"))
