# Agent Operating Architecture (PMO Hub)

## Purpose
Unified architecture for all AI-agent work in this repository.
Combines:
- Project skills (Bitrix24 + Python + Frontend)
- Context-engineering skills (imported from Agent-Skills-for-Context-Engineering)

## Architecture Layers
1. Skill Discovery Layer
- Agent reads skill names/descriptions only.
- Full skill content is loaded only when task matches triggers.

2. Orchestration Layer
- Default pattern: supervisor/orchestrator (single execution agent + specialized skill activation).
- Sub-agent pattern is optional for heavy parallelizable tasks.

3. Context Layer
- Working context: current task, changed files, active constraints.
- Persistent context (filesystem): `.agent/context/*`.
- Compression strategy: structured summaries preserving decisions, artifact trail, and next steps.

4. Tool Layer
- Prefer consolidated workflows over many narrow operations.
- Use deterministic file-based artifacts for reproducibility.

5. Evaluation Layer
- For non-trivial features, evaluate outcome using rubric in `.agent/evaluation/rubric.md`.
- Apply LLM-as-judge pattern only when manual checks are insufficient.

## Standard Execution Loop
1. Clarify scope and target outcome.
2. Activate minimal relevant skills.
3. Build/update plan in `.agent/plans/current-plan.md`.
4. Execute in small iterations with artifact logging.
5. Validate behavior and record decisions.
6. Compress context for next iteration.

## Mandatory Artifacts
- `.agent/context/session-summary.md`
- `.agent/context/decision-log.jsonl`
- `.agent/context/artifact-index.jsonl`
- `.agent/plans/current-plan.md`

## PMO Hub-Specific Defaults
- Backend: Python (Django + b24pysdk)
- Frontend: Nuxt 3 + Bitrix24 UI Kit
- Integration-first workflow: Bitrix placement/events -> backend API -> UI
- Heavy synchronization and recalculation tasks should be queue-ready by design.
- Bitrix24 project task operations run via webhook from env (`B24_WEBHOOK_URL`, `B24_PROJECT_GROUP_ID`).
- Task board conventions:
  - title format: human-readable title first, then `[RD-xxx][EPIC-xxx]`
  - descriptions in Russian
  - epic is a top-level task; roadmap tasks are epics' subtasks; nested subtasks use `parent`
  - kanban movement synced with task status transitions
  - on completion, fill Bitrix24 task result with summary + commit link
  - epic root tasks must have auto-close enabled; closed epic title includes `Завершена`
- Post-push deployment guardrail: verify VPS sync and health with `./scripts/vps/verify-sync.sh`.
- Config and env: single source of truth for env files, VPS/B24 variables, and script behaviour is `instructions/env-and-config.md`. Use it for any config, deploy, or script question (no `env/` folder — all env in repo root).
