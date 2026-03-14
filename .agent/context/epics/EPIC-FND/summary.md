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

## Reopen Iteration (2026-03-15)
- `RD-004` reopened and moved back to `IN_PROGRESS` for a new admin UX iteration.
- Context synchronization completed from mandatory sources:
  - `instructions/*` agent architecture/workflow docs
  - roadmap files (`docs/ROADMAP_TASKS.json`, `docs/ROADMAP_EXECUTION_STATUS.json`)
  - global memory (`session-summary`, `decision-log`, `artifact-index`, `current-plan`, rubric)
  - epic-local memory (`EPIC-FND/handoff|summary|decisions|artifacts`)
- Dependency gate re-check:
  - `RD-004 depends_on RD-003`
  - `RD-003=5 (DONE)` in repo status file
  - cross-epic blockers: none
  - result: **unblocked**
- Implementation hold rule applied:
  - no final UI decisions before user clarifies desired information blocks and visual style for admin list + card.

## Stage 1 (Unfold Base Integration)
- Applied first-stage modern admin skin integration with `django-unfold`:
  - dependency added to `backends/python/api/requirements.txt`
  - `unfold` enabled in `INSTALLED_APPS` in `backends/python/api/settings.py`
  - minimal `UNFOLD` branding config added (`SITE_TITLE`, `SITE_HEADER`, `SITE_SUBHEADER`)
  - existing admin classes switched to `unfold.admin.ModelAdmin` in `backends/python/api/main/admin.py`
- Current step intentionally avoids final layout decisions for list/detail content density.
- Validation:
  - `python3 -m compileall backends/python/api/settings.py backends/python/api/main/admin.py` passed
  - `ReadLints` for changed files: no issues

## Stage 2 (Admin UX Information Architecture)
- Upgraded list/detail information hierarchy for installations and accounts in `backends/python/api/main/admin.py`.
- Added compact visual status indicators (badge-style rendering) for:
  - installation status
  - account status
  - auth health
- Increased operational readability in list view:
  - added token TTL metric (`token_ttl_hours`)
  - added portal segmentation (`portal_size_tier`)
  - reordered list columns to show high-priority health indicators first
- Expanded installation card blocks with operator-focused summaries:
  - `portal_overview`
  - `auth_timeline`
  - status/token metrics grouped in analytics section
- Validation:
  - `python3 -m compileall backends/python/api/main/admin.py` passed
  - `ReadLints` for `admin.py`: no issues

## Branch Isolation
- To avoid conflicts with the parallel EPIC-2 agent, all RD-004 stage 1+2 changes were isolated in branch:
  - `epic-fnd-rd004-admin-unfold`
- Commit created in that branch:
  - `2f13db6` (`feat(admin): modernize RD-004 with Unfold and richer diagnostics UX`)
