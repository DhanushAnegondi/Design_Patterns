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
