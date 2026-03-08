---
name: navigate-b24-project
description: Understand the Python + frontend structure of this Bitrix24 project. Use this skill to quickly find where to implement UI, API, and integration logic.
---

# Navigate Bitrix24 Project (Python + Frontend)

## Project Structure

```text
b24-ai-starter/
├── frontend/                 # Nuxt 3 Frontend
│   ├── app/pages/            # Pages (.client.vue)
│   ├── app/components/       # UI Components
│   ├── app/stores/           # Pinia Stores
│   └── app/composables/      # Shared Logic
├── backends/python/          # Django + b24pysdk
│   ├── api/main/views.py     # API endpoints
│   ├── api/main/models.py    # Data models
│   └── api/main/utils/       # Auth/helpers/decorators
├── instructions/             # Active guidance
│   ├── knowledge.md
│   ├── front/
│   ├── python/
│   └── bitrix24/
├── scripts/                  # dev-init, security, versioning
├── docker-compose.yml
└── makefile
```

## Key Locations by Task

| Task | Location |
|------|----------|
| Frontend pages | `frontend/app/pages/` |
| Frontend components | `frontend/app/components/` |
| Frontend API/state | `frontend/app/stores/`, `frontend/app/composables/` |
| Python endpoints | `backends/python/api/main/views.py` |
| Python models | `backends/python/api/main/models.py` |
| Python auth/helpers | `backends/python/api/main/utils/` |
| Env/config | `.env`, `docker-compose.yml`, `makefile` |

## Documentation

- General: `instructions/knowledge.md`
- Frontend: `instructions/front/knowledge.md`
- Python: `instructions/python/knowledge.md`
- Widgets/Robots: `instructions/bitrix24/`
