"""
Dataset generator for the Incremental Loader concept (Chapter 2).

The book's scenario: legacy "visit" events are still written to a transactional database and must
be ingested into the Bronze layer. The dataset GROWS continuously and each event is immutable, so
we only want to ingest the visits added since the last run. The delta column is the event time.

This generator emits three pieces:
  visits_batch_1.csv  — the first wave of visits (event_time inside hour 09)
  visits_batch_2.csv  — visits that arrive later (event_time inside hour 10)
  visits_late.csv     — ONE visit whose event_time falls back in hour 09 but is delivered last.
                        It demonstrates the late-data gotcha: a watermark on event time skips it.

Deterministic: same seed -> same data. Run:  python generate.py
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 7
HERE = Path(__file__).parent
PAGES = ["/home", "/post/data-engineering", "/post/idempotency", "/about", "/pricing", "/post/s3-full-load"]


def make_visits(n, seed, base_time: datetime, span_minutes: int, start_id: int):
    rnd = random.Random(seed)
    rows = []
    for i in range(start_id, start_id + n):
        ts = base_time + timedelta(seconds=rnd.randint(0, span_minutes * 60))
        rows.append({
            "visit_id": f"V{i:06d}",
            "event_time": ts.strftime("%Y-%m-%dT%H:%M:%S"),
            "user_id": f"U{rnd.randint(1, 120):04d}",
            "page": rnd.choice(PAGES),
        })
    # keep each batch sorted by event_time, like a real append-only log
    rows.sort(key=lambda r: r["event_time"])
    return rows


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["visit_id", "event_time", "user_id", "page"])
        w.writeheader()
        w.writerows(rows)
    return path


def main():
    day = datetime(2026, 6, 12, 9, 0, 0)               # hour 09
    batch1 = make_visits(300, SEED, day, span_minutes=59, start_id=1)
    batch2 = make_visits(200, SEED + 1, day.replace(hour=10), span_minutes=59, start_id=301)
    # a straggler whose event_time is back in hour 09 (before batch2's max) but delivered last
    late = make_visits(1, SEED + 2, day.replace(minute=30), span_minutes=1, start_id=501)

    write_csv(batch1, HERE / "visits_batch_1.csv")
    write_csv(batch2, HERE / "visits_batch_2.csv")
    write_csv(late, HERE / "visits_late.csv")
    print(f"batch1={len(batch1)} rows, batch2={len(batch2)} rows, late={len(late)} row "
          f"(event_time {late[0]['event_time']})")


if __name__ == "__main__":
    main()
