# DEDP Learning — design patterns, one day at a time

A hands-on learning log for *Data Engineering Design Patterns* (Bartosz Konieczny, O'Reilly 2025).
Every day I take one design pattern from the book, implement it from scratch in my own words and my
own data, explain it to myself in an interactive page, and commit it. The point is to be able to
re-implement any DE pattern under pressure — and to show that journey publicly.

## How it works
- `/today_cron` picks the next concept, builds a complete day, verifies it runs on any machine,
  and stages it for commit. (See `.claude/commands/today_cron.md`.)
- Every day lives in `days/day-NN-<concept>/` and is self-contained:
  `README.md` · `index.html` (interactive explainer) · `code/` · `context.md` · `.env.example`
  · `requirements.txt`.
- Datasets are modular, one folder per concept under `datasets/`.
- A reviewer + verifier + watchdog check every day for correctness, portability, and honesty.

## Layout
```
days/            one folder per concept (the learning units)
datasets/        modular datasets, one folder per concept
.claude/         agents, the /today_cron command, installed skills (impeccable, find-skills)
harness/         the project's self-improvement memory (failure patterns, checklists)
tracker/         concept ladder + git/push history
ledger/          per-session work logs
```

## Source & reference
- Book corpus (Markdown): `../Data Engineering Design Patterns/`
- Author's reference code: https://github.com/bartosz25/data-engineering-design-patterns-book
- Implementations are my own clean versions, technically faithful to the book.

## Running a day
```bash
cd days/day-01-full-load
python -m venv .venv && .venv/Scripts/activate   # Windows; use source .venv/bin/activate on *nix
pip install -r requirements.txt
cp .env.example .env
python run.py
```
Open `index.html` in a browser for the interactive explainer.

## Progress
See `tracker/tracker.md`.
