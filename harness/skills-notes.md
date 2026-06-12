# Harness — skills usage notes

How to use the designated skills well. Agents that build frontend/visual content read this.

## impeccable (pbakaus/impeccable) — design / anti-slop
- Installed into `.claude/skills/`. Access via `/impeccable <command>` (23 commands), e.g.
  `/impeccable polish <page>`, `/impeccable audit <page>`.
- After install, run `/impeccable init` once per project to set the design language.
- Has 41 deterministic detectors for AI-generated frontend slop — treat a failing detector as a
  blocking issue, not a suggestion.
- Rule: any `index.html` an agent produces must be polished/audited with impeccable before it can PASS.

## find-skills (vercel-labs/skills) — discovery
- `npx skills find <query>` to discover a skill before hand-rolling a capability.
- Prefer skills with high install count / official source (Vercel, Anthropic) / GitHub stars.
- Use when a day's concept needs a capability we don't already have a clean approach for.

## (append learnings about these skills as we use them)
