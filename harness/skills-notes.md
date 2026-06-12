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

## Learnings (2026-06-12, first use)
- Windows: `npx impeccable skills install` fails on the `unzip` step (no unzip on Windows). The zip
  IS downloaded to %TEMP%\impeccable-update-*.zip — extract it with PowerShell Expand-Archive and
  copy the `.claude` subtree into the project. The CLI's `detect` command itself works fine.
- The anti-slop gate is `npx impeccable@2.3.2 detect <file>` → exit 0 = clean, exit 2 = anti-patterns.
  This is deterministic and runnable in Bash, so any agent can gate HTML with it regardless of
  whether the `/impeccable` slash command is wired up.
- Pin the version (`impeccable@2.3.2`) so npx doesn't re-resolve/hang.
- Build HTML to avoid P-03 / P-04 on the first pass; expect 1-2 detect/fix cycles otherwise.
