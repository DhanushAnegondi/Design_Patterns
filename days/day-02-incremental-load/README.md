# Day 02 — Incremental Loader (on S3, in Docker)

> **Chapter 2 — Data Ingestion · pattern: Incremental Loader.**
> The one idea to take away: **remember the newest thing you've already loaded (the "watermark") and
> next time load only what's newer — but if you use event time for that, late arrivals slip through.**

---

## 1. Explain it like I'm five

Yesterday (Full Loader) we copied the *whole* list every time. That's wasteful when the list keeps
growing. Imagine a notebook where new lines are only ever *added* at the bottom, never changed.

Instead of recopying the whole notebook each day, you put a **bookmark** on the last line you
copied. Next time you only copy the lines *below the bookmark*, then move the bookmark down. Way
less work.

The catch: if someone sneaks a new line **above** your bookmark (it was written late), you'll never
copy it — your bookmark already moved past it. That's the one trap of this pattern.

The bookmark has a real name: the **watermark**.

---

## 2. The real problem (our blog-analytics project)

Most visit events stream in real time, but some old systems still write visits into a regular
database. We need to copy those into the **Bronze layer** (raw landing zone). The data:

- grows continuously,
- is **append-only** (every visit is immutable — it never changes once written).

So each run should copy only the visits added **since last time**, not the whole table.

---

## 3. Words you need first (skip if you know them)

- **Bronze layer** — the raw landing zone, the first place data lands before cleaning.
- **Delta column** — a column that tells you "how new" a row is. Here it's `event_time`.
- **Watermark** — the highest `event_time` we've already ingested. We store it as a tiny file in S3
  (`bronze/visits/_WATERMARK`) and only load rows whose `event_time` is greater than it.
- **Partition** — each run writes its new rows to its own folder, e.g.
  `bronze/visits/ingested_at=2026-06-12T11:00/`. Keeps runs separate and easy to reason about.
- **Docker / LocalStack** — same as Day 01: Docker runs everything in throwaway boxes; LocalStack is
  a free, local stand-in for Amazon S3 so there's no AWS account, no cost, and no API limits.

---

## 4. How to run it

**You need:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) running. Nothing else.

```bash
cd days/day-02-incremental-load
docker compose up --build --abort-on-container-exit
```

**What you should see:**
```
1. First run — watermark starts at epoch, so everything new is ingested
   source=300  ingested=300  watermark 1970-01-01... -> 2026-06-12T09:58:58
2. Source grew by 200 — incremental run ingests ONLY the new rows
   source=500  ingested=200  skipped(old)=300  watermark ... -> ...10:58:38
3. Volume moved: incremental vs full reload
   full reload would have read 800 rows across the 2 runs
   incremental read only 500 rows  (38% less)
4. Late data — an event behind the watermark is SILENTLY SKIPPED
   source=501  ingested=0  <-- the late visit was missed
RESULT
   PASS: ...
```

**Clean up (always):**
```bash
docker compose down -v
```

---

## 5. What the code actually does

`code/incremental_loader.py` is the whole pattern in two moves, run once per execution:

1. **Read the watermark.** First run, there's no watermark file, so it defaults to the epoch
   (`1970-01-01...`) — meaning "everything is new".
2. **Select & write the new rows.** Keep only source rows where `event_time > watermark`. Write them
   to a fresh partition `bronze/visits/ingested_at=<run-id>/data.csv`.
3. **Advance the watermark** to the newest `event_time` just ingested (and never move it backward).

The demo grows the source between runs so you can watch run 2 ingest only the 200 *new* rows and
skip the 300 it already has.

### The trap, made real (section 4)
After the watermark has moved to ~10:58, a straggler visit arrives with `event_time` of 09:30 —
*earlier* than the watermark. The filter `event_time > watermark` skips it, so it's **lost**. The
demo asserts `ingested == 0` to prove the data loss is real, not hand-waving.

> The fix for this is a *later* pattern (a lookback window / late-data integrator, Chapter 3). Today
> we only need to **see** the problem clearly.

---

## 6. Why it saves so much

A **full** loader re-reads the entire source every run. Across our two runs that's 300 + 500 = **800
rows read**. The **incremental** loader read only the new rows: 300 + 200 = **500** — about **38%
less**. The bigger and older the dataset, the larger that saving becomes.

---

## 7. Consequences (the trade-offs)

- **You now hold state.** The watermark must be stored and protected. Lose it and you either
  re-ingest everything or skip data.
- **Late / out-of-order data is a real hazard** when the delta column is event time (shown above).
- **Pagination:** `list_objects_v2` caps at 1000 keys per call — fine here, paginate in production
  (flagged in the code comments).
- **The book's other flavour:** if the source is already split into time partitions, the run can
  derive *which* partition to read from the clock (e.g. a job at 11:00 reads the 10:00 partition)
  and doesn't need to remember a watermark at all. We implemented the watermark flavour because the
  state-keeping is the interesting part.

---

## 8. How this maps to the book and the author's code

- **Book:** Chapter 2, "Incremental Load" → "Pattern: Incremental Loader", including its real-time /
  late-data warning.
- **Author's repo:** [`chapter-02/02-incremental-load`](https://github.com/bartosz25/data-engineering-design-patterns-book/tree/master/chapter-02/02-incremental-load)
  (Spark/Airflow, time-partition flavour).
- **Our version:** the delta-column flavour on **S3 (LocalStack) + Python/boto3**, watermark stored
  as a small S3 object. Same pattern, AWS/S3 technology, runs anywhere.

---

## 9. Files in this folder

| File | What it is |
|------|-----------|
| `docker-compose.yml` | starts LocalStack (S3) + the loader container |
| `Dockerfile` | builds the tiny Python loader image |
| `code/incremental_loader.py` | watermark read/advance + partitioned writes |
| `code/run.py` | the runnable demo with assertions (incl. the late-data miss) |
| `requirements.txt` | Python dependencies (`boto3`, `moto`) |
| `.env.example` | config + how to point at LocalStack or real AWS |
| `index.html` | interactive watermark-sweep explainer (open in a browser) |
| `context.md` | what you should be able to explain after today |
| dataset | `../../datasets/incremental-load/` (three visit batches + generator) |

---

## 10. Don't have Docker? Run it in pure Python
```bash
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
python code/run.py                                   # USE_MOTO defaults to 1 (in-process mock)
```

## 11. Always clean up
```bash
docker compose down -v
```
Yesterday: [Day 01 — Full Loader](../day-01-full-load/README.md). Today is the answer to its volume problem.
