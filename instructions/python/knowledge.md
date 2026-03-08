# Python Backend: Knowledge Base (Current Stack)

## Stack
- Framework: Django
- Bitrix SDK: `b24pysdk`
- Runtime: Docker (`api-python`)
- DB: PostgreSQL/MySQL via `.env`

## Main Paths
- API views: `backends/python/api/main/views.py`
- Models: `backends/python/api/main/models.py`
- Auth/Decorators: `backends/python/api/main/utils/decorators/`
- URL routing: `backends/python/api/main/urls.py`

## Core Endpoints
- `GET /api/health`
- `GET /api/enum`
- `GET /api/list`
- `POST /api/install`
- `POST /api/getToken`

## Auth Flow
1. Bitrix calls install handler with OAuth payload.
2. Backend stores/updates account data.
3. Frontend requests JWT via `/api/getToken`.
4. Protected API calls use `Authorization: Bearer <token>`.

## Development
- Start stack: `make dev-python`
- Logs: `make logs`
- Stop: `make down`

## Queue (optional)
- Enable `ENABLE_RABBITMQ=1` in `.env`
- See `instructions/queues/python.md`

## Code Principles
- Keep views thin; business logic in services/helpers.
- Validate portal and role context in each critical operation.
- Use idempotent handlers for webhooks/install flows.
