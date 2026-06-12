"""
Incremental Loader demo — runnable on any machine, no real AWS.

What it proves:
  1. The first run ingests everything (watermark starts at epoch).
  2. As the source grows, each run ingests ONLY the new rows and advances the watermark.
  3. Incremental ingestion moves far less data than a full reload would.
  4. The late-data gotcha is real: an event whose event_time is behind the watermark is SKIPPED.

Run:  python run.py
"""
import csv
import io
import os
import sys
from pathlib import Path

USE_MOTO = os.environ.get("USE_MOTO", "1") == "1"
BUCKET = os.environ.get("S3_BUCKET", "bronze-layer")
REGION = os.environ.get("AWS_REGION", "us-east-1")

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_REGION", REGION)

CODE_DIR = Path(__file__).parent
# DATASET_DIR can be overridden (the Docker container mounts the dataset at /data).
DATASET_DIR = Path(
    os.environ.get("DATASET_DIR") or (CODE_DIR / ".." / ".." / ".." / "datasets" / "incremental-load")
).resolve()

sys.path.insert(0, str(CODE_DIR))
from incremental_loader import IncrementalLoader, get_s3_client  # noqa: E402


def line(title):
    print("\n" + "=" * 70 + f"\n{title}\n" + "=" * 70)


def read_rows(name: str) -> list[dict]:
    path = DATASET_DIR / name
    if not path.exists():
        import subprocess
        subprocess.run([sys.executable, str(DATASET_DIR / "generate.py")], check=True)
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def wait_for_s3(s3, retries=40, delay=1.5):
    """When pointed at LocalStack/real S3, wait until the endpoint answers before we start."""
    import time
    for _ in range(retries):
        try:
            s3.list_buckets()
            return
        except Exception:
            time.sleep(delay)
    raise RuntimeError("S3 endpoint did not become ready in time")


def demo():
    s3 = get_s3_client()
    if os.environ.get("AWS_ENDPOINT_URL"):
        print(f"  (waiting for S3 endpoint {os.environ['AWS_ENDPOINT_URL']} ...)")
        wait_for_s3(s3)
    s3.create_bucket(Bucket=BUCKET)

    batch1 = read_rows("visits_batch_1.csv")   # 300, hour 09
    batch2 = read_rows("visits_batch_2.csv")   # 200, hour 10
    late = read_rows("visits_late.csv")         # 1, event_time back in hour 09

    loader = IncrementalLoader(BUCKET)
    failures = []

    # The "source" is the legacy transactional DB. It grows between runs.
    source: list[dict] = []

    # --- Run 1: first ingestion ----------------------------------------------------------
    line("1. First run — watermark starts at epoch, so everything new is ingested")
    source += batch1
    r1 = loader.run(source, run_id="2026-06-12T10:00")
    print(f"  source={r1['source_rows']}  ingested={r1['ingested']}  "
          f"watermark {r1['watermark_before']} -> {r1['watermark_after']}")
    if r1["ingested"] != 300:
        failures.append(f"run1 expected 300 ingested, got {r1['ingested']}")

    # --- Run 2: source grew, ingest only the delta ---------------------------------------
    line("2. Source grew by 200 — incremental run ingests ONLY the new rows")
    source += batch2
    r2 = loader.run(source, run_id="2026-06-12T11:00")
    print(f"  source={r2['source_rows']}  ingested={r2['ingested']}  skipped(old)={r2['skipped']}  "
          f"watermark {r2['watermark_before']} -> {r2['watermark_after']}")
    if r2["ingested"] != 200:
        failures.append(f"run2 expected 200 ingested, got {r2['ingested']}")
    if r2["skipped"] != 300:
        failures.append(f"run2 expected 300 old rows skipped, got {r2['skipped']}")

    # --- Volume comparison ----------------------------------------------------------------
    line("3. Volume moved: incremental vs full reload")
    # A full loader re-reads the WHOLE source on every run, so its cost is the source size at run 1
    # plus the (larger) source size at run 2 — not the final size doubled.
    full_reload_reads = r1["source_rows"] + r2["source_rows"]   # 300 + 500 = 800
    incremental_reads = r1["ingested"] + r2["ingested"]          # 300 + 200 = 500
    print(f"  full reload would have read {full_reload_reads} rows across the 2 runs")
    print(f"  incremental read only {incremental_reads} rows  "
          f"({100 - round(incremental_reads / full_reload_reads * 100)}% less)")
    if loader.bronze_total() != 500:
        failures.append(f"expected 500 rows in bronze, got {loader.bronze_total()}")

    # --- Run 3: the late-data gotcha ------------------------------------------------------
    line("4. Late data — an event behind the watermark is SILENTLY SKIPPED")
    print(f"  watermark is now {loader.get_watermark()}")
    print(f"  a straggler arrives with event_time {late[0]['event_time']} (earlier than watermark)")
    source += late
    r3 = loader.run(source, run_id="2026-06-12T12:00")
    print(f"  source={r3['source_rows']}  ingested={r3['ingested']}  <-- the late visit was missed")
    if r3["ingested"] != 0:
        failures.append(f"run3 expected the late row to be skipped (0 ingested), got {r3['ingested']}")
    if loader.bronze_total() != 500:
        failures.append(f"late row should NOT be in bronze; expected 500, got {loader.bronze_total()}")

    # --- result ---------------------------------------------------------------------------
    line("RESULT")
    print(f"  bronze partitions: {loader.list_partitions()}")
    if failures:
        for f in failures:
            print(f"  FAIL: {f}")
        return 1
    print("  PASS: incremental loads moved only new rows, the watermark advanced correctly,")
    print("        and the late event was provably missed. Incremental Loader understood,")
    print("        including its sharpest edge.")
    return 0


def main():
    if USE_MOTO:
        from moto import mock_aws
        with mock_aws():
            return demo()
    return demo()


if __name__ == "__main__":
    raise SystemExit(main())
