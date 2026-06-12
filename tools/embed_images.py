"""
Embed extracted images into chapter MD files at the right positions.
Strategy: find "Figure X-Y" references in MD text, insert image markdown after each reference.
For images without a clear text anchor, append them in a ## Figures section at end of chapter.
"""
import json
import os
import re
from collections import defaultdict

OUT_DIR = r"F:\Personal\Projects\Data_engineering\Data Engineering Design Patterns"
MANIFEST_PATH = os.path.join(OUT_DIR, "images_manifest.json")

with open(MANIFEST_PATH, encoding="utf-8") as f:
    manifest = json.load(f)

# Group images by chapter
by_chapter = defaultdict(list)
for entry in manifest:
    by_chapter[entry["chapter"]].append(entry)

# Chapter slug map
CHAPTER_SLUGS = {
    1:  "ch01_introducing_data_engineering_design_patterns",
    2:  "ch02_data_ingestion_design_patterns",
    3:  "ch03_error_management_design_patterns",
    4:  "ch04_idempotency_design_patterns",
    5:  "ch05_data_value_design_patterns",
    6:  "ch06_data_flow_design_patterns",
    7:  "ch07_data_security_design_patterns",
    8:  "ch08_data_storage_design_patterns",
    9:  "ch09_data_quality_design_patterns",
    10: "ch10_data_observability_design_patterns",
}

# Figure reference pattern in markdown text
FIG_REF_RE = re.compile(r'Figure\s+(\d+)[-–](\d+)', re.IGNORECASE)

def make_img_md(entry):
    rel_path = entry["rel_path"].replace("\\", "/")
    caption = entry["caption"]
    page = entry["page"]
    return f'\n![{caption}]({rel_path})\n*Figure — page {page}: {caption}*\n'

for ch_num, images in sorted(by_chapter.items()):
    slug = CHAPTER_SLUGS.get(ch_num)
    if not slug:
        continue

    md_path = os.path.join(OUT_DIR, f"{slug}.md")
    if not os.path.exists(md_path):
        print(f"  WARNING: {md_path} not found, skipping")
        continue

    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    embedded = set()

    # Try to anchor each image by its figure reference in text
    for img in images:
        fig_refs = img.get("figure_refs", [])
        placed = False
        for fig_ref in fig_refs:
            # Build pattern for this figure ref (e.g. "Figure 3-2" or "Figure 3–2")
            parts = re.split(r'[-–]', fig_ref)
            if len(parts) == 2:
                pat = re.compile(
                    r'(Figure\s+' + re.escape(parts[0]) + r'[-–]' + re.escape(parts[1]) + r'[^a-zA-Z0-9])',
                    re.IGNORECASE
                )
                match = pat.search(content)
                if match:
                    insert_pos = match.end()
                    img_md = make_img_md(img)
                    content = content[:insert_pos] + img_md + content[insert_pos:]
                    embedded.add(img["filename"])
                    placed = True
                    break

    # Images not anchored to a figure reference → append in a Figures section
    unplaced = [img for img in images if img["filename"] not in embedded]
    if unplaced:
        figures_section = "\n\n---\n\n## Chapter Figures\n\n"
        for img in unplaced:
            figures_section += make_img_md(img) + "\n"
        content += figures_section

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Ch{ch_num}: embedded {len(images) - len(unplaced)} anchored + {len(unplaced)} appended = {len(images)} total images")

print("\nAll images embedded.")
