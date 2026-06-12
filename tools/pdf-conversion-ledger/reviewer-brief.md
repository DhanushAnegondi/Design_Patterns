# Reviewer Brief — Data Engineering Design Patterns

## What this project is
Converting the O'Reilly book "Data Engineering Design Patterns" (Bartosz Konieczny, 2025, 805 pages)
into structured per-chapter Markdown files for concept-by-concept project-based learning.

## What "good" means here
- Every design pattern in the book surfaces as a heading in its chapter MD file
- Each pattern has Problem / Solution / Consequences / Examples sections (### level)
- Code blocks are ONLY real code — never narrative prose that mentions code terms
- All code blocks have language tags: python / sql / scala
- All 69 figures are embedded as images at their Figure reference points
- MD files open and render correctly in Obsidian / VS Code / Typora
- No hallucinated content — every claim traceable to raw PDF text

## What a reviewer must check
1. No fenced code blocks starting with an English sentence
2. Every chapter has its design patterns listed as ## or ### headings
3. images/ folder has PNGs referenced with relative paths
4. 00_INDEX.md has correct page ranges and links all 10 chapters
5. Code in fences is syntactically plausible — not truncated mid-statement
6. No repeated chapter titles or duplicated content blocks
