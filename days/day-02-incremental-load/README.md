# Day 02 — Incremental Loader (on S3)

> Chapter 2, *Data Ingestion Design Patterns* · pattern: **Incremental Loader** (book pp. 46–50)
> The one new idea: **a watermark turns "load everything" into "load only what's new" — and event time as the watermark can silently drop late data.**

## Problem (from the book)
Most visit events arrive via streaming, but some legacy producers still write visits to a
transactional database. We need to bring those legacy visits into the Bronze layer. The dataset
**grows continuously** and every visit is **immutable**, so each run should ingest only the visits
added since the last execution.

## Solution
Use a **delta column** — here the visit's `event_time` — and remember the highest value ingested so
far (the **watermark**). Each run:
1. read the watermark (starts at epoch),
2. select source rows with `event_time > watermark`,
3. write them as a new immutable partition `bronze/visits/ingested_at=<run>/`,
4. advance the watermark to the new max `event_time`.

The book describes a second flavour (time-partitioned source, where the partition to read is
derived from the run time). We implement the delta-column flavour because it's the one that has to
*remember state*, which is the interesting part.

## The sharp edge (the book's "BE AWARE OF REAL-TIME ISSUES")
Using event time as the delta column is risky: if a producer emits a visit **late** — an event
whose `event_time` is older than a watermark you already passed — the next run's `event_time >
watermark` filter skips it forever. The demo feeds in exactly such a straggler and asserts it is
missed. (The fix is a later pattern: a lookback window / Late Data Integrator, Chapter 3.)

## Consequences
- **Much less data moved.** The demo shows incremental reading ~50% of what a full reload would.
- **State to manage.** You must store and protect the watermark; lose it and you re-ingest or skip.
- **Late / out-of-order data is a real hazard** when the delta column is event time.

## Run it
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env          # cp on macOS/Linux
python code/run.py
```
Runs in-process via **moto** by default — no AWS, no cost. Expected: four sections ending in
`PASS`, with run 2 ingesting only 200 of 500 rows and run 4 ingesting 0 (the late visit missed).

## Files
- `code/incremental_loader.py` — watermark read/advance + partitioned writes.
- `code/run.py` — runnable demo with assertions (including the late-data miss).
- `index.html` — interactive explainer.
- `context.md` — what to be able to explain after today.
- dataset: `../../datasets/incremental-load/`.

## See also
- Book corpus: `../../../Data Engineering Design Patterns/ch02_data_ingestion_design_patterns.md` ("## Incremental Load").
- Author reference: https://github.com/bartosz25/data-engineering-design-patterns-book/tree/master/chapter-02/02-incremental-load
- Yesterday: [Day 01 — Full Loader](../day-01-full-load/README.md). Today is the answer to its volume problem.
