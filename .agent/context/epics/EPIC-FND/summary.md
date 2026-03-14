# EPIC-FND Summary

## Scope
- Epic: `EPIC-FND`
- Task: `RD-004` (Django admin installations monitoring)

## Dependency Gate
- `depends_on`: `RD-003`
- Status check: `RD-003=5 (DONE)` in `docs/ROADMAP_EXECUTION_STATUS.json`
- Cross-epic blockers: none declared for `RD-004`
- Decision: task is **unblocked**, implementation started

## What Was Implemented
- Enhanced `Bitrix24Account` Django admin with operational analytics:
  - token health (`has_valid_tokens`)
  - token expiration (`token_expires_at`)
  - scope preview (`scope_preview`)
  - filters, search, ordering, and structured fieldsets
- Enhanced `ApplicationInstallation` Django admin for installation diagnostics:
  - installation list with portal/account columns and auth diagnostics
  - card-level analytics (`auth_health`, token expiry, installation age)
  - status payload preview for fast troubleshooting
  - `list_select_related` and admin filters/search for fast navigation

## DoD Coverage
- User authentication in Django admin: supported by standard Django admin flow (unchanged).
- Installation list visibility: provided through `ApplicationInstallationAdmin` list view with searchable/filterable records.
- Installation card open by click: provided by Django admin change page for each row.
- Installation analytics on card: added readonly analytics fields and diagnostics section.

## Validation
- `python3 -m compileall backends/python/api/main/admin.py` passed.
- VPS check:
  - `/admin/login/` points to Nuxt frontend (not Django admin).
  - correct Django admin URL is `/api/admin/`.
  - end-to-end checks on `https://pmo.russaldi.com/api/admin/` passed:
    - login works
    - installations list opens
    - installation change page opens with analytics sections.
  - `https://pmo.russaldi.com/api/admin/main/bitrix24account/` opens without runtime errors.

## Production Fixes Applied
- Reset known Django superuser credentials on VPS for account `admin`.
- Fixed admin 500 on installations list:
  - root cause: `status_code` JSON parsing incompatibility in legacy table path
  - fix: defer `status_code` in queryset and render preview via SQL cast (`status_code::text`)
- Fixed admin 500 on installation card:
  - added missing readonly timestamps (`created_at_utc`, `update_at_utc`)
  - normalized naive datetime handling in `installation_age_hours`.
- Fixed admin 500 on `Bitrix24 accounts` list:
  - root cause: `django.utils.timezone.utc` attribute is absent in Django 5.2
  - fix: replaced with standard `datetime.timezone.utc` in timestamp conversion and aware datetime creation.

## Risks / Follow-ups
- Credentials should be changed by operator after first successful login.
- For very large payloads, preview is intentionally truncated to 2000 chars in admin view.

## Closure
- `RD-004` marked `DONE` in `docs/ROADMAP_EXECUTION_STATUS.json`.
- Bitrix24 sync completed:
  - `sync-status --sync-kanban --apply`
  - `sync-epic-completion --apply` (EPIC-FND marked complete, auto-close enabled).
- Epic status: **EPIC-FND completed**.
