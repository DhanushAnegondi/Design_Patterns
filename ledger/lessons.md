# Lessons — DEDP Learning

Recurring failure patterns. Feeds the reviewer brief and the harness. Gets stricter over time.

## Seeded from the PDF→MD conversion session (2026-06-11)
- Use PyMuPDF over pdfplumber for any further PDF work; font + content two-layer classifier for
  code fences. (See ../../memory/pdf-extraction-lessons.md.)
- Ledger-first: create and log to the ledger on the first file write, never retroactively.
  A session that ends with an empty ledger is a process failure.

## 2026-06-12 — first 2 days
- **Verify the numbers a demo prints, not just that it runs.** The Day 02 verifier passed (exit 0,
  asserts green) but the reviewer caught a real bug: the "volume saved" line computed
  `len(source)*2` (final size doubled = 1000) instead of summing the source size at each run
  (300+500 = 800), overstating savings as 50% vs the true 38%. A passing run with a wrong printed
  statistic is still wrong. → Reviewer must recompute any headline number the demo claims.
  (Probe: for any printed %/ratio, derive it by hand from the run's own intermediate values.)
- **Flag silent-truncation APIs.** `list_objects_v2` caps at 1000 keys/call; teaching code must
  carry a one-line "paginate in production" note so a learner doesn't copy a silent bug.

## (project lessons accumulate below as agents hit repeated failures)
