"""
Dataset generator for the Full Loader concept (Chapter 2).

Produces two FULL snapshots of a `devices` reference dataset — the kind of slowly-changing
external reference data the book describes: a few times a week it changes, it has no reliable
"last updated" column, and it never exceeds ~1M rows. Because there is no delta column, the only
safe way to ingest it is a full load (overwrite the whole thing) each run.

Deterministic: same seed -> same data. Run:  python generate.py
"""
import csv
import random
from pathlib import Path

SEED = 42
HERE = Path(__file__).parent

BROWSERS = ["Chrome", "Firefox", "Safari", "Edge", "Opera", "Samsung Internet"]
OSES = ["Windows", "macOS", "Linux", "Android", "iOS"]
TYPES = ["desktop", "mobile", "tablet"]
MANUFACTURERS = ["Apple", "Samsung", "Dell", "HP", "Lenovo", "Google", "Xiaomi", "Asus"]
RESOLUTIONS = ["1920x1080", "1366x768", "2560x1440", "1440x900", "390x844", "412x915", "768x1024"]


def make_snapshot(n_rows: int, seed: int, start_id: int = 1):
    rnd = random.Random(seed)
    rows = []
    for i in range(start_id, start_id + n_rows):
        rows.append({
            "device_id": f"DV{i:05d}",
            "device_type": rnd.choice(TYPES),
            "browser": rnd.choice(BROWSERS),
            "os": rnd.choice(OSES),
            "manufacturer": rnd.choice(MANUFACTURERS),
            "screen_resolution": rnd.choice(RESOLUTIONS),
        })
    return rows


def write_csv(rows, path: Path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def main():
    # Snapshot 1: the reference dataset on day 1 (500 devices)
    v1 = make_snapshot(n_rows=500, seed=SEED, start_id=1)

    # Snapshot 2: a few days later. No "updated_at" exists, so we cannot tell WHICH rows changed
    # — that is exactly why a full load is required. v2 keeps most rows, mutates ~30 of them, and
    # appends 20 brand-new devices (520 total).
    v2 = [dict(r) for r in v1]
    rnd = random.Random(SEED + 1)
    for idx in rnd.sample(range(len(v2)), 30):           # 30 silent in-place changes
        v2[idx]["browser"] = rnd.choice(BROWSERS)
        v2[idx]["os"] = rnd.choice(OSES)
    v2.extend(make_snapshot(n_rows=20, seed=SEED + 2, start_id=501))  # 20 new devices

    write_csv(v1, HERE / "devices_snapshot_1.csv")
    write_csv(v2, HERE / "devices_snapshot_2.csv")
    print(f"Wrote devices_snapshot_1.csv ({len(v1)} rows) and devices_snapshot_2.csv ({len(v2)} rows)")


if __name__ == "__main__":
    main()
