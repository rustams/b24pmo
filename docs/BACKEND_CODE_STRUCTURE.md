# Backend Code Structure (Python)

This project now follows feature-oriented backend modularization.

## Root
- `backends/python/api/main/models.py` - shared integration models (Bitrix account/install)
- `backends/python/api/main/urls.py` - centralized route map
- `backends/python/api/main/views.py` - compatibility facade

## Feature Modules
- `main/features/common/` - root/health/enum/list endpoints
- `main/features/installer/` - install/getToken lifecycle
- `main/features/strategy/` - goals/initiatives
- `main/features/delivery/` - portfolios/programs/projects/milestones
- `main/features/resources/` - allocations/capacity
- `main/features/risks/` - risk registry surface
- `main/features/budget/` - budget transactions
- `main/features/meetings/` - meeting logs and decisions
- `main/features/sync/` - sync status and trigger endpoints
- `main/features/rbac/` - role matrix endpoints

Each feature module contains:
- `services.py` for business logic
- `views.py` for HTTP handlers
- `__init__.py` for package boundary

This keeps files small and supports incremental expansion toward full PMO Hub implementation.
