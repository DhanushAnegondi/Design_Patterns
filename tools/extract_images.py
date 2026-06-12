"""
Extract all figures/diagrams from Data Engineering Design Patterns PDF.
- Saves each image to Data Engineering Design Patterns/images/<chapter>/fig_<page>_<idx>.png
- Generates a manifest: images_manifest.json mapping each image to its page, chapter, and caption
"""
import fitz  # PyMuPDF
import json
import os
import re
from pathlib import Path

PDF_PATH = r"F:\Personal\Projects\Data_engineering\Data Engineering Design Patterns.pdf"
OUT_BASE = r"F:\Personal\Projects\Data_engineering\Data Engineering Design Patterns"
EXTRACT_DIR = r"F:\Personal\Projects\Data_engineering\extract_output"
IMAGES_DIR = os.path.join(OUT_BASE, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# Chapter page ranges (from extraction)
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

def get_chapter(page_num):
    for ch, (start, end, slug) in CHAPTER_RANGES.items():
        if start <= page_num <= end:
            return ch, slug
    return None, None


def extract_captions(page_text, page_num):
    """Extract figure captions like 'Figure 3-2. Caption text'"""
    captions = {}
    pattern = re.compile(r'Figure\s+(\d+[-–]\d+)[.\s]+(.+?)(?=Figure|\Z)', re.DOTALL)
    for m in pattern.finditer(page_text):
        fig_id = m.group(1).replace('–', '-')
        caption = ' '.join(m.group(2).split())[:200]
        captions[fig_id] = caption
    return captions


print("Opening PDF with PyMuPDF...")
doc = fitz.open(PDF_PATH)
total_pages = len(doc)
print(f"Total pages: {total_pages}")

manifest = []
skipped = 0
saved = 0

for page_num in range(total_pages):
    page = doc[page_num]
    pdf_page = page_num + 1  # 1-indexed

    ch_num, ch_slug = get_chapter(pdf_page)
    if ch_num is None:
        continue

    # Extract text for caption detection
    page_text = page.get_text()
    captions = extract_captions(page_text, pdf_page)

    # Get all images on this page
    image_list = page.get_images(full=True)
    if not image_list:
        continue

    # Create chapter images subfolder
    ch_img_dir = os.path.join(IMAGES_DIR, f"ch{ch_num:02d}")
    os.makedirs(ch_img_dir, exist_ok=True)

    for img_idx, img_info in enumerate(image_list):
        xref = img_info[0]
        width = img_info[2]
        height = img_info[3]

        # Skip tiny images (icons, bullets, decorative elements < 80x80px)
        if width < 80 or height < 80:
            skipped += 1
            continue

        # Skip very wide but short images (likely horizontal rules/dividers)
        if height < 30:
            skipped += 1
            continue

        try:
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]  # png, jpeg, etc.

            # Convert to PNG for consistency
            img_filename = f"fig_p{pdf_page:03d}_{img_idx:02d}.png"
            img_path = os.path.join(ch_img_dir, img_filename)
            rel_path = f"images/ch{ch_num:02d}/{img_filename}"

            # Save image
            if image_ext == "png":
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
            else:
                # Convert to PNG using Pillow
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(image_bytes))
                img.save(img_path, "PNG")

            # Try to find matching figure caption from nearby text
            # Look for "Figure X-Y" references in this page
            fig_refs = re.findall(r'Figure\s+(\d+[-–]\d+)', page_text)
            caption = ""
            if fig_refs:
                # Use the first figure reference on this page as candidate
                fig_id = fig_refs[0].replace('–', '-')
                caption = captions.get(fig_id, f"Figure on page {pdf_page}")
                # Try to match by chapter number
                if not caption:
                    for fid, fcap in captions.items():
                        if fid.startswith(str(ch_num) + '-'):
                            caption = fcap
                            break

            entry = {
                "chapter": ch_num,
                "chapter_title": CHAPTER_TITLES[ch_num],
                "chapter_slug": ch_slug,
                "page": pdf_page,
                "img_index": img_idx,
                "width": width,
                "height": height,
                "filename": img_filename,
                "rel_path": rel_path,
                "abs_path": img_path,
                "caption": caption or f"Figure on page {pdf_page}",
                "figure_refs": fig_refs,
            }
            manifest.append(entry)
            saved += 1

        except Exception as e:
            print(f"  Warning: could not extract image xref={xref} on page {pdf_page}: {e}")
            skipped += 1

    if pdf_page % 100 == 0:
        print(f"  Processed page {pdf_page}/{total_pages} — {saved} images saved so far")

doc.close()

# Save manifest
manifest_path = os.path.join(OUT_BASE, "images_manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"\nExtraction complete!")
print(f"  Images saved: {saved}")
print(f"  Images skipped (too small): {skipped}")
print(f"  Manifest: {manifest_path}")

# Print per-chapter summary
from collections import defaultdict
by_chapter = defaultdict(list)
for entry in manifest:
    by_chapter[entry["chapter"]].append(entry)

print("\nPer-chapter image count:")
for ch in sorted(by_chapter.keys()):
    imgs = by_chapter[ch]
    print(f"  Ch{ch}: {len(imgs)} images ({imgs[0]['chapter_title']})")
