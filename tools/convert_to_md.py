"""
Convert extracted chapter JSON files to structured Markdown.
Handles: headings, code blocks, pattern sections (Problem/Solution/Consequences/Examples).
"""
import json
import os
import re

EXTRACT_DIR = r"F:\Personal\Projects\Data_engineering\extract_output"
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

# Known pattern-section keywords
PATTERN_SECTIONS = re.compile(
    r'^(Problem|Solution|Consequences|Examples?|Summary|Case Study|'
    r'What Are Design Patterns\?|Common Data Engineering Patterns|'
    r'Yet More Design Patterns\?)$',
    re.IGNORECASE
)

# Detect code-like lines (Python/SQL/Scala/Java snippets)
CODE_INDICATORS = re.compile(
    r'(def |import |from |class |SELECT |INSERT |CREATE |WITH |spark\.|df\.|'
    r'\.filter\(|\.map\(|\.write\.|\.read\.|@task|@dag|pipeline|--\s|#!|'
    r'if __name__|print\(|return |val |var |fun |object )',
    re.IGNORECASE
)


def clean_line(line: str) -> str:
    line = line.replace('', '-')  # bullet
    line = line.replace('’', "'").replace('‘', "'")
    line = line.replace('“', '"').replace('”', '"')
    line = line.replace('–', '-').replace('—', '—')
    line = line.replace('�', '')
    return line


def is_heading(line: str) -> bool:
    """Heuristic: short line, mostly title-case or all-caps, not ending with period."""
    stripped = line.strip()
    if not stripped or len(stripped) > 100:
        return False
    if stripped.endswith('.') or stripped.endswith(','):
        return False
    words = stripped.split()
    if len(words) < 2 or len(words) > 12:
        return False
    # Check if it looks like a heading: starts capital, short, no sentence structure
    return stripped[0].isupper() and not stripped.endswith(':')


def is_pattern_heading(line: str) -> bool:
    """Design pattern names are usually Title Case 2-5 words."""
    stripped = line.strip()
    words = stripped.split()
    if 2 <= len(words) <= 6:
        title_words = sum(1 for w in words if w[0].isupper() and len(w) > 1)
        if title_words >= len(words) - 1:
            return True
    return False


def process_chapter(json_path: str) -> str:
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    ch_num = data['chapter']
    ch_title = CHAPTER_TITLES.get(ch_num, data['title'])
    raw_text = data['raw_text']

    lines = raw_text.split('\n')
    md_lines = []
    md_lines.append(f"# Chapter {ch_num}: {ch_title}")
    md_lines.append(f"\n> **Book:** Data Engineering Design Patterns — Bartosz Konieczny (O'Reilly, 2025)")
    md_lines.append(f"> **Pages:** {data['start_page']}–{data['end_page']} ({data['page_count']} pages)")
    md_lines.append("")

    in_code_block = False
    code_buffer = []
    prev_blank = True
    page_marker_pattern = re.compile(r'^\[Page \d+\]$')

    i = 0
    while i < len(lines):
        raw_line = lines[i]
        line = clean_line(raw_line).rstrip()

        # Skip page markers (keep as HTML comment for reference)
        if page_marker_pattern.match(line.strip()):
            if in_code_block:
                # Close code block before page break
                md_lines.append('```')
                md_lines.append('')
                md_lines.extend(code_buffer)
                code_buffer = []
                in_code_block = False
            i += 1
            continue

        # Detect code blocks
        if CODE_INDICATORS.search(line) and not in_code_block:
            # Look ahead: if next 2+ lines also look like code, open a block
            lookahead = [clean_line(lines[j]) for j in range(i, min(i + 4, len(lines)))]
            code_hits = sum(1 for l in lookahead if CODE_INDICATORS.search(l))
            if code_hits >= 2:
                if not prev_blank:
                    md_lines.append('')
                # Detect language
                lang = 'python'
                if re.search(r'\bSELECT\b|\bCREATE\b|\bINSERT\b|\bWITH\b', line, re.IGNORECASE):
                    lang = 'sql'
                elif re.search(r'\bval\b|\bobject\b|\bfun\b', line):
                    lang = 'scala'
                md_lines.append(f'```{lang}')
                in_code_block = True
                code_buffer = []

        if in_code_block:
            # End code block on blank line followed by non-code
            if not line.strip():
                # Peek: if next non-blank line is not code, close block
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                next_line = clean_line(lines[j]) if j < len(lines) else ''
                if not CODE_INDICATORS.search(next_line):
                    md_lines.append(line)
                    md_lines.append('```')
                    md_lines.append('')
                    in_code_block = False
                    code_buffer = []
                    i += 1
                    continue
            md_lines.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Pattern section keywords → H3
        if PATTERN_SECTIONS.match(stripped):
            md_lines.append('')
            md_lines.append(f'### {stripped}')
            md_lines.append('')
            prev_blank = True
            i += 1
            continue

        # Chapter heading at top of page
        if re.match(r'^Chapter\s+\d+', stripped):
            # skip redundant chapter heading repetitions (already at top)
            i += 1
            continue

        # "Figure X-X." captions
        if re.match(r'^Figure\s+\d+[-–]\d+', stripped):
            md_lines.append('')
            md_lines.append(f'> *{stripped}*')
            md_lines.append('')
            prev_blank = True
            i += 1
            continue

        # Note/Warning callouts
        if re.match(r'^(Note|Warning|Tip|Important)[:\s]', stripped, re.IGNORECASE):
            md_lines.append('')
            md_lines.append(f'> **{stripped}**')
            prev_blank = False
            i += 1
            continue

        # Footnotes — small, numbered
        if re.match(r'^\d{1,2}\s+[A-Z]', stripped) and len(stripped) < 300:
            md_lines.append(f'<!-- footnote: {stripped} -->')
            i += 1
            continue

        # Bullet points
        if re.match(r'^[•\-\*]\s+', stripped) or re.match(r'^\s*', stripped):
            clean = re.sub(r'^[•\-\*]\s*', '', stripped)
            md_lines.append(f'- {clean}')
            prev_blank = False
            i += 1
            continue

        # Numbered lists
        if re.match(r'^\d+\.\s+', stripped):
            md_lines.append(stripped)
            prev_blank = False
            i += 1
            continue

        # Section headings (heuristic for design pattern names)
        if is_heading(stripped) and not prev_blank is False:
            # Could be H2 (category) or H3 (pattern name)
            # Shorter all-caps-ish → H2, longer title-case → H3
            words = stripped.split()
            if 2 <= len(words) <= 4 and stripped.isupper():
                md_lines.append('')
                md_lines.append(f'## {stripped.title()}')
                md_lines.append('')
            elif 2 <= len(words) <= 8:
                md_lines.append('')
                md_lines.append(f'## {stripped}')
                md_lines.append('')
            else:
                md_lines.append(stripped)
            prev_blank = True
            i += 1
            continue

        # Blank line
        if not stripped:
            if not prev_blank:
                md_lines.append('')
            prev_blank = True
            i += 1
            continue

        # Regular paragraph line
        md_lines.append(stripped)
        prev_blank = False
        i += 1

    # Close any open code block
    if in_code_block:
        md_lines.append('```')

    return '\n'.join(md_lines)


def main():
    json_files = sorted([f for f in os.listdir(EXTRACT_DIR) if f.endswith('.json')])
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
        print(f"  -> {md_fname} ({word_count:,} words)")
        index_entries.append((ch_num, ch_title, md_fname, meta['start_page'], meta['end_page'], meta['page_count']))

    # Write index file
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
        "- Each file covers one chapter with all design patterns, code examples, and consequences.",
        "- Sections are structured as: **Problem → Solution → Consequences → Examples**",
        "- Code blocks are language-tagged (python / sql / scala) for syntax highlighting.",
        "- Use the chapter files as reference during project-based learning — each chapter = one concept domain.",
        "",
        "## Chapter Overview",
        "",
        "| Chapter | Focus |",
        "|---------|-------|",
        "| Ch 1 | What are design patterns? Blog analytics case study intro |",
        "| Ch 2 | Data Ingestion — batch, streaming, change data capture patterns |",
        "| Ch 3 | Error Management — dead-letter, retry, circuit-breaker patterns |",
        "| Ch 4 | Idempotency — safe retries, backfilling, deduplication |",
        "| Ch 5 | Data Value — enrichment, aggregation, joining patterns |",
        "| Ch 6 | Data Flow — orchestration, dependency, scheduling patterns |",
        "| Ch 7 | Data Security — encryption, masking, access control patterns |",
        "| Ch 8 | Data Storage — partitioning, indexing, compaction patterns |",
        "| Ch 9 | Data Quality — validation, profiling, anomaly detection |",
        "| Ch 10 | Data Observability — monitoring, alerting, lineage patterns |",
    ]

    index_path = os.path.join(OUT_DIR, "00_INDEX.md")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(index_lines))
    print(f"\nIndex written to 00_INDEX.md")
    print("Done!")


if __name__ == '__main__':
    main()
