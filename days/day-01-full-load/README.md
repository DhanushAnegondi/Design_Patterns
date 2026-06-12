# Day 01 — Full Loader (on S3)

> Chapter 2, *Data Ingestion Design Patterns* · pattern: **Full Loader** (book pp. 41–46)
> The one new idea: **publish a full reload atomically by swapping a pointer, never by overwriting in place.**

## Problem (from the book, mapped to our blog platform)
We're building the Silver layer. A transformation job needs extra information about each **device**
from an external provider. That device dataset:
- changes only a few times a week,
- is small (well under 1M rows),
- and has **no "last updated" column**, so we cannot tell which rows changed.

With no delta column, we cannot do an incremental load. We must re-ingest the **whole** dataset
every run. That is the Full Loader.

## Solution
A Full Loader is conceptually two steps — extract the full source, load it to the target
(EL; add a thin transform and it's ETL). The trap is *how* you publish the new full snapshot.

This day implements two loaders against an S3 object store:

| Loader | What it does | Verdict |
|--------|--------------|---------|
| `NaiveFullLoader` | deletes the live prefix, then writes the new snapshot | ❌ has a window where readers see 0 rows |
| `SafeVersionedFullLoader` | writes the snapshot under an immutable `versions/<v>/` prefix, then flips a single `_CURRENT` pointer object | ✅ readers always see a complete version |

The single `PUT` of `_CURRENT` is the object-store equivalent of the book's mitigation — swapping a
**view** over two technical tables so consumers never see a half-written dataset. Keeping old
versions gives us **rollback / time travel** for free.

## Consequences (what to watch for)
- **Data volume** — you move the entire dataset every run. Fine for slowly-growing reference data;
  costly for large, fast-growing data (that's tomorrow's Incremental Loader).
- **Data consistency** — never drop-then-insert in place. Use an atomic swap (pointer/view) and
  keep the previous version so you can roll back when a bad load happens.

## Run it
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env          # cp on macOS/Linux
python code/run.py
```
By default it runs entirely in-process via the **moto** S3 mock — no AWS account, no cost, no
network. `.env.example` shows how to repoint at LocalStack or real S3 with one variable.

Expected: four numbered sections ending in `PASS`, including the naive loader briefly reading
`0 rows` mid-overwrite and a rollback returning to 500 rows.

## Files
- `code/full_loader.py` — the two loaders + a tiny S3 client factory (moto / LocalStack / real).
- `code/run.py` — the runnable demo with assertions.
- `index.html` — interactive explainer (open in a browser).
- `context.md` — what to be able to explain after today.
- dataset: `../../datasets/full-load/` (two device snapshots + generator).

## See also
- Book corpus: `../../../Data Engineering Design Patterns/ch02_data_ingestion_design_patterns.md`
- Author reference: https://github.com/bartosz25/data-engineering-design-patterns-book/tree/master/chapter-02/01-full-load
  (author uses Spark + Airflow + PostgreSQL; this is our own S3/object-store version of the same pattern).
