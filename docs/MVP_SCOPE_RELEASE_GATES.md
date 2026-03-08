# RD-001: MVP Scope and Release Gates

## Purpose
Lock MVP boundaries and release gates for PMO Hub delivery so execution can proceed without scope drift.

## In Scope (MVP v1.0)
- Installer + onboarding + mapping of Smart Processes and Lists.
- Core domains:
  - Goals, Initiatives, Projects.
  - Milestones, ResourceAllocations, Risks (manual), BudgetTransactions (basic).
- PMO Hub project tab/pages with create/read/update for core entities.
- Task webhook flow for milestone progress recalculation.
- Base RBAC for primary roles.
- Critical logging + health checks.

## Out of Scope (Post-MVP)
- Full portfolio optimization and scenario modeling.
- Advanced AI/LLM risk forecasting.
- Cross-portal analytics.
- Advanced financial analytics and ERP connectors.

## Delivery Gates

### Gate G0: Foundation Ready
- Roadmap tasks created and dependency-linked in Bitrix24.
- Execution workflow and status sync rules established.
- Source-of-truth artifacts available in repository.

### Gate G1: Installer Ready
- Onboarding flow is idempotent.
- Mapping configuration is persisted and editable.
- Scope checks provide deterministic admin guidance.

### Gate G2: Domain Core Ready
- Strategy + project + milestones flow works end-to-end.
- Task event updates milestone progress reliably.
- Core CRUD contracts documented and stable.

### Gate G3: Operational Domains Ready
- Resources, risks, budget, meetings flows are available in UI/API.
- Resource timeline supports allocation creation and conflict warning logic.

### Gate G4: Release Candidate
- RBAC enforced on backend and reflected in UI capabilities.
- Baseline quality checks pass.
- MVP acceptance checklist passed.

## MVP Acceptance Criteria
- Functional coverage equals MVP list from `docs/PMO_HUB_PRODUCT_SPEC.md`.
- All mandatory flows verified by technical and UI checks.
- No blocker defects in installer, project flow, or resource planning.
- Bitrix24 board and repository artifacts are synchronized.

## Testing Policy for Planning Tasks
- Technical:
  - Validate structure and traceability to product spec.
  - Validate referenced files and workflow commands are valid.
- UI:
  - Not applicable for this planning-only task.

## Artifacts
- `docs/DELIVERY_ROADMAP.md`
- `docs/ROADMAP_TASKS.json`
- `docs/ROADMAP_EXECUTION_STATUS.json`
- `docs/MVP_SCOPE_RELEASE_GATES.md` (this document)
