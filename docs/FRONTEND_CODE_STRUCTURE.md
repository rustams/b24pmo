# Frontend Code Structure (Nuxt 3)

Frontend is now organized by PMO feature domains to mirror backend modules.

## Existing Core
- `frontend/app/pages/` - route entrypoints
- `frontend/app/stores/api.ts` - auth token lifecycle + authenticated HTTP helpers
- `frontend/app/stores/pmo.ts` - PMO domain state orchestration

## PMO Feature Layer
- `frontend/app/features/pmo/shared/`
  - `types.ts` shared contracts
  - `module-cards.ts` PMO navigation cards
- `frontend/app/features/pmo/components/`
  - `PmoModuleCard.vue`
  - `PmoOverviewPanel.vue`
- `frontend/app/features/pmo/modules/*/api.ts`
  - strategy
  - delivery
  - resources
  - risks
  - budget
  - meetings
  - sync
  - rbac

## PMO Pages
- `frontend/app/pages/pmo/index.client.vue`
- `frontend/app/pages/pmo/strategy.client.vue`
- `frontend/app/pages/pmo/delivery.client.vue`
- `frontend/app/pages/pmo/resources.client.vue`
- `frontend/app/pages/pmo/risks.client.vue`
- `frontend/app/pages/pmo/budget.client.vue`
- `frontend/app/pages/pmo/meetings.client.vue`
- `frontend/app/pages/pmo/sync.client.vue`
- `frontend/app/pages/pmo/rbac.client.vue`

## Backend Binding
All PMO module APIs call backend scaffold routes under `/api/pmo/*`, which mirror backend feature modules in:
`backends/python/api/main/features/*`

This design allows independent growth of each business block without inflating a few central files.
