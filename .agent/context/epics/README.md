# Epic Context Workspace

Each epic is handled by a dedicated agent/session.

## Structure
- `EPIC-FND/`
- `EPIC-INS/`
- `EPIC-CORE/`
- `EPIC-OPS/`
- `EPIC-SEC/`
- `EPIC-V11/`

Each epic folder must contain:
- `handoff.json` (required, machine-readable)
- `summary.md` (recommended)
- `decisions.jsonl` (recommended)
- `artifacts.jsonl` (recommended)

Supervisor reads epic folders and merges updates into shared context:
- `.agent/context/session-summary.md`
- `.agent/context/decision-log.jsonl`
- `.agent/context/artifact-index.jsonl`
- `.agent/plans/current-plan.md`
