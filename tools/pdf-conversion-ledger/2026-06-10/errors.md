# Errors — 2026-06-10

## Repo misattribution in ML/DL category (caught by reviewer agent)
- **Symptom:** Synthesis cited the two ML picks (GPT-2 Rebuild, Prices Predictor) as folders
  inside `AdilShamim8/100-AI-ML-DL`.
- **Root cause:** (1) wrong slug — `100-AI-ML-DL` 404s; real catalog repo is
  `100-AI-Machine-Learning-Deep-Learnin-Projects`. (2) The two ML projects are NOT folders in
  that catalog at all — they are standalone sibling repos by the same author. Survey agent
  conflated catalog links with in-repo folders.
- **Fix:** Cite the actual standalone repos:
  - GPT-2 Rebuild -> https://github.com/AdilShamim8/GPT-2-Rebuild-nanoGPT
  - Prices Predictor -> https://github.com/AdilShamim8/Prices_Predictor_System
  Also corrected Prices Predictor to "HOUSE price prediction" with a ZenML pipelines/steps
  MLOps layout (verified by reviewer: pipelines/, steps/, run_deployment.py, run_pipeline.py).
- **Lesson candidate:** Survey agents over GitHub *catalog* repos must distinguish in-repo
  folders from outbound links to sibling repos. (Watch for recurrence before promoting to lessons.md.)
