# Epic Agent Operating Model

## Goal
Run roadmap execution with one dedicated agent per epic, while preserving a single shared project memory.

## Roles
- **Supervisor**: plans execution, assigns epic agents, consolidates context.
- **Epic Agent**: executes only one epic scope and writes structured outcomes.

## Epic Scope
- `EPIC-FND`
- `EPIC-INS`
- `EPIC-CORE`
- `EPIC-OPS`
- `EPIC-SEC`
- `EPIC-V11`

## Filesystem Contract
Each epic agent writes to:
- `.agent/context/epics/<EPIC>/summary.md`
- `.agent/context/epics/<EPIC>/decisions.jsonl`
- `.agent/context/epics/<EPIC>/artifacts.jsonl`
- `.agent/context/epics/<EPIC>/handoff.json`

Supervisor updates shared memory:
- `.agent/context/session-summary.md`
- `.agent/context/decision-log.jsonl`
- `.agent/context/artifact-index.jsonl`
- `.agent/plans/current-plan.md`

## Handoff JSON Schema
```json
{
  "epic": "EPIC-FND",
  "timestamp": "2026-03-14T00:00:00Z",
  "status": "in_progress",
  "completed_tasks": [],
  "changed_files": [],
  "bitrix_sync": {
    "sync_epic_structure": "not_run",
    "sync_status": "not_run"
  },
  "open_risks": [],
  "next_actions": []
}
```

## Commit Policy
- Intermediate/admin commits are expected and should be frequent.
- `./scripts/vps/verify-sync.sh` is required only for:
  - large integration commits, or
  - functional milestone completion.

## Recommended Supervisor Loop
1. Pick next epic by dependency and risk.
2. Launch epic agent with explicit scope and DoD.
3. Validate epic-local artifacts and handoff.
4. Sync Bitrix24 as needed.
5. Merge into shared memory.
6. Create commit.
