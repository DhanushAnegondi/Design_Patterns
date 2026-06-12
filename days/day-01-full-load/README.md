# Day 01 — Full Loader (on S3, in Docker)

> **Chapter 2 — Data Ingestion · pattern: Full Loader.**
> The one idea to take away: **when you replace a whole dataset, publish the new copy by flipping a
> pointer — never by deleting the old one first.**

---

## 1. Explain it like I'm five

Imagine a whiteboard that always shows "today's list of devices". Every few days someone hands you
a brand-new list and says "replace the whole thing". You have two ways to do it:

- **The bad way:** erase the whole whiteboard, then start writing the new list. If your boss walks
  past *while the board is empty*, they think we have zero devices. Panic.
- **The good way:** write the new list on a *second* whiteboard, and only when it's completely
  finished do you swap which board is hanging on the wall. Nobody ever sees a blank board.

That swap is the entire lesson. On S3 the "which board is on the wall" is a tiny file called a
**pointer**, and swapping it is one instant operation.

---

## 2. The real problem (our blog-analytics project)

We're building the **Silver layer** (cleaned, enriched data). One job needs extra details about each
**device** (browser, OS, screen size) that come from an outside provider. That device list:

- changes only a few times a week,
- is small (well under a million rows),
- and — crucially — has **no "last updated" column**.

Because nothing tells us *which* rows changed, we can't be clever and load "just the changes". We
have to reload the **entire** list every time. That is the **Full Loader** pattern.

---

## 3. Words you need first (skip if you know them)

- **Amazon S3** — a place in the cloud to store files ("objects"). Think of it as an infinite hard
  drive you talk to over the internet.
- **Bucket** — a top-level folder in S3. Ours is called `silver-layer`.
- **Object / key** — a file in a bucket and its full path. e.g. the object with key
  `devices/safe/_CURRENT` is a file at that path.
- **Full load** — replace the whole dataset every run (the opposite of "incremental", which is
  tomorrow's lesson).
- **Docker** — a way to run software in a clean, throwaway box ("container") so it works the same on
  every computer. You don't install Python or S3 — Docker does it inside the box.
- **LocalStack** — a free program that pretends to be Amazon S3 **on your own laptop**. Same
  commands as real AWS, but no account, no bill, and no rate limits. We run it as one of the
  Docker containers, so the code thinks it's talking to real S3.

**Why Docker here?** So you can run this with zero setup and zero AWS cost, and so it behaves
identically on any machine. The author of the book uses Docker for the same reason; we use
LocalStack to stay in the S3 world without needing a real AWS account.

---

## 4. How to run it (the whole thing)

**You need:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and
running. That's it — no Python, no AWS account.

```bash
cd days/day-01-full-load
docker compose up --build --abort-on-container-exit
```

What happens, in order:
1. Docker starts **LocalStack** (your pretend-S3) and waits until it's ready.
2. Docker builds a tiny **loader** container (Python + the `boto3` AWS library).
3. The loader runs `code/run.py` against LocalStack and prints four numbered sections.

**What you should see** (the important lines):
```
1. Safe versioned Full Loader — first daily snapshot
   _CURRENT -> 2026-06-11 | consumer reads 500 rows
2. Next day — full reload ...
   _CURRENT -> 2026-06-12 | consumer reads 520 rows
   versions retained: ['2026-06-11', '2026-06-12']
3. Naive drop-then-insert — exposing the consistency window
   >>> mid-overwrite: consumer reads 0 rows  <-- data has vanished
4. Rollback — re-point _CURRENT at yesterday's version
   _CURRENT -> 2026-06-11 | consumer reads 500 rows
RESULT
   PASS: ...
```

**Clean up when you're done** (stops and deletes the containers — always do this):
```bash
docker compose down -v
```

---

## 5. What the code actually does

There are two loaders in `code/full_loader.py`. Both put the same data in S3; only the *publishing
method* differs.

### The WRONG way — `NaiveFullLoader`
1. Delete the live file `devices/naive/current/data.csv`.
2. Write the new file.

Between steps 1 and 2 the data is **gone**. Section 3 of the demo proves it: a reader checking in
that moment sees **0 rows**. In real life two jobs run at slightly different times, so this *will*
bite you.

### The RIGHT way — `SafeVersionedFullLoader`
1. Write the new snapshot to an **immutable, versioned** path nobody is reading yet:
   `devices/safe/versions/2026-06-12/data.csv`.
2. Flip one tiny pointer file `devices/safe/_CURRENT` to contain `2026-06-12`.

A reader always does: read `_CURRENT` → read that version's file. So it only ever sees a **complete**
dataset. Step 2 is a single S3 `PUT`, which is atomic — there is no "half-swapped" moment.

Because old versions are never deleted, **rollback is free**: to go back to yesterday, point
`_CURRENT` at the older version (section 4).

---

## 6. The mechanism in one picture

```
new snapshot ─▶ versions/2026-06-12/data.csv   (immutable; readers ignore it for now)
                                   │
                          flip _CURRENT (1 atomic PUT)
                                   │
reader ──▶ read _CURRENT ──▶ read that version  ──▶ always a COMPLETE dataset
```

This is the object-store version of the classic database trick: build the new table, then swap the
**view** so consumers switch over instantly. (The book shows the database-view version; ours is the
S3 version. Same idea.)

---

## 7. Consequences (when NOT to be naive about this)

- **Volume:** you move the *entire* dataset every run. Fine for small, slow reference data; wasteful
  for big, fast-growing data — that's why tomorrow's **Incremental Loader** exists.
- **Consistency:** never delete-then-write in place. Always write-new-then-swap-pointer.
- **Concurrency:** two full loads at once could flip `_CURRENT` to a version another process is still
  writing. The book's Airflow version prevents this with `max_active_runs=1`; a production S3
  version would serialize loads (a lock or single-writer scheduler).
- **Pagination:** the code lists S3 objects with `list_objects_v2`, which returns at most 1000 keys
  per call. Fine at demo scale; in production you'd paginate. (Flagged in the code comments.)

---

## 8. How this maps to the book and the author's code

- **Book:** Chapter 2, "Full Load" → "Pattern: Full Loader" (Problem / Solution / Consequences).
- **Author's repo:** [`chapter-02/01-full-load`](https://github.com/bartosz25/data-engineering-design-patterns-book/tree/master/chapter-02/01-full-load)
  — implemented with **Apache Spark + Airflow + PostgreSQL** and a Docker data-generator.
- **Our version:** the same pattern on **S3 (LocalStack) + Python/boto3**, chosen to match the
  AWS/S3 stack and to run anywhere with no AWS bill. The technology is swapped on purpose; the
  pattern (full reload + atomic swap + keep previous version) is identical.

---

## 9. Files in this folder

| File | What it is |
|------|-----------|
| `docker-compose.yml` | starts LocalStack (S3) + the loader container |
| `Dockerfile` | builds the tiny Python loader image |
| `code/full_loader.py` | the two loaders (naive vs safe versioned) |
| `code/run.py` | the runnable demo with assertions |
| `requirements.txt` | Python dependencies (`boto3`, `moto`) |
| `.env.example` | config + how to point at LocalStack or real AWS |
| `index.html` | interactive visual explainer (open in a browser) |
| `context.md` | what you should be able to explain after today |
| dataset | `../../datasets/full-load/` (two device snapshots + generator) |

---

## 10. Don't have Docker? Run it in pure Python

The same code runs **without Docker** using an in-process S3 mock (`moto`):
```bash
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
python code/run.py                                   # USE_MOTO defaults to 1
```
Docker is the recommended path (it uses a *real* S3 API via LocalStack); the moto path is a
zero-dependency fallback for quick checks.

---

## 11. Always clean up
```bash
docker compose down -v
```
Leaving LocalStack running in the background slows your machine. Stop it the moment you're done.
