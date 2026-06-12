# Context — Day 02, Incremental Loader

## Where this sits
- Book: Chapter 2 → "Incremental Load" category → **Incremental Loader** pattern.
- Pages: ~46–50 in the corpus (`ch02_data_ingestion_design_patterns.md`, "## Incremental Load").
- Author ref: `chapter-02/02-incremental-load`. Ours is the S3 object-store take.
- Follows directly from Day 01: it solves the Full Loader's volume problem.

## The ONE concept this teaches
**The watermark.** Incremental loading is "load everything" minus "everything I already loaded",
and the bookkeeping that makes that possible is a single stored high-water value on the delta
column. Get the watermark right and you move minimal data; misuse event time as the delta column
and you silently lose late events.

## After today I can explain…
1. **When** to choose incremental over full: continuously growing, append-only/immutable data that
   has a usable delta column.
2. **How** the watermark works: read it, filter `delta > watermark`, write the new slice, advance it.
3. **Why** it saves so much: only the new rows are read/written each run (demo: ~50% less).
4. **The trap**: event-time watermarks drop late/out-of-order data. I can show a missed event and
   name the fix direction (lookback window / Late Data Integrator, Chapter 3).
5. The book's second flavour: time-partitioned sources resolve the slice from the run time and
   don't need to remember a watermark (pairs with the Readiness Marker pattern).

## How our version differs from the author's (intentionally)
- Author: Spark/Airflow against a relational source.
- Ours: pure-Python boto3 to S3, mocked with moto, watermark stored as a tiny S3 object. Same
  pattern, swapped to the AWS/S3 stack and made to run anywhere with zero setup.

## Known gaps / deferred
- No lookback-window mitigation for late data (that's a Chapter 3 pattern; we only expose the bug).
- Watermark is a plain object; a production version would guard against concurrent runs and partial
  failures (idempotency — Chapter 4).
- We model the transactional source as CSV batches rather than a live DB connection.

## Next
Day 03 — likely **Change Data Capture** (Chapter 2): when you need inserts, updates AND deletes,
not just appends.
