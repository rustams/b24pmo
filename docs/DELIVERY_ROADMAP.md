# PMO Hub Delivery Roadmap (MVP -> v1.1)

## Goal
Deliver PMO Hub as a production-grade Bitrix24 app with predictable milestones, dependency-managed execution, and dual tracking:
- repository artifacts (`.agent/*`, code, docs)
- Bitrix24 project tasks (webhook automation)

## Delivery Principles
- Domain-by-domain vertical slices (backend + frontend + integration).
- Idempotent install/sync behavior first, then business features.
- Every milestone has: API contract, UI flow, tests, and observability hook.
- Bitrix24 task board is the operational source for execution status.

## Stage Plan

### Stage 0: Foundation and Operational Baseline (Week 1)
- Finalize environment, CI checks, coding conventions.
- Lock integration contract for Bitrix24 REST and webhook handling.
- Prepare roadmap automation (task creation + dependency sync).

Exit criteria:
- Base environments stable.
- Roadmap tasks created in Bitrix24 and linked by dependencies.

### Stage 1: Installer and Mapping Core (Weeks 1-2)
- Build installer flow: OAuth state, mapping SP/Lists, permission checks.
- Add config persistence and idempotency guarantees.
- Implement first sync cycle for users/tasks/calendar skeleton.

Exit criteria:
- Portal onboarding succeeds end-to-end.
- Mapping config is editable and persisted.

### Stage 2: Strategy and Project Delivery Core (Weeks 2-4)
- Implement Goals/Initiatives/Projects API slices.
- Build PMO tabs/pages for strategy and delivery views.
- Implement milestone CRUD + task-driven progress recalculation.

Exit criteria:
- PM can manage goals/initiatives/projects and milestones in UI.
- Task updates propagate into milestone progress.

### Stage 3: Resources, Risks, Budget, Meetings (Weeks 4-6)
- Resource allocation CRUD + day-level cache recomputation jobs.
- Risks list workflow (manual MVP path).
- Budget transaction ingestion and plan/fact read model.
- Meeting protocol storage + linked action items.

Exit criteria:
- Resource timeline works with conflict warnings.
- Risks, budget entries, and meeting records are usable from PMO UI.

### Stage 4: RBAC, Dashboards, Hardening (Weeks 6-8)
- Enforce role-scoped access in backend endpoints and UI navigation.
- Add project-level dashboard widgets (milestones/risks/load).
- Add health checks, structured logs, error handling, and baseline tests.

Exit criteria:
- Role restrictions validated.
- MVP DoD baseline reached for release candidate.

### Stage 5: v1.1 Extension (Post-MVP)
- Portfolio/CEO dashboards.
- AI keyword-based risk suggestion worker.
- Roles/Skills matching in resource planner.

## Work Tracking Model
- Master task catalog: `docs/ROADMAP_TASKS.json`
- Optional status snapshot input: `docs/ROADMAP_STATUS.example.json`
- Sync script: `scripts/bitrix24/roadmap_sync.py`
- Task-id mapping output: `.agent/context/bitrix-task-map.json`
- Naming rule in Bitrix24: human-readable task title first, then `[RD-xxx][EPIC-xxx]`.
- Task descriptions in Bitrix24 are maintained in Russian.
- After every push, deployment sync on VPS must be verified with `scripts/vps/verify-sync.sh`.

## Bitrix24 Integration Contract
Required for automation:
1. Bitrix24 Project (GROUP_ID) already created.
2. Incoming webhook URL with task permissions.
3. Responsible user IDs (optional per task, fallback default allowed).

Primary REST methods:
- `tasks.task.add`
- `tasks.task.update`
- `task.dependence.add`

## Suggested Execution Cadence
- Planning sync: once before sprint kickoff.
- Status sync: daily or after significant task transitions.
- Weekly checkpoint: update `.agent/context/session-summary.md` and risk log.
