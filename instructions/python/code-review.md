# Python Code Review Checklist (Project-Specific)

## Critical
- Authentication/authorization checks are present.
- Portal isolation (`portal_id`) is enforced.
- Webhook/install handlers are idempotent.
- External Bitrix calls have error handling and retry strategy.

## Correctness
- Business rules for PMO entities are deterministic.
- Date/time calculations use explicit timezone handling.
- Resource/budget aggregation avoids double counting.

## Maintainability
- Views are thin; logic extracted to services/helpers.
- Function and module names are clear.
- Type hints are used for public functions.

## Security
- No token leakage in logs.
- No hardcoded secrets.
- Inputs validated and sanitized.

## Performance
- Batch API is used where possible.
- Expensive recalculations are moved to workers.
- DB queries are indexed and bounded.
