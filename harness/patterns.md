# Harness — learned failure patterns

Each entry: the failure class → the fix that worked → a probe to detect recurrence.
Agents read this at Orient and are bound by it. Append on top, dated. This file makes the
system stricter over time — same mistake twice is a process failure.

## Format
```
### P-NN: <short failure class>  (first seen YYYY-MM-DD)
Symptom: ...
Root cause: ...
Fix: ...
Probe: <command or check that detects recurrence>
```

## Seeded patterns (carried from prior session)

### P-01: narrative prose wrapped in code fences (PDF→MD)  (2026-06-11)
Symptom: English sentences mentioning code terms got fenced as ```python/sql.
Root cause: keyword/font heuristics fire on prose; O'Reilly uses monospace for inline mentions.
Fix: two-layer classifier; first line of a block must itself be real code.
Probe: `python check_fences.py` (in ../../) → must report 0 suspect blocks.

### P-02: code that only runs on the author's machine  (seeded, watch from Day 1)
Symptom: hardcoded abs paths / real AWS creds / Docker-only steps with no teardown.
Root cause: copying reference impl without adapting for portability.
Fix: moto/LocalStack local default; env vars; relative paths; verifier runs in clean venv.
Probe: verifier spins a fresh venv with ONLY the day's requirements.txt and runs run.py.
