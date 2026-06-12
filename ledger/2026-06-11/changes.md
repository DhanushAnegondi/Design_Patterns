# Changes — 2026-06-11

## Foundation built
- Project root `dedp-learning/` with skeleton: `.claude/{agents,commands,skills}`, `harness/`,
  `tracker/`, `ledger/`, `days/`, `datasets/`, `shared/`.
- `CLAUDE.md` — authoritative spec: objective, grounding hierarchy, `/today_cron` contract,
  runs-on-any-device rule, datasets policy, skills policy, agent roster + model policy, the loop,
  self-improvement harness, tracker, git policy.
- Ledger: reviewer-brief.md, lessons.md, dated logs/changes.
- Harness: patterns.md (seeded P-01, P-02), verification-checklist.md, skills-notes.md.
- Tracker: tracker.json (28 concepts, ordered by chapter) + tracker.md.
- Agents (.claude/agents/): concept-builder (sonnet), html-builder (sonnet), dataset-builder
  (haiku), verifier (sonnet), reviewer (sonnet), watchdog (sonnet), logger (haiku).

## Skills
- impeccable v2.3.2/skill 3.5.0 installed to `.claude/skills/impeccable/`. Installer's
  `skills install` shells out to `unzip` (absent on Windows) → worked around by extracting the
  downloaded temp zip with Expand-Archive and copying the `.claude` subtree into the project.
- Verified `npx impeccable detect <file>` works — caught low-contrast + overused-font on a sample
  (exit 2 = anti-patterns found). This is the anti-slop gate agents will call.
- find-skills installed via `npx skills add` (non-interactive, symlinked for Claude Code).

## Git
- Initialized git repo (main), scaffolding commit 506c217. Local only, no remote/push.

## Day 01 — Full Loader (commit 1a33064)
- datasets/full-load: generate.py (seed 42) → devices_snapshot_1.csv (500), _2.csv (520) + DATASET.md.
- code/full_loader.py: NaiveFullLoader (drop-insert, exposes 0-row window) + SafeVersionedFullLoader
  (immutable versions/<v>/ + atomic _CURRENT pointer swap + rollback). S3 via boto3, moto-mocked.
- code/run.py: 4-section demo with assertions. Verified in clean venv → exit 0, all PASS.
- README.md, context.md, .env.example (moto default + LocalStack/real switch), requirements.txt.
- index.html: interactive (SVG flow diagram + naive-vs-safe animated simulator). impeccable detect:
  4 findings → fixed (eyebrow→breadcrumb, dropped uppercase/wide-tracking, cut em-dashes) → exit 0.

## Day 02 — Incremental Loader (building)
- datasets/incremental-load: generate.py (seed 7) → visits_batch_1.csv (300), _2 (200), _late (1).
- code/incremental_loader.py: watermark read/advance + partitioned writes; event_time delta column.
- code/run.py: 4-section demo incl. the late-data miss. Verified in clean venv → exit 0, all PASS.
- index.html: interactive watermark-sweep simulator. impeccable detect: 3 cycles
  (flat-hierarchy, numbered-markers, tight-leading) → exit 0. Root-caused the tight-leading quirk
  (static analyzer inherits body computed px line-height) → harness P-04.
