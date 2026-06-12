# Context — Day 01, Full Loader

## Where this sits
- Book: Chapter 2, Data Ingestion Design Patterns → "Full Load" category → **Full Loader** pattern.
- Pages: ~41–46 in the corpus (`ch02_data_ingestion_design_patterns.md`, "## Full Load").
- Author ref: `chapter-02/01-full-load` (Spark/Airflow/Postgres). Ours is the S3 object-store take.

## The ONE concept this teaches
**Atomic publication of a full reload.** A full load is trivial to *compute* and easy to get wrong
to *publish*. The skill is making the switch from old data to new data atomic — on S3 that means
write-to-new-version then flip a single pointer object, never delete-then-write in place.

## After today I can explain…
1. **When** to choose a full load: small, slowly-changing data with **no reliable delta column**.
2. **Why** drop-then-insert is dangerous: a consumer reading mid-write sees partial/zero rows
   (the demo proves a real 0-row window).
3. **How** to fix it on an object store: immutable `versions/<v>/` + atomic `_CURRENT` pointer swap
   = the object-store version of the book's "swap a view over two technical tables."
4. **What** it costs: you reprocess the entire dataset every run (the volume consequence), and you
   keep old versions for rollback/time-travel.

## How our version differs from the author's (intentionally)
- Author: Spark job + Airflow DAG + PostgreSQL tables.
- Ours: pure-Python boto3 against S3, mocked locally with moto so it runs on any device with zero
  setup. The *pattern* (full reload + atomic swap + keep previous version) is identical; only the
  technology is swapped to match the AWS/S3 stack the learner actually uses.

## Known gaps / deferred
- We don't implement the auto-scaling mitigation for the volume problem (infra concern, not code).
- Real S3 already versions objects natively; we model versioning explicitly to make the mechanism
  visible. On real S3 you might lean on bucket versioning + a manifest instead.
- Concurrency window is shown single-threaded for clarity; a real race needs two clients, but the
  mechanism (empty live prefix between delete and write) is the same. **Why concurrency is
  dangerous here:** two full loads running at once could flip `_CURRENT` to a version whose
  `data.csv` is still being written by the other process, publishing a half-written snapshot. The
  author's Airflow DAG prevents this with `max_active_runs=1`; a production S3 version would
  serialize loads (a lock, a single-writer scheduler, or conditional puts).
- `list_objects_v2` is not paginated in the code (it caps at 1000 keys/call). Flagged inline as a
  demo-scale simplification; production needs a paginator.

## Next
Day 02 — **Incremental Loader**: when a delta column *does* exist, stop reloading everything and
ingest only what changed since a watermark.
