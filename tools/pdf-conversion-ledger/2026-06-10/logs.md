# Logs — 2026-06-10

## Task
Coach the user on resume-worthy projects pulled from 4 external GitHub repos, with a
worker→reviewer agent loop verifying DE-relevance and grounding for each pick.

## Steps
- Created ledger/, reviewer-brief.md (DE-targeted curation criteria), lessons.md.
- Launched survey workflow #1 (DE-filtered). Two JS bugs first: `await parallel(...).filter`
  precedence (needs parens) and unbalanced paren after the fix. Re-ran clean; completed.
  Result: 3 of 4 repos are low-value for a DE; only real DE pick is the Kafka streaming
  project in project-based-learning (closes the Kafka gap).
- PIVOT: user clarified they do NOT want a DE-only filter — they want the highest
  SENIOR-PROFILE-value projects across ALL categories, every category represented.
- Relaunched workflow #2 (senior-profile lens): per-repo survey across all categories,
  synthesis ranks by profile-weight with per-category picks + build order, adversarial
  reviewer checks grounding/coverage/honesty. Running.
- Answers captured: goal = overall senior profile value (not strictly DE); scope = every category.
- Workflow #2 completed; reviewer caught ML repo misattribution (logged in errors.md); corrected
  and delivered the 7-pick plan + ranking + build order.
- User asked for MORE projects across DE/AI/LLM/ML/DevOps. Launched workflow #3 (domain-catalog):
  5 domain agents (web search + fetch-verify), synthesis, URL-checking reviewer.
- Workflow #3: surveys + synthesis completed (~30 verified picks across 5 domains). Reviewer agent
  FAILED on session limit (resets ~11:20pm PT). Substituted a manual spot-check of 5 highest-risk
  URLs (NeMo Guardrails reorg, LangGraph deep notebook path, aws-samples streaming, dbt-testing,
  monte-carlo) — all 5 resolved and matched descriptions. Delivered catalog with verification caveat.
- TODO when limit resets: optionally run the full adversarial URL reviewer over workflow #3 output.
