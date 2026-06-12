---
description: Generate, verify, and stage today's design-pattern concept (code + interactive HTML + dataset + context) ready to commit. Tracks git/push history.
argument-hint: "[optional: concept-slug to force a specific concept]"
---

# /today_cron — produce today's learning unit

You are the LEAD orchestrator for the DEDP daily learning loop. Read `CLAUDE.md` fully before
acting. Follow this exactly. Use the project agents with their declared models — never let a swarm
inherit a large model.

## 0. Orient (always first)
- Read `ledger/reviewer-brief.md`, `ledger/lessons.md`, `harness/patterns.md`, and
  `harness/verification-checklist.md` into context.
- Read `tracker/tracker.json`. Reconcile git state: run `git log --oneline -n 5` and
  `git status --porcelain` and `git remote -v`. Record any new commits since `last_local_sha`,
  and detect any new pushes (compare local vs `@{u}` if a remote exists). Update the tracker's
  `git` block and `pushes[]` for anything that happened since last run — including repeat pushes
  on a concept already pushed.

## 1. Pick the concept
- If `$ARGUMENTS` names a concept slug, use it. Otherwise pick the first concept in
  `tracker.json` with status `todo` (lowest chapter, then order). Assign it the next `day` number.
- Mark it `building`. Create `days/day-NN-<slug>/` and `datasets/<slug>/`.

## 2. Build (parallel where independent)
Spawn, each with its model set explicitly:
- `concept-builder` (sonnet) → README.md (beginner-first, exhaustive), code/ (runnable),
  context.md, .env.example, requirements.txt, AND `docker-compose.yml` + `Dockerfile` (PRIMARY run
  path: LocalStack for S3 + a runner container; `docker compose up --build` must work end-to-end,
  `docker compose down -v` after). Grounded in the chapter MD + author repo; web-search only to
  confirm. No real cloud / no API limits — LocalStack locally.
- `dataset-builder` (haiku) → `datasets/<slug>/` + DATASET.md (reproducible, right format).
- After those return, `html-builder` (sonnet) → interactive `index.html`. It MUST use the
  impeccable skill and pass the detector: `npx impeccable detect days/day-NN-<slug>/index.html`.
  Default styling is a FAIL.

## 3. Verify → Review → Watch (the gate)
- `verifier` (sonnet): fresh venv from the day's requirements.txt, run `python run.py`, capture
  output, confirm runs-on-any-device. Returns PASS/FAIL + actual output.
- `reviewer` (sonnet): adversarial fidelity check vs book AND author repo. PASS/FAIL + gaps.
- `watchdog` (sonnet): scan all step outputs for hallucination / unsourced claims / scope drift.
- Also run the impeccable detector on index.html and require 0 anti-patterns (or documented,
  justified exceptions).

## 4. Correct
- On any FAIL, route the specific fixes back to the relevant builder. Re-verify. Max 3 cycles per
  step. If still failing, summon the Opus roadblock specialist for that one step. If it still
  fails, log to `errors.md` and mark the day `BLOCKED` (do not fake a PASS).

## 5. Log + stage (logger, haiku)
- Append to `ledger/<today>/logs.md`, `errors.md`, `changes.md`; refresh `handoff.md`.
- Update `tracker.json` + `tracker.md`: status → `verified`, fill `verified_at`.
- Stage the day: `git add days/day-NN-<slug> datasets/<slug>` and write the suggested commit
  message to the day folder as `COMMIT_MSG.txt` in the form `dayNN(<slug>): <what was learned>`.
- Do NOT commit or push automatically unless the learner says so. Present the commit command for
  them to run. When they push, the next `/today_cron` Orient step records it.

## 6. Self-improve
- If any reviewer/watchdog finding repeats a known class, append it to `harness/patterns.md` and
  `ledger/lessons.md` with a probe. The system must get stricter over time.

## Output to the learner
A short report: which concept, what it teaches (the ONE new idea), verify result (with real
output), reviewer/watchdog verdicts, the detector result, and the exact commit command to run.
