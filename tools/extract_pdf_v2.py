"""
Re-extract PDF using PyMuPDF (fitz) — better code block preservation than pdfplumber.
Outputs per-chapter JSON with richer structure: blocks typed as 'text' or 'code'.
"""
import fitz
import json
import os
import re

PDF_PATH = r"F:\Personal\Projects\Data_engineering\Data Engineering Design Patterns.pdf"
OUT_DIR = r"F:\Personal\Projects\Data_engineering\extract_output_v2"
os.makedirs(OUT_DIR, exist_ok=True)

CHAPTER_RANGES = {
    1:  (24,  35,  "ch01_introducing_data_engineering_design_patterns"),
    2:  (36,  101, "ch02_data_ingestion_design_patterns"),
    3:  (102, 184, "ch03_error_management_design_patterns"),
    4:  (185, 258, "ch04_idempotency_design_patterns"),
    5:  (259, 358, "ch05_data_value_design_patterns"),
    6:  (359, 424, "ch06_data_flow_design_patterns"),
    7:  (425, 501, "ch07_data_security_design_patterns"),
    8:  (502, 583, "ch08_data_storage_design_patterns"),
    9:  (584, 648, "ch09_data_quality_design_patterns"),
    10: (649, 805, "ch10_data_observability_design_patterns"),
}

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

# Monospace/code fonts commonly used in O'Reilly books
CODE_FONTS = {'courier', 'courierNew', 'consolaS', 'menlo', 'monaco', 'sourcecodepro',
              'dejavusansmono', 'inconsolata', 'lucidaconsole', 'anonymous', 'firacode',
              'operator', 'droidmono', 'ubuntumono', 'notomono', 'codefont'}

def is_code_font(fontname: str) -> bool:
    fn = fontname.lower().replace(' ', '').replace('-', '')
    if 'mono' in fn or 'code' in fn or 'courier' in fn or 'consol' in fn:
        return True
    for cf in CODE_FONTS:
        if cf in fn:
            return True
    return False

def get_chapter(page_1indexed):
    for ch, (start, end, slug) in CHAPTER_RANGES.items():
        if start <= page_1indexed <= end:
            return ch, slug
    return None, None

print("Opening PDF with PyMuPDF...")
doc = fitz.open(PDF_PATH)
total = len(doc)
print(f"Total pages: {total}")

# Accumulate per-chapter structured blocks
chapter_data = {ch: {"blocks": [], "start_page": s, "end_page": e, "slug": slug, "title": CHAPTER_TITLES[ch]}
                for ch, (s, e, slug) in CHAPTER_RANGES.items()}

for page_idx in range(total):
    page_num = page_idx + 1
    ch_num, ch_slug = get_chapter(page_num)
    if ch_num is None:
        continue

    page = doc[page_idx]

    # Use dict-based extraction for font info
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

    for block in blocks:
        if block.get("type") != 0:  # 0 = text, 1 = image
            continue

        block_text_parts = []
        block_is_code = False
        block_font_sizes = []

        for line in block.get("lines", []):
            line_parts = []
            line_is_code = False
            for span in line.get("spans", []):
                font = span.get("font", "")
                size = span.get("size", 12)
                text = span.get("text", "")
                if is_code_font(font):
                    line_is_code = True
                    block_is_code = True
                line_parts.append(text)
                block_font_sizes.append(size)
            line_text = "".join(line_parts)
            if line_text.strip():
                block_text_parts.append(("code" if line_is_code else "text", line_text))

        if not block_text_parts:
            continue

        # Determine dominant font size for heading detection
        avg_size = sum(block_font_sizes) / len(block_font_sizes) if block_font_sizes else 12

        full_text = "\n".join(t for _, t in block_text_parts)
        if not full_text.strip():
            continue

        chapter_data[ch_num]["blocks"].append({
            "page": page_num,
            "type": "code" if block_is_code else "text",
            "avg_font_size": round(avg_size, 1),
            "text": full_text,
            "lines": block_text_parts,
        })

    if page_num % 100 == 0:
        print(f"  Page {page_num}/{total}")

doc.close()

# Save per-chapter JSON
for ch_num, data in chapter_data.items():
    slug = data["slug"]
    out = {
        "chapter": ch_num,
        "title": data["title"],
        "slug": slug,
        "start_page": data["start_page"],
        "end_page": data["end_page"],
        "page_count": data["end_page"] - data["start_page"] + 1,
        "blocks": data["blocks"],
    }
    path = os.path.join(OUT_DIR, f"{slug}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    code_blocks = sum(1 for b in data["blocks"] if b["type"] == "code")
    print(f"  Ch{ch_num}: {len(data['blocks'])} blocks ({code_blocks} code blocks) -> {slug}.json")

print("\nExtraction v2 complete.")
