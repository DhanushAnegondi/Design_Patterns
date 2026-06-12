"""
Extract Data Engineering Design Patterns PDF into per-chapter JSON chunks.
Outputs: extract_output/<chapter_slug>.json with {chapter, patterns, pages, raw_text}
"""
import pdfplumber
import json
import re
import os

PDF_PATH = r"F:\Personal\Projects\Data_engineering\Data Engineering Design Patterns.pdf"
OUT_DIR = r"F:\Personal\Projects\Data_engineering\extract_output"
os.makedirs(OUT_DIR, exist_ok=True)

CHAPTER_PATTERN = re.compile(
    r'^Chapter\s+(\d+)[.\s]+(.+)$', re.IGNORECASE | re.MULTILINE
)

SECTION_PATTERN = re.compile(
    r'^(#{1,3}\s+.+|[A-Z][A-Za-z\s\-:]{10,80})$', re.MULTILINE
)

print("Opening PDF...")
with pdfplumber.open(PDF_PATH) as pdf:
    total = len(pdf.pages)
    print(f"Total pages: {total}")

    # First pass: extract all text with page numbers
    all_pages = []
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        all_pages.append({"page": i + 1, "text": text})
        if (i + 1) % 50 == 0:
            print(f"  Extracted page {i+1}/{total}")

print("Identifying chapter boundaries...")

# Find chapter start pages
chapter_boundaries = []
for pg in all_pages:
    lines = pg["text"].split("\n")
    for line in lines[:5]:  # chapters usually start near top of page
        m = CHAPTER_PATTERN.match(line.strip())
        if m:
            ch_num = int(m.group(1))
            ch_title = m.group(2).strip()
            chapter_boundaries.append({
                "chapter": ch_num,
                "title": ch_title,
                "start_page": pg["page"]
            })
            break

# Deduplicate (same chapter may appear in TOC + body)
seen = {}
for cb in chapter_boundaries:
    k = cb["chapter"]
    if k not in seen:
        seen[k] = cb
    else:
        # Keep the higher page number (actual chapter, not TOC reference)
        if cb["start_page"] > seen[k]["start_page"]:
            seen[k] = cb

chapter_boundaries = sorted(seen.values(), key=lambda x: x["start_page"])
print(f"Found {len(chapter_boundaries)} chapters:")
for cb in chapter_boundaries:
    print(f"  Ch{cb['chapter']}: {cb['title']} — starts p.{cb['start_page']}")

# Second pass: assign pages to chapters
for i, cb in enumerate(chapter_boundaries):
    start = cb["start_page"]
    end = chapter_boundaries[i + 1]["start_page"] - 1 if i + 1 < len(chapter_boundaries) else total

    raw_pages = [p for p in all_pages if start <= p["page"] <= end]
    raw_text = "\n\n".join(
        f"[Page {p['page']}]\n{p['text']}" for p in raw_pages
    )

    slug = f"ch{cb['chapter']:02d}_{re.sub(r'[^a-z0-9]+', '_', cb['title'].lower()).strip('_')}"
    out = {
        "chapter": cb["chapter"],
        "title": cb["title"],
        "start_page": start,
        "end_page": end,
        "page_count": end - start + 1,
        "slug": slug,
        "raw_text": raw_text
    }

    path = os.path.join(OUT_DIR, f"{slug}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  Saved {slug}.json ({out['page_count']} pages)")

print("\nExtraction complete.")
