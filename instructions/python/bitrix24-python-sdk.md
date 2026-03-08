# Bitrix24 Python SDK Guide for This Project

## Purpose
Use `b24pysdk` from Django backend for Bitrix24 REST operations required by PMO Hub.

## Where to Integrate
- Main API layer: `backends/python/api/main/views.py`
- Account/token model: `backends/python/api/main/models.py`
- Authorization decorators: `backends/python/api/main/utils/decorators/`

## Typical Usage Pattern
```python
client = request.bitrix24_account.client
items = client.call("crm.item.list", {
    "entityTypeId": 123,
    "filter": {},
    "select": ["id", "title"]
})
```

## Required Method Groups
- Smart Processes: `crm.item.get|add|update|list`
- Lists: `lists.element.get|add|update|list`
- Tasks: `tasks.task.get|list`, `task.item.update`, `task.elapseditem.get`
- Users: `user.get|list`
- Calendar: `calendar.accessibility.get`, `calendar.event.get`
- Sonet groups: `sonet_group.get|add`

## Reliability Rules
- Use batch operations for bulk sync.
- Respect per-portal rate limit and retries with backoff.
- Move heavy operations to queue workers.

## Security Rules
- Never log full tokens.
- Store only minimum personal data in app DB.
- Validate role/access before mutating project/budget/risk data.
