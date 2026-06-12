"""
Full Loader demo — runnable on any machine, no real AWS.

What it proves:
  1. A safe versioned full load publishes a COMPLETE dataset via an atomic pointer swap.
  2. A second full load overwrites the logical dataset while keeping the old version for rollback.
  3. The naive drop-then-insert approach has a real window where consumers see ZERO rows.
  4. Rollback (time travel) is a single pointer write.

Run:  python run.py
"""
import os
import sys
from pathlib import Path

# --- config / portability -------------------------------------------------------------------
# Default path: moto in-process mock (USE_MOTO=1). To run against LocalStack or real S3, set
# USE_MOTO=0 and AWS_ENDPOINT_URL / AWS credentials in .env (see .env.example).
USE_MOTO = os.environ.get("USE_MOTO", "1") == "1"
BUCKET = os.environ.get("S3_BUCKET", "silver-layer")
REGION = os.environ.get("AWS_REGION", "us-east-1")

# moto/boto need *some* credentials present even for the mock.
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_REGION", REGION)

CODE_DIR = Path(__file__).parent
DATASET_DIR = (CODE_DIR / ".." / ".." / ".." / "datasets" / "full-load").resolve()

sys.path.insert(0, str(CODE_DIR))
from full_loader import NaiveFullLoader, SafeVersionedFullLoader, get_s3_client  # noqa: E402


def line(title):
    print("\n" + "=" * 70 + f"\n{title}\n" + "=" * 70)


def load_snapshot_bytes(name: str) -> bytes:
    path = DATASET_DIR / name
    if not path.exists():
        # Generate datasets on the fly if they are not present yet.
        import subprocess
        subprocess.run([sys.executable, str(DATASET_DIR / "generate.py")], check=True)
    return path.read_bytes()


def demo():
    s3 = get_s3_client()
    # Create the target bucket (us-east-1 needs no LocationConstraint).
    s3.create_bucket(Bucket=BUCKET)

    snap1 = load_snapshot_bytes("devices_snapshot_1.csv")  # 500 rows
    snap2 = load_snapshot_bytes("devices_snapshot_2.csv")  # 520 rows

    failures = []

    # --- 1. Safe versioned full load: first run -------------------------------------------
    line("1. Safe versioned Full Loader — first daily snapshot")
    safe = SafeVersionedFullLoader(BUCKET)
    safe.load(snap1, version="2026-06-11")
    count = safe.read_current_count()
    print(f"  _CURRENT -> {safe.current_version()} | consumer reads {count} rows")
    if count != 500:
        failures.append(f"expected 500 rows after first load, got {count}")

    # --- 2. Second full load: overwrite the logical dataset, keep history -----------------
    line("2. Next day — full reload (no delta column exists, so we reload everything)")
    safe.load(snap2, version="2026-06-12")
    count = safe.read_current_count()
    print(f"  _CURRENT -> {safe.current_version()} | consumer reads {count} rows")
    print(f"  versions retained: {safe.list_versions()}")
    if count != 520:
        failures.append(f"expected 520 rows after second load, got {count}")
    if safe.list_versions() != ["2026-06-11", "2026-06-12"]:
        failures.append(f"expected both versions retained, got {safe.list_versions()}")

    # --- 3. The naive drop-insert trap: a real zero-row window ----------------------------
    line("3. Naive drop-then-insert — exposing the consistency window")
    naive = NaiveFullLoader(BUCKET)
    naive.load(snap1)  # establish a live dataset first
    print(f"  before overwrite: consumer reads {naive.read_current_count()} rows")
    naive.begin_overwrite()  # step 1 of drop-insert (delete live)
    mid = naive.read_current_count()  # a consumer reading RIGHT NOW
    print(f"  >>> mid-overwrite: consumer reads {mid} rows  <-- data has vanished")
    naive.finish_overwrite(snap2)  # step 2 (write new)
    print(f"  after overwrite:  consumer reads {naive.read_current_count()} rows")
    if mid != 0:
        failures.append(f"expected naive mid-overwrite window to show 0 rows, got {mid}")

    # --- 4. Rollback / time travel --------------------------------------------------------
    line("4. Rollback — re-point _CURRENT at yesterday's version")
    safe.rollback("2026-06-11")
    count = safe.read_current_count()
    print(f"  _CURRENT -> {safe.current_version()} | consumer reads {count} rows")
    if count != 500:
        failures.append(f"expected 500 rows after rollback, got {count}")

    # --- result ---------------------------------------------------------------------------
    line("RESULT")
    if failures:
        for f in failures:
            print(f"  FAIL: {f}")
        return 1
    print("  PASS: safe load is atomic, history is retained, rollback works, and the naive")
    print("        overwrite was shown to expose a zero-row window. Full Loader understood.")
    return 0


def main():
    if USE_MOTO:
        from moto import mock_aws
        with mock_aws():
            return demo()
    return demo()


if __name__ == "__main__":
    raise SystemExit(main())
