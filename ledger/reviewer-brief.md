# Reviewer brief — DEDP Learning

## What this project is
A daily hands-on learning system over the textbook *Data Engineering Design Patterns*
(O'Reilly 2025). Each day = one concept implemented for real + interactive HTML explainer +
dataset + clean commit. Goal: portfolio that proves the learner can re-implement any DE pattern.

## Grounding (truth hierarchy)
1. Chapter MD corpus at `book-corpus/chapters/`
2. Author repo `bartosz25/data-engineering-design-patterns-book`
3. Web search only to confirm when 1 and 2 are unclear. Never invent.

## What "good" means here
- Code RUNS on any device: fresh venv + day's requirements.txt, no real cloud, no secrets,
  no hardcoded absolute paths. S3 patterns use moto/LocalStack locally by default.
- The implementation is the learner's OWN clean version, not a copy of the author's repo, but
  technically faithful to the pattern (Problem/Solution/Consequences hold).
- Interactive `index.html` actually teaches: diagrams + blocks + animation, built with the
  impeccable skill. Unstyled/default HTML = FAIL.
- Every technical claim is traceable to the book or author repo. No hallucinated APIs/flags.
- `context.md`, `.env.example`, `requirements.txt`, dataset + `DATASET.md` all present.

## What a reviewer MUST check each day
1. Does the code execute end-to-end in a clean venv and print a verifiable result?
2. Does it avoid real cloud/secrets/abs-paths (runs-on-any-device)?
3. Is the pattern implemented faithfully vs the book AND the author repo? Name any technical gap.
4. Are all API calls / library flags real? (cross-check docs on any doubt)
5. Is the HTML genuinely interactive and impeccable-polished, not slop?
6. Is the day folder complete (README, index.html, code/, context.md, .env.example, requirements)?
7. Is the dataset modular, documented, and reproducible?
8. Tracker + ledger updated; commit message follows `dayNN(<concept>): ...`.

## Verdict format
```
VERDICT: PASS | FAIL
- [PASS/FAIL] <check> — note
FIXES (if FAIL): <specific, file:line where possible>
```
