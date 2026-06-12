# DEDP Learning — project rules (authoritative)

This project turns the textbook *Data Engineering Design Patterns* (Bartosz Konieczny,
O'Reilly 2025) into a **daily, hands-on learning system**. Each day the learner picks up one
concept, implements it for real, sees it explained interactively, and commits the result to
GitHub. The end goal is a public portfolio that proves the learner can solve any DE problem.

This file OVERRIDES global rules where they conflict. Read it fully before acting.

## The objective (the "why")
- **Learner:** Dhanush — recently-hired data engineer, learns fast from *why* before *how*,
  wants beginner-first explanations. Real stack: Snowflake / AWS / Airflow / Power BI / Jenkins
  / Git / Python / Kafka.
- **Goal:** Understand each design pattern deeply enough to re-implement it from scratch, in his
  own words and his own data — not copy the author. Build a daily-commit GitHub portfolio that
  shows the learning journey and proves problem-solving skill.
- **Definition of done for a concept:** working code that runs on *any* device + an interactive
  HTML explainer + a context file + a dataset + a clean commit, all verified by agents.

## Source of truth (grounding — non-negotiable)
1. **Primary corpus:** the chapter Markdown files at
   `book-corpus/chapters/` (00_INDEX.md + ch01–ch10). This is the book. NOTE: `book-corpus/` is
   git-ignored — it is copyrighted O'Reilly content kept LOCAL ONLY for grounding, never published.
2. **Reference implementation:** the author's repo
   `https://github.com/bartosz25/data-engineering-design-patterns-book` (chapter-NN folders).
   Use it to fill gaps where book snippets are vague — but build *our own* cleaner version.
3. If the book and a claim disagree, the book wins. If something is genuinely unclear in both,
   **web-search to confirm** before writing it. Never invent API surface, flags, or behavior.
4. The watchdog treats any unsourced technical claim as a hallucination until grounded.

## What `/today_cron` produces (the daily unit)
Running `/today_cron` in this project:
1. Reads `tracker/tracker.json` → finds the next not-yet-done concept (ordered by chapter).
2. Reads the relevant chapter MD from the corpus + the matching author-repo folder.
3. Generates a self-contained day folder under `days/day-NN-<concept-slug>/`:
   - `README.md` — step-by-step guide (problem → solution → consequences → how to run)
   - `index.html` — **interactive** explainer (diagrams, blocks, animations) built with the
     **impeccable** skill, not default styling. Must teach the concept visually.
   - `code/` — the runnable implementation (Python; SQL/Scala when the pattern needs it)
   - `context.md` — the "context file": what concept, which chapter/pages, what the learner
     should be able to explain after, links to corpus + author ref, the ONE new idea it teaches
   - `.env.example` — every config the code needs, with safe local defaults (never real secrets)
   - `requirements.txt` — pinned deps for that day (reproducibility)
   - `docker-compose.yml` + `Dockerfile` — the PRIMARY way to run the day: bring up the needed
     services (LocalStack for S3, Postgres/Spark/Kafka when the pattern needs them) + a runner
     container. `docker compose up --build --abort-on-container-exit` must run it end-to-end.
   - `README.md` must be **beginner-first and exhaustive**: explain the concept like to a beginner,
     define every term (S3, bucket, Docker, LocalStack, ...), give exact run + teardown commands,
     walk the code, list consequences, and map to the book + author repo. Everything in the README.
4. Wires the dataset under `datasets/<concept-slug>/` (see Datasets).
5. Runs the agentic verification loop (below). Only a PASS is "ready to commit."
6. Updates `tracker/tracker.json` + `tracker/tracker.md` and writes the suggested commit message.
7. Does NOT push. The learner pushes. The tracker then records the push on the next run.

## Runs-on-any-device rule (hard)
The day's code MUST run on a clean machine with no AWS account and no API limits. Two paths:
- **PRIMARY — Docker.** `docker compose up --build` brings up **LocalStack** (a local, free S3 with
  the real S3 API and no rate limits) plus a runner container. This mirrors how the book's author
  ships every example (Docker) and is what we commit/push. Always `docker compose down -v` after.
- **FALLBACK — pure Python.** The same code also runs with an in-process mock (`moto`, `USE_MOTO=1`)
  for a quick check without Docker.
- `.env.example` shows how to point at real AWS, but the default path is always local/free.
- No hardcoded absolute paths. Use paths relative to the day folder or env vars.
- No real credentials. Ever. `.env.example` only; `.env` is git-ignored.
- A `run.py` or documented command must execute end-to-end and print a verifiable result.
- If Docker is used (LocalStack/Spark), the code must `docker compose down` after — see the
  Docker stop rule below.

## Datasets (modular)
- One folder per concept: `datasets/<concept-slug>/`.
- Prefer formats the book/pattern uses: CSV for raw ingestion, JSON for semi-structured, Parquet
  /Delta for lakehouse layers.
- Each dataset folder has a `DATASET.md`: source (synthetic / author-repo / public), schema,
  row count, how it was generated, and which concept consumes it.
- Synthetic generators live next to the data as `generate.py` so data is reproducible, not committed
  as opaque blobs when large. Small sample data may be committed directly.
- Public-data option: `https://github.com/awesomedata/awesome-public-datasets`.

## Skills policy (use the good skills, not defaults)
- **HTML / any frontend or visual explainer → use `impeccable`.** Agents that build HTML are
  instructed to call `/impeccable` (polish/audit) and obey its 41 anti-slop detector rules.
  Default/unstyled HTML is a FAIL.
- **Discovering a better skill for a task → use `find-skills`** (`npx skills find <query>`)
  before hand-rolling something a skill already does well.
- Agents must be told which skill to use; they may not fall back to default behavior when a
  designated skill exists.

## Agent roster (every agent declares its model)
Spawn each agent with its model set explicitly. Never let a swarm inherit a big model.

| Agent | Model | Role |
|-------|-------|------|
| `concept-builder` | Sonnet | Reads corpus + author ref, writes README/code/context for the day |
| `html-builder` | Sonnet | Builds the interactive `index.html` via the impeccable skill |
| `dataset-builder` | Haiku | Generates/wires the modular dataset + DATASET.md |
| `verifier` | Sonnet | Creates a clean venv, runs the code, confirms it works on any device |
| `reviewer` | Sonnet | Adversarial: checks code+docs against book AND author repo for technical gaps |
| `watchdog` | Sonnet | Runs every step; flags hallucination / unsourced claims / scope drift |
| `logger` | Haiku | Writes ledger logs, errors, changes; updates tracker |
| roadblock specialist | Opus | Summoned ONLY when verifier/reviewer fail 3× on one step |

Model ladder: Haiku < Sonnet < Opus. Fable 5 is reserved (≈2× Opus cost) — not used here unless
explicitly requested for a single highest-stakes call.

## The loop (per concept / per day)
1. **Orient** — load `ledger/reviewer-brief.md` + `ledger/lessons.md` + `harness/patterns.md`.
2. **Build** — `concept-builder` + `dataset-builder` + `html-builder` produce the day folder.
3. **Verify** — `verifier` runs the code in a fresh venv on the day's `requirements.txt`.
4. **Review** — `reviewer` checks against book + author repo; `watchdog` checks for hallucination.
5. **Correct** — on FAIL, route fixes back to the builder. Max 3 cycles per step, then escalate to
   the Opus roadblock specialist; if still failing, log to `errors.md` and mark the day BLOCKED.
6. **Log** — `logger` appends to ledger (logs/errors/changes) and updates the tracker.
7. **Self-improve** — repeated failure class → write it to `harness/patterns.md` and
   `ledger/lessons.md`; future Orient folds these in, so the system gets stricter over time.

## Self-improvement harness (hard rule — the system must learn)
- `harness/patterns.md` — recurring failure patterns + the fix that worked + a probe to detect
  recurrence. Every reviewer/watchdog FAIL that repeats a class goes here.
- `harness/verification-checklist.md` — the living checklist the verifier/reviewer run each day.
  It grows when a new failure mode is found; it never silently shrinks.
- `harness/skills-notes.md` — what we learned about using impeccable/find-skills well.
- Agents read the harness at Orient and are bound by it. The harness is the project's memory of
  its own mistakes — same mistake twice is a process failure, not bad luck.

## Tracker (concept + commit/push history)
- `tracker/tracker.json` — machine state: every concept (chapter, slug, status
  `todo|building|verified|committed|pushed`), the commit SHA, timestamps, and a `pushes[]` log.
- `tracker/tracker.md` — human-readable progress table.
- On each `/today_cron` run: detect git state (`git log`, `git status`, remote) and reconcile —
  record new commits and **detect/record every push** (including multiple pushes on one concept).
- The tracker is the answer to "what have I learned and shipped so far."

## Ledger (per global rules, lives here)
`ledger/` with `reviewer-brief.md`, `lessons.md`, and dated `YYYY-MM-DD/` folders holding
`logs.md`, `errors.md`, `changes.md`, `handoff.md`. Log in parallel as work happens — never
retroactively at the end. (Global rules' L5 lesson: a session that ends with an empty ledger is a
process failure.)

## Git policy
- This folder is its own git repo, mapped to the learner's GitHub.
- Agents/Claude make **local commits** only. **Never push** without the learner's explicit go-ahead.
- `.env`, `venv/`, large generated datasets, and `node_modules/` are git-ignored.
- One concept = one focused commit. Commit message format:
  `dayNN(<concept>): <what was learned/implemented>`.

## Docker stop rule
If a day uses Docker (LocalStack, Spark, Postgres), stop the stack immediately after each
verification step — never leave containers running between steps or sessions.

## Style
Terse, imperative. No marketing fluff, no emoji in committed files. Sentence-case headings.
Match surrounding code's idioms. Report outcomes faithfully — a failed verify is reported with the
error, never hidden.
