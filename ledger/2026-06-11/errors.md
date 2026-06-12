# Errors — 2026-06-11 / 2026-06-12

## E1: `npx impeccable skills install` hangs, then fails on `unzip`
Symptom: install ran ~30 min with no output (hung on a Y/n prompt), then failed: `'unzip' is not
recognized`. Windows has no `unzip`.
Root cause: (a) interactive prompt with no piped stdin; (b) installer shells out to `unzip`.
Fix: pipe empty stdin (`"" | npx ...`) to auto-answer; the zip downloads to %TEMP%; extract with
Expand-Archive and copy the `.claude` subtree into the project. Logged to harness/skills-notes.md.

## E2: f-string / unicode issues in helper scripts (carried habit)
Avoided this time by keeping generators simple; noted that Windows console is cp1252, so avoid
non-ASCII in print().

## E3: impeccable detector findings on HTML (expected, not bugs)
Day 1: eyebrow chip, all-caps body, wide tracking, em-dash overuse → fixed in 1 cycle.
Day 2: flat type hierarchy, numbered-section-markers (axis 09/10/11), tight-leading → 3 cycles.
Root-caused tight-leading to the analyzer inheriting body computed px line-height (harness P-04).
All resolved to exit 0.
