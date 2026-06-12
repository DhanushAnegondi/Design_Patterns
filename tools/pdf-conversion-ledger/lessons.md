# Lessons — Data Engineering Design Patterns Project

## 2026-06-11

### L1: Font detection alone is not enough for code-fence classification in O'Reilly PDFs
O'Reilly books use monospace font for BOTH actual code blocks AND inline code mentions
within prose (e.g., `TRUNCATE TABLE`, `withWatermark`). Font-based extraction marks all
of them as code, causing narrative sentences to be wrapped in fenced blocks.

**Fix that worked:** Two-layer classifier — font=code is necessary, plus a content gate:
first line of block must pass CODE_START_RE AND must NOT trigger PROSE_START_RE or
PROSE_CONTAM_RE. First-line gate is the critical rule: if first line reads like English,
the whole merged block is prose.

**Probe to run after any future PDF conversion:**
```python
bad = [b for b in re.findall(r'```\w+\n(.*?)```', md, re.DOTALL)
       if PROSE_CHECK.search(b.strip().split('\n')[0])]
assert len(bad) == 0
```

### L2: pdfplumber truncates code; PyMuPDF preserves it
pdfplumber concatenates spans without spacing and can't distinguish code lines — produces
mid-word truncations (`should_create_t`, `job_argum`). Use `fitz.get_text("dict")` which
returns per-span font metadata, preserving code blocks faithfully.
**Rule:** Always use PyMuPDF when code preservation matters.

### L3: Never use keyword heuristics for fence/no-fence decisions
`if re.search(r'def |import |SELECT ', line)` fires on narrative ("the SELECT statement
performs..."). Keywords are for language tagging only (python/sql/scala), not for
deciding whether to fence at all.

### L4: Haiku for line-level bugs, Sonnet for structural/holistic quality
Haiku agents reliably caught prose-in-fences, missing ### tags.
Sonnet watchdog caught cross-chapter issues (index accuracy, pattern completeness).
Keep this split in future review workflows.

### L5: PROCESS FAILURE — ledger not maintained during session
The entire session (PDF extraction, 3 conversion iterations, image extraction, 2 review
workflows, 31+ agents, ~3M tokens) ran with no ledger, no logs, no errors recorded.
**Rule:** Create ledger/ on first file-write. Log each iteration failure to errors.md
immediately — never retroactively. A session that ends with empty ledger = process failure.
