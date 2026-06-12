"""
v3: Strict code-block classifier.
Font=monospace is necessary but NOT sufficient for a fenced block.
A block is ACTUAL CODE only if it passes content tests:
  - Has genuine code syntax (assignments, function calls, SQL clauses, imports, etc.)
  - Does NOT read like an English sentence (no articles/connectors at the start)
  - OR is multi-line with code-like structure
Single-line monospace prose mentions become inline `backtick` spans, not fenced blocks.
"""
import json
import os
import re

EXTRACT_DIR = r"F:\Personal\Projects\Data_engineering\extract_output_v2"
OUT_DIR     = r"F:\Personal\Projects\Data_engineering\Data Engineering Design Patterns"
os.makedirs(OUT_DIR, exist_ok=True)

CHAPTER_TITLES = {
    1:  "Introducing Data Engineering Design Patterns",
    2:  "Data Ingestion Design Patterns",
    3:  "Error Management Design Patterns",
    4:  "Idempotency Design Patterns",
    5:  "Data Value Design Patterns",
    6:  "Data Flow Design Patterns",
    7:  "Data Security Design Patterns",
    8:  "Data Storage Design Patterns",
    9:  "Data Quality Design Patterns",
    10: "Data Observability Design Patterns",
}

PATTERN_SECTIONS = {
    'problem', 'solution', 'consequences', 'examples', 'example', 'summary',
    'case study', 'what are design patterns?', 'common data engineering patterns',
    'yet more design patterns?', 'how to use this book', 'the structure of this book',
}

# Patterns that unambiguously signal REAL code
CODE_START_RE = re.compile(
    r'^('
    r'(def |class |import |from\s+\S+\s+import|@\w+|async def )|'       # Python
    r'(SELECT\b|INSERT\b|CREATE\b|DROP\b|ALTER\b|WITH\b|UPDATE\b|DELETE FROM\b|MERGE\b|TRUNCATE TABLE\b(?=\s*\n))|'  # SQL statement starts
    r'(val |var |object |case class |trait )|'                           # Scala
    r'(public |private |void |int |String |List<)|'                      # Java
    r'(\$\s*\w|aws |gcloud |bq |docker |kubectl )|'                      # CLI
    r'(#!\/|---\n|apiVersion:)|'                                         # YAML/bash
    r'(\w+\s*=\s*.+\()|'                                                 # assignment with function call
    r'(\w+\.\w+\()|'                                                     # method call
    r'(for\s+\w+\s+in\s+|if\s+\w+.*:$|while\s+\w+|return\s+\w+)'       # control flow
    r')', re.IGNORECASE | re.MULTILINE
)

# Patterns that signal this is ENGLISH PROSE (not code)
PROSE_START_RE = re.compile(
    r'^(The |A |An |In |It |This |That |These |Those |You |We |They |'
    r'For |When |If |Since |Because |However |Moreover |Therefore |'
    r'First|Second|Third|Finally|Next|Then|Also|Note |Warning |'
    r'Overall|Although|Even|While|After|Before|During|'
    r'As a |As an |As the |With the |With a |With an )',
    re.IGNORECASE
)

# English sentence indicators anywhere in short text
SENTENCE_RE = re.compile(r'\b(the|a|an|is|are|was|were|will|can|could|should|would|has|have|had|'
                          r'not|but|and|or|its|their|your|our|this|that|which|with|from|into|onto)\b',
                          re.IGNORECASE)

# Prose contamination — if ANY of these appear after a SQL keyword opener, it's narrative
PROSE_CONTAM_RE = re.compile(
    r"\b(doesn't|don't|isn't|aren't|won't|can't|couldn't|wouldn't|shouldn't|"
    r"doesn|support|creates?|outcome|operation\.|approach|result|means?|allows?|"
    r"provides?|requires?|ensures?|generates?|produces?|executes?|performs?|"
    r"handles?|manages?|enables?|defines?|query\.|shows?\s+this|in\s+action|"
    r"commands?\s+like|keep\s+in\s+mind)\b",
    re.IGNORECASE
)

def line_is_code(line: str) -> bool:
    """True if this single line is unambiguously code syntax."""
    s = line.strip()
    if not s:
        return False
    # Prose opener → definitely not code
    if PROSE_START_RE.match(s):
        return False
    # Must match a real code pattern
    if not CODE_START_RE.match(s):
        return False
    # Reject if prose contamination follows a SQL keyword
    if PROSE_CONTAM_RE.search(s):
        return False
    # Extra guard: if >40% of tokens are common English words, it's prose
    words = s.split()
    if len(words) >= 5:
        eng = sum(1 for w in words if SENTENCE_RE.match(w))
        if eng / len(words) > 0.40:
            return False
    return True

def is_real_code_block(text: str) -> bool:
    """
    Returns True only if the block is genuine code.
    Key rule: the FIRST non-empty line must itself be real code.
    Then >= 50% of lines must be code-like.
    Single lines follow the same first-line rule.
    """
    lines = [l for l in text.strip().split('\n') if l.strip()]
    if not lines:
        return False

    first_line = lines[0].strip()

    # First line MUST be real code — no exceptions
    if not line_is_code(first_line):
        return False

    if len(lines) == 1:
        return True

    # Multi-line: count code vs prose lines (skip first, already cleared)
    code_count = 1  # first line passed
    prose_count = 0
    for line in lines[1:]:
        s = line.strip()
        if not s:
            continue
        if PROSE_START_RE.match(s):
            prose_count += 1
        elif CODE_START_RE.match(s):
            code_count += 1
        elif re.search(r'^\s*(#|//|--\s)', s):  # comment lines
            code_count += 1
        elif re.search(r'[=(){}\[\]]', s) and not SENTENCE_RE.search(s[:20]):
            code_count += 1
        elif SENTENCE_RE.search(s) and len(s.split()) > 4:
            prose_count += 1

    # Reject if prose dominates
    total = code_count + prose_count
    if total > 0 and prose_count / total > 0.5:
        return False

    return True

def detect_lang(code: str) -> str:
    c = code.lower()
    if re.search(r'^(select|insert|create|drop|alter|with\s+\w|update|delete|merge|truncate)\b', c, re.MULTILINE):
        if not re.search(r'\bdef \b|\bimport \b|\bval \b|class ', c):
            return 'sql'
    if re.search(r'\bval \b|\bobject \b|\bcase class\b', code):
        return 'scala'
    return 'python'

def clean(t: str) -> str:
    return (t.replace('‘', "'").replace('’', "'")
             .replace('“', '"').replace('”', '"')
             .replace('–', '-').replace('—', '—')
             .replace('�', '').replace('•', '-'))

def is_pattern_section(text: str) -> bool:
    return text.strip().rstrip('.').lower() in PATTERN_SECTIONS

def heading_level(text: str, size: float) -> int:
    s = text.strip()
    if not s or len(s) > 120 or s.endswith(',') or s.endswith(';'):
        return 0
    words = s.split()
    if size >= 14:
        return 2
    if size >= 12.5 and len(words) <= 10:
        caps = sum(1 for w in words if w and w[0].isupper())
        if caps >= max(1, len(words) - 2):
            return 3
    return 0

def process_chapter(json_path: str) -> str:
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    ch_num    = data['chapter']
    ch_title  = CHAPTER_TITLES.get(ch_num, data['title'])
    blocks    = data['blocks']

    out = []
    out.append(f"# Chapter {ch_num}: {ch_title}")
    out.append("")
    out.append(f"> **Book:** Data Engineering Design Patterns — Bartosz Konieczny (O'Reilly, 2025)")
    out.append(f"> **Pages:** {data['start_page']}–{data['end_page']} ({data['page_count']} pages)")
    out.append("")

    i = 0
    while i < len(blocks):
        block  = blocks[i]
        btype  = block['type']
        raw    = clean(block['text']).strip()
        size   = block.get('avg_font_size', 12.0)

        if not raw:
            i += 1
            continue

        # Skip repeated chapter heading at top
        if re.match(r'^Chapter\s+\d+[.\s]', raw) and i < 5:
            i += 1
            continue

        # ── CODE BLOCK ───────────────────────────────────────────────────────
        if btype == 'code':
            # Accumulate consecutive code-font blocks
            code_parts = [raw]
            j = i + 1
            while j < len(blocks) and blocks[j]['type'] == 'code':
                nxt = clean(blocks[j]['text']).strip()
                if nxt:
                    code_parts.append(nxt)
                j += 1
            full_code = "\n".join(code_parts)

            if is_real_code_block(full_code):
                lang = detect_lang(full_code)
                out.append("")
                out.append(f"```{lang}")
                out.append(full_code)
                out.append("```")
                out.append("")
            else:
                # Inline prose mentioning code — render as plain paragraph with backtick wrapping for short terms
                prose = full_code.replace('\n', ' ').strip()
                # Wrap any CamelCase identifiers or UPPER_CASE SQL terms in backticks
                prose = re.sub(r'\b([A-Z_]{3,})\b', r'`\1`', prose)  # SQL keywords
                prose = re.sub(r'\b([a-z]+\.[a-z_]+\()', r'`\1`', prose)  # method.calls()
                out.append(prose)
                out.append("")
            i = j
            continue

        # ── PATTERN SECTION (Problem / Solution / etc.) ───────────────────
        if is_pattern_section(raw):
            out.append("")
            out.append(f"### {raw}")
            out.append("")
            i += 1
            continue

        # ── FIGURE CAPTION ────────────────────────────────────────────────
        if re.match(r'^Figure\s+\d+[-–]\d+', raw):
            out.append("")
            out.append(f"> *{raw}*")
            out.append("")
            i += 1
            continue

        # ── EXAMPLE LABEL ────────────────────────────────────────────────
        if re.match(r'^Example\s+\d+[-–]\d+', raw):
            out.append("")
            out.append(f"**{raw}**")
            out.append("")
            i += 1
            continue

        # ── CALLOUT (Note / Warning / Tip) ───────────────────────────────
        if re.match(r'^(NOTE|WARNING|TIP|IMPORTANT)\b', raw, re.IGNORECASE):
            out.append("")
            out.append(f"> **{raw}**")
            out.append("")
            i += 1
            continue

        # ── FOOTNOTE ─────────────────────────────────────────────────────
        if re.match(r'^\d{1,2}\s+[A-Z]', raw) and len(raw) < 300 and size < 10:
            out.append(f"<!-- footnote: {raw} -->")
            i += 1
            continue

        # ── HEADING ──────────────────────────────────────────────────────
        lvl = heading_level(raw, size)
        if lvl == 2:
            out.append("")
            out.append(f"## {raw}")
            out.append("")
            i += 1
            continue
        if lvl == 3:
            out.append("")
            out.append(f"### {raw}")
            out.append("")
            i += 1
            continue

        # ── BULLET ───────────────────────────────────────────────────────
        if re.match(r'^[-•\*]\s+', raw):
            bullet_text = re.sub(r'^[-•\*]\s*', '', raw)
            out.append(f"- {bullet_text}")
            i += 1
            continue

        # ── NUMBERED LIST ────────────────────────────────────────────────
        if re.match(r'^\d+\.\s+', raw):
            out.append(raw)
            i += 1
            continue

        # ── PARAGRAPH ────────────────────────────────────────────────────
        out.append(raw)
        out.append("")
        i += 1

    return "\n".join(out)


def main():
    files = sorted(f for f in os.listdir(EXTRACT_DIR) if f.endswith('.json'))
    index = []

    for fname in files:
        path = os.path.join(EXTRACT_DIR, fname)
        print(f"Converting {fname}...")
        md = process_chapter(path)

        with open(path, encoding='utf-8') as f:
            meta = json.load(f)

        ch_num = meta['chapter']
        title  = CHAPTER_TITLES.get(ch_num, meta['title'])
        slug   = f"ch{ch_num:02d}_{re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')}"
        md_path = os.path.join(OUT_DIR, f"{slug}.md")

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md)

        words  = len(md.split())
        fenced = len(re.findall(r'^```(python|sql|scala)', md, re.MULTILINE))
        unfenced_code = len(re.findall(r'^```$', md, re.MULTILINE))  # untagged fences remaining
        print(f"  {slug}.md | {words:,} words | {fenced} tagged fences | {unfenced_code} untagged")
        index.append((ch_num, title, f"{slug}.md", meta['start_page'], meta['end_page'], meta['page_count']))

    # Write index
    idx = [
        "# Data Engineering Design Patterns — Chapter Index",
        "",
        "> Bartosz Konieczny (O’Reilly, 2025) · 805 pages · 10 chapters",
        "",
        "| # | Chapter | Pages | File |",
        "|---|---------|-------|------|",
    ]
    for n, t, f, sp, ep, pc in index:
        idx.append(f"| {n} | {t} | {sp}–{ep} ({pc} pp) | [{f}]({f}) |")
    idx += [
        "",
        "## Pattern Quick-Reference",
        "",
        "| Chapter | Patterns |",
        "|---------|---------|",
        "| Ch 2 — Ingestion | Full Loader, Incremental Loader, CDC, Passthrough Replicator, Transformation Replicator, Compactor, Readiness Marker, External Trigger |",
        "| Ch 3 — Error Mgmt | Dead-Letter, Retry, Circuit Breaker, Windowed Deduplicator, Dynamic Late Data Integrator, Checkpointer |",
        "| Ch 4 — Idempotency | Fast Metadata Cleaner, Data Overwrite, Merger, Stateful Merger, Keyed Idempotency, Transactional Writer, Proxy |",
        "| Ch 5 — Data Value | Static/Dynamic Joiner, Wrapper, Metadata Decorator, Distributed/Local Aggregator, Sessionizer, Orderer patterns |",
        "| Ch 6 — Data Flow | Orchestration, pipeline dependency, scheduling patterns |",
        "| Ch 7 — Security | Encryption, masking, access control, anonymization |",
        "| Ch 8 — Storage | Partitioning, indexing, compaction, caching |",
        "| Ch 9 — Quality | Schema validation, data profiling, anomaly detection, contracts |",
        "| Ch 10 — Observability | Metrics, alerting, lineage, SLA monitoring |",
    ]
    with open(os.path.join(OUT_DIR, "00_INDEX.md"), 'w', encoding='utf-8') as f:
        f.write('\n'.join(idx))

    print("\nv3 conversion done.")

if __name__ == '__main__':
    main()
