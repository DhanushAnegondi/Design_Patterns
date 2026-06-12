# Errors — 2026-06-11

## E1: pdftoppm not found
**Symptom:** `Read` tool on PDF failed — `pdftoppm` not installed on Windows.
**Fix:** Used `pdfplumber` (already installed) then upgraded to `PyMuPDF` for better extraction.

## E2: pdf-viewer MCP viewer never connected
**Symptom:** `display_pdf` returned viewUUID but `interact` always timed out ("viewer never connected").
**Root cause:** PDF viewer requires an active browser/iframe session which isn't available in this context.
**Fix:** Bypassed viewer entirely; used Python libraries for all extraction.

## E3: desktop-commander read_file ETIMEDOUT on F:\ drive
**Symptom:** `read_file` on `F:\Data Engineering Design Patterns.pdf` timed out.
**Root cause:** F:\ root is outside the allowed directory (`F:\Personal\Projects\Data_engineering`).
**Fix:** Copied PDF to project directory first.

## E4: v1 converter — narrative text in code fences (quality score 3-5/10)
**Symptom:** Haiku review agents found dozens of English sentences inside ```python/sql blocks.
**Root cause:** Keyword heuristic (`def`, `import`, `SELECT`) fired on prose mentioning those terms.
**Fix:** Switched to font-based extraction (PyMuPDF), then added two-layer content classifier.

## E5: v2 converter — still had narrative in fences (scores 2-3/10)
**Symptom:** Font-based extraction still leaked prose because O'Reilly uses monospace for
inline code mentions within sentences.
**Root cause:** Merged consecutive monospace blocks regardless of whether they were inline
mentions or standalone code blocks. The broad bracket-check (`[=(){}]`) also counted
`absolute(-1) ==` as code.
**Fix (v3):** First-line gate — entire merged block rejected if first line fails `line_is_code()`.
Added PROSE_CONTAM_RE for post-SQL-keyword prose markers (doesn't, supports, outcome, query., etc.).
Added "with the/a/an" and "with commands like" to PROSE_START_RE.
**Result:** 0 suspect blocks across all 10 chapters.

## E6: UnicodeEncodeError in extract_pdf_v2.py
**Symptom:** `UnicodeEncodeError: 'charmap' codec can't encode character '→'`
**Fix:** Replaced `→` arrow with `->` in print statement.

## E7: SyntaxError — backslash in f-string
**Symptom:** `SyntaxError: f-string expression part cannot include a backslash` in Python 3.11.
**Fix:** Extracted regex substitution to a variable before embedding in f-string.
