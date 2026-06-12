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

### P-03: impeccable anti-slop patterns to avoid on FIRST draft of any HTML  (2026-06-12)
The detector reliably flags these AI-slop tells. Build HTML without them from the start:
- tracked-caps "eyebrow" label above a big hero headline -> use a normal-case breadcrumb instead.
- text-transform:uppercase or letter-spacing >0.05em on anything that is body text (not a tiny label).
- more than 2 em-dashes in visible body copy -> use commas/colons/periods/parentheses.
- numbered display markers as section labels (01, 02, ...) AND any 2+ digit sequence the detector
  can read as one (e.g. axis ticks 09/10/11) -> use words ("earlier -> later", "first/second batch").
- flat type hierarchy: keep few sizes with >=1.25 ratio steps (0.8rem / 1rem / 1.25rem / big display).
Probe: `npx impeccable@2.3.2 detect <file>` must exit 0 (0 anti-patterns).

### P-05: a tool's non-zero exit / red stderr is NOT necessarily a failure  (2026-06-12)
Symptom: `npx impeccable detect` printed red text and "exit 2"; looked like repeated failures.
Reality: exit 2 = "anti-patterns found" (the gate working); PowerShell renders a native program's
stderr in red even on success (NativeCommandError wrapping), which looks alarming but isn't.
Fix / how to apply: run system commands (docker, npx, git) via the Bash tool, or capture output and
print only the relevant lines — do not pipe native stderr through PowerShell with `2>&1 | Out-String`.
Interpret exit codes by the tool's own contract, and say plainly "the detector found N issues,
fixing them" instead of surfacing a wall of red. Don't repeat the same loud command many times.

### P-06: Docker (LocalStack) is the primary run path, not moto  (2026-06-12)
Why: the book's author ships every example via Docker; real S3 has API limits/cost; LocalStack gives
the real S3 API locally for free with no limits. Each day must ship docker-compose.yml + Dockerfile
and be verified with `docker compose up --build --abort-on-container-exit` (runner exits 0), then
`docker compose down -v`. moto/USE_MOTO=1 stays as a no-Docker fallback only.
Gotchas learned: (a) don't depend on a localstack healthcheck — wait for S3 in Python (retry
list_buckets); (b) make dataset path overridable via DATASET_DIR env so the container can mount it;
(c) LocalStack accepts any AWS creds (AWS_ACCESS_KEY_ID=test).

### P-04: impeccable "tight-leading" false-ish flag on large inheriting text  (2026-06-12)
Symptom: tight-leading "line-height 1.28x" on an element you never set to 1.28.
Root cause: the static-HTML analyzer inherits the body's COMPUTED px line-height into children, so
any body-text element with font-size > body (e.g. a 1.25rem lede inheriting body's 25.6px) reads as
25.6/20 = 1.28x. Headings (h1-h6) are exempt; the rule only hits non-heading text >50 chars.
Fix: put an explicit unitless line-height (>=1.3, ideally 1.5) on every enlarged body-text element
(lede, intro paragraphs). Rule source: scripts/detector/rules/checks.mjs ~line 1594.
