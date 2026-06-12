# Harness — verification checklist (living)

The verifier and reviewer run this every day. It grows when a new failure mode appears; it never
silently shrinks. A day is "ready to commit" only when every MUST passes.

## Runs-on-any-device (verifier — MUST)
- [ ] Fresh venv created from the day's `requirements.txt` only — no global deps assumed.
- [ ] `python run.py` (or the documented command) executes end-to-end without error.
- [ ] It prints a verifiable result (row counts, file listing, assertion that PASSED).
- [ ] No real AWS/cloud call by default — moto/LocalStack used; `.env.example` shows the real-AWS switch.
- [ ] No hardcoded absolute paths; no real secrets anywhere; `.env` is git-ignored.
- [ ] If Docker used: stack is torn down (`docker compose down`) after the run.

## Technical fidelity (reviewer — MUST)
- [ ] Pattern implemented faithfully vs the chapter MD (Problem/Solution/Consequences hold).
- [ ] Cross-checked against the author repo folder; any deviation is intentional and noted.
- [ ] All library APIs / flags are real (cross-checked on any doubt). No invented surface.
- [ ] Edge cases the book calls out are handled or explicitly deferred in context.md.

## Learning value (reviewer — MUST)
- [ ] `context.md` names the ONE new concept the day teaches and what the learner can now explain.
- [ ] README has a clear step-by-step the learner can follow unaided.

## Interactive HTML (html reviewer — MUST)
- [ ] `index.html` opens standalone and renders (no broken assets, no external build step).
- [ ] Teaches visually: diagram(s) + conceptual blocks + at least one animation/interaction.
- [ ] Built/polished with the impeccable skill; passes its anti-slop detectors. Default styling = FAIL.

## Hygiene (watchdog — MUST)
- [ ] No unsourced technical claim (everything traces to book / author repo / confirmed docs).
- [ ] Scope is exactly the day's concept — no drift into other patterns.
- [ ] Tracker + ledger updated; commit message follows `dayNN(<concept>): ...`.

## Dataset (MUST)
- [ ] Dataset lives in `datasets/<concept-slug>/` with `DATASET.md` (source, schema, rows, how-made).
- [ ] Reproducible (generator script) or a small committed sample; format fits the pattern.
