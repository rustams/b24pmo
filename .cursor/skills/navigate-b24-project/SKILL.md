---
name: navigate-b24-project
description: Understand the PHP + frontend structure of this Bitrix24 project. Use this skill to quickly find where to implement UI, API, and integration logic.
---

# Navigate Bitrix24 Project (PHP + Frontend)

## Project Structure

```text
b24-ai-starter/
├── frontend/                 # Nuxt 3 Frontend
│   ├── app/pages/            # Pages (.client.vue)
│   ├── app/components/       # UI Components
│   ├── app/stores/           # Pinia Stores
│   └── app/composables/      # Shared Logic
├── backends/php/             # Symfony 7 + Bitrix24 PHP SDK
│   ├── src/Controller/       # API endpoints
│   ├── src/Service/          # Business logic
│   └── src/Bitrix24Core/     # OAuth/events/integration core
├── instructions/             # Active guidance
│   ├── knowledge.md
│   ├── front/
│   ├── php/
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
| PHP endpoints | `backends/php/src/Controller/` |
| PHP services | `backends/php/src/Service/` |
| Bitrix24 core integration | `backends/php/src/Bitrix24Core/` |
| Env/config | `.env`, `docker-compose.yml`, `makefile` |

## Documentation

- General: `instructions/knowledge.md`
- Frontend: `instructions/front/knowledge.md`
- PHP: `instructions/php/knowledge.md`
- Widgets/Robots: `instructions/bitrix24/`
