# Changes — 2026-06-11

## PDF Extraction Pipeline

### extract_pdf.py (v1 — pdfplumber)
Extracted 805 pages into 10 per-chapter JSON files (extract_output/).
Identified chapter boundaries by scanning for "Chapter N" pattern in first 5 lines of each page.
Chapter ranges: Ch1 p24-35, Ch2 p36-101, Ch3 p102-184, Ch4 p185-258, Ch5 p259-358,
Ch6 p359-424, Ch7 p425-501, Ch8 p502-583, Ch9 p584-648, Ch10 p649-805.

### extract_pdf_v2.py (PyMuPDF font-aware)
Re-extracted using fitz.get_text("dict") — returns per-span font metadata.
Code blocks identified by monospace font detection (courier, mono, consola, etc.).
Produced extract_output_v2/ with blocks typed as "text" or "code".
Code block counts: Ch2=114, Ch3=135, Ch4=120, Ch5=148, Ch6=97, Ch7=88, Ch8=110, Ch9=97, Ch10=75.

### extract_images.py
Extracted 69 PNG images from PDF using PyMuPDF fitz.extract_image().
Skipped images < 80x80px (decorative elements).
Anchored images to Figure references in text; unanchored appended to ## Chapter Figures section.
Output: images/ch0N/ folders with fig_p<page>_<idx>.png files + images_manifest.json.

## MD Conversion Pipeline

### convert_to_md.py (v1 — keyword heuristic)
Used keyword regex to detect code blocks. Result: narrative prose wrapped in fences.
Abandoned after first watchdog review (scores 3-5/10).

### convert_to_md_v2.py (font-based, no content gate)
Used font type from v2 extraction. Still leaked prose because O'Reilly uses monospace
for inline code mentions. Abandoned after second watchdog review (scores 2-3/10).

### convert_to_md_v3.py (font + content classifier) — FINAL
Two-layer classifier:
1. Block must be font=code (from extraction)
2. First line must pass line_is_code(): CODE_START_RE match + not PROSE_START_RE + not PROSE_CONTAM_RE
Result: 0 suspect blocks across all 10 chapters (verified by check_fences.py).

### embed_images.py
Reads images_manifest.json, finds Figure X-Y references in MD text, inserts image markdown inline.
Ran after each conversion to re-embed (conversion overwrites MD files).

## Review Workflows

### Workflow 1 (de-patterns-review) — 31 agents, ~2.4M tokens
Phase 1: 10 Haiku review agents checked each chapter MD against raw JSON ground truth.
Phase 2: Haiku agents polished failing chapters.
Phase 3: Sonnet watchdog issued overall verdict.
Result: FAIL across most chapters due to narrative-in-fences bug.

### Workflow 2 (de-patterns-final-watchdog) — 10 agents, ~577k tokens
Haiku spot-checks + Sonnet final gate on v3 files.
Result: Still found 6 suspect blocks (all starting with "with the", "SELECT query.", etc.).
Fixed manually by iterating on PROSE_START_RE and PROSE_CONTAM_RE.

## Final State
Output: F:\Personal\Projects\Data_engineering\Data Engineering Design Patterns\
- 00_INDEX.md + 10 chapter MD files (2k-21k words each)
- 119 fenced code blocks total, all tagged python/sql/scala, 0 narrative contamination
- 69 PNG images embedded across all chapters
- check_fences.py confirms 0 suspect blocks
