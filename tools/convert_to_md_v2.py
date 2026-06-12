"""
Convert font-aware chapter JSON (v2) to clean Markdown.
Key rules:
- ONLY blocks typed 'code' get fenced code blocks — never narrative text
- Section headers (Problem/Solution/Consequences/Examples) → ### heading
- Pattern names detected by heading font size and title-case heuristic → ## heading
- Chapter overview sections (categories) → ## heading
- All code blocks get language tag based on content keywords
"""
import json
import os
import re

EXTRACT_DIR = r"F:\Personal\Projects\Data_engineering\extract_output_v2"
OUT_DIR = r"F:\Personal\Projects\Data_engineering\Data Engineering Design Patterns"
os.makedirs(OUT_DIR, exist_ok=True)

CHAPTER_TITLES = {
    1: "Introducing Data Engineering Design Patterns",
    2: "Data Ingestion Design Patterns",
    3: "Error Management Design Patterns",
    4: "Idempotency Design Patterns",
    5: "Data Value Design Patterns",
    6: "Data Flow Design Patterns",
    7: "Data Security Design Patterns",
    8: "Data Storage Design Patterns",
    9: "Data Quality Design Patterns",
    10: "Data Observability Design Patterns",
}

# Exact section keywords → always ### heading
PATTERN_SECTIONS = {
    'problem', 'solution', 'consequences', 'examples', 'example',
    'summary', 'case study', 'what are design patterns?',
    'common data engineering patterns', 'yet more design patterns?',
    'how to use this book', 'the structure of this book',
}

def clean(text: str) -> str:
    text = text.replace('’', "'").replace('‘', "'")
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('–', '-').replace('—', '—')
    text = text.replace('�', '')
    text = text.replace('•', '-')
    return text

def detect_lang(code: str) -> str:
    code_l = code.lower()
    if re.search(r'\bselect\b|\bcreate\b|\binsert\b|\bwith\b.*\bselect\b|\bdrop\b|\bfrom\b.*\bwhere\b', code_l):
        if not re.search(r'\bdef \b|\bimport \b|\bval \b', code_l):
            return 'sql'
    if re.search(r'\bval \b|\bobject \b|\bcase class\b|\bdef \b.*:\s*[A-Z]', code):
        return 'scala'
    return 'python'

def is_pattern_section_header(text: str) -> bool:
    stripped = text.strip().rstrip('.')
    return stripped.lower() in PATTERN_SECTIONS

def is_heading_candidate(text: str, avg_size: float) -> tuple:
    """Returns (level, text) or (0, text) if not a heading."""
    stripped = text.strip()
    if not stripped or len(stripped) > 120:
        return 0, stripped
    if stripped.endswith(',') or stripped.endswith(';'):
        return 0, stripped

    words = stripped.split()
    word_count = len(words)

    # Font size based: larger fonts are headings
    if avg_size >= 14:
        return 2, stripped
    if avg_size >= 12.5 and word_count <= 10:
        # Title-case check
        title_words = sum(1 for w in words if w and w[0].isupper())
        if title_words >= max(1, word_count - 2):
            return 3, stripped

    return 0, stripped

def looks_like_chapter_intro(text: str) -> bool:
    return bool(re.match(r'^Chapter\s+\d+[.\s]', text.strip()))

def process_chapter(json_path: str) -> str:
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    ch_num = data['chapter']
    ch_title = CHAPTER_TITLES.get(ch_num, data['title'])
    blocks = data['blocks']

    lines = []
    lines.append(f"# Chapter {ch_num}: {ch_title}")
    lines.append("")
    lines.append(f"> **Book:** Data Engineering Design Patterns — Bartosz Konieczny (O'Reilly, 2025)")
    lines.append(f"> **Pages:** {data['start_page']}–{data['end_page']} ({data['page_count']} pages)")
    lines.append("")

    prev_page = None
    i = 0
    while i < len(blocks):
        block = blocks[i]
        btype = block['type']
        text = clean(block['text']).strip()
        avg_size = block.get('avg_font_size', 12.0)
        page = block.get('page', 0)

        if not text:
            i += 1
            continue

        # Page transition comment (lightweight)
        if page != prev_page:
            prev_page = page

        # Skip repeated chapter title lines
        if looks_like_chapter_intro(text) and i < 5:
            i += 1
            continue

        # Code block
        if btype == 'code':
            # Accumulate consecutive code blocks into one fenced block
            code_lines = [text]
            j = i + 1
            while j < len(blocks) and blocks[j]['type'] == 'code':
                next_text = clean(blocks[j]['text']).strip()
                if next_text:
                    code_lines.append(next_text)
                j += 1

            full_code = "\n".join(code_lines)
            lang = detect_lang(full_code)
            lines.append("")
            lines.append(f"```{lang}")
            lines.append(full_code)
            lines.append("```")
            lines.append("")
            i = j
            continue

        # Pattern section header (Problem / Solution / etc.)
        if is_pattern_section_header(text):
            lines.append("")
            lines.append(f"### {text}")
            lines.append("")
            i += 1
            continue

        # Figure caption
        if re.match(r'^Figure\s+\d+[-–]\d+', text):
            lines.append("")
            lines.append(f"> *{text}*")
            lines.append("")
            i += 1
            continue

        # Example label (e.g., "Example 3-2. Title")
        if re.match(r'^Example\s+\d+[-–]\d+', text):
            lines.append("")
            lines.append(f"**{text}**")
            lines.append("")
            i += 1
            continue

        # Note / Warning callouts
        if re.match(r'^(NOTE|WARNING|TIP|IMPORTANT)\b', text, re.IGNORECASE):
            lines.append("")
            lines.append(f"> **{text}**")
            lines.append("")
            i += 1
            continue

        # Footnote (small numbered text)
        if re.match(r'^\d{1,2}\s+[A-Z]', text) and len(text) < 300 and avg_size < 10:
            lines.append(f"<!-- footnote: {text} -->")
            i += 1
            continue

        # Heading detection
        level, heading_text = is_heading_candidate(text, avg_size)
        if level == 2:
            lines.append("")
            lines.append(f"## {heading_text}")
            lines.append("")
            i += 1
            continue
        if level == 3:
            lines.append("")
            lines.append(f"### {heading_text}")
            lines.append("")
            i += 1
            continue

        # Bullet points
        if re.match(r'^[•\-\*]\s+', text):
            bullet_text = re.sub(r'^[•\-\*]\s*', '', text)
            lines.append(f"- {bullet_text}")
            i += 1
            continue

        # Numbered list
        if re.match(r'^\d+\.\s+', text):
            lines.append(text)
            i += 1
            continue

        # Regular paragraph
        lines.append(text)
        lines.append("")
        i += 1

    return "\n".join(lines)


def main():
    json_files = sorted(f for f in os.listdir(EXTRACT_DIR) if f.endswith('.json'))
    index_entries = []

    for fname in json_files:
        json_path = os.path.join(EXTRACT_DIR, fname)
        print(f"Converting {fname}...")
        md_content = process_chapter(json_path)

        with open(json_path, encoding='utf-8') as f:
            meta = json.load(f)

        ch_num = meta['chapter']
        ch_title = CHAPTER_TITLES.get(ch_num, meta['title'])
        md_fname = f"ch{ch_num:02d}_{re.sub(r'[^a-z0-9]+', '_', ch_title.lower()).strip('_')}.md"
        md_path = os.path.join(OUT_DIR, md_fname)

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        word_count = len(md_content.split())
        code_blocks = md_content.count('```python') + md_content.count('```sql') + md_content.count('```scala')
        print(f"  -> {md_fname} ({word_count:,} words, {code_blocks} code blocks)")
        index_entries.append((ch_num, ch_title, md_fname, meta['start_page'], meta['end_page'], meta['page_count']))

    # Regenerate index
    index_lines = [
        "# Data Engineering Design Patterns — Chapter Index",
        "",
        "> Bartosz Konieczny (O'Reilly, 2025) · 805 pages · 10 chapters",
        "",
        "## Chapters",
        "",
        "| # | Chapter | Pages | File |",
        "|---|---------|-------|------|",
    ]
    for ch_num, title, fname, sp, ep, pc in index_entries:
        index_lines.append(f"| {ch_num} | {title} | {sp}–{ep} ({pc} pp) | [{fname}]({fname}) |")

    index_lines += [
        "",
        "## How to Use These Files",
        "",
        "- Each file = one chapter, containing all design patterns with Problem → Solution → Consequences → Examples.",
        "- Code blocks are language-tagged (`python` / `sql` / `scala`) for syntax highlighting.",
        "- Images are embedded inline at their Figure reference points.",
        "- Use as a concept-by-concept reference during project-based learning.",
        "",
        "## Chapter Overview",
        "",
        "| Chapter | Patterns Covered |",
        "|---------|-----------------|",
        "| Ch 1 | What are design patterns? Medallion architecture, case study intro |",
        "| Ch 2 | Full Loader, Incremental Loader, CDC, Passthrough Replicator, Transformation Replicator, Compactor, Readiness Marker, External Trigger |",
        "| Ch 3 | Dead-Letter, Retry, Circuit Breaker, Deduplicator, Dynamic Late Data Integrator, Checkpointer |",
        "| Ch 4 | Fast Metadata Cleaner, Data Overwrite, Merger, Stateful Merger, Keyed Idempotency, Transactional Writer, Proxy |",
        "| Ch 5 | Static Joiner, Dynamic Joiner, Wrapper, Metadata Decorator, Distributed Aggregator, Local Aggregator, Sessionizer patterns, Orderer patterns |",
        "| Ch 6 | Pipeline orchestration, dependency management, scheduling, data flow patterns |",
        "| Ch 7 | Encryption, masking, access control, data anonymization, GDPR patterns |",
        "| Ch 8 | Partitioning, indexing, compaction, tiered storage, caching patterns |",
        "| Ch 9 | Schema validation, data profiling, anomaly detection, data contracts |",
        "| Ch 10 | Metrics, alerting, lineage tracking, SLA monitoring, observability patterns |",
    ]

    with open(os.path.join(OUT_DIR, "00_INDEX.md"), 'w', encoding='utf-8') as f:
        f.write('\n'.join(index_lines))

    print("\nDone! Index written.")


if __name__ == '__main__':
    main()
