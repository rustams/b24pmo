# Окружение и конфигурация (для агента и разработки)

Файл — единый источник правды по env, конфигам и скриптам, которые от них зависят. Папки `env` в репозитории нет; все настройки — в корневых файлах.

## Где что лежит

| Что | Где | В git |
|-----|-----|--------|
| Основной конфиг приложения | `.env` в корне | Нет (.gitignore) |
| Шаблон основного конфига | `.env.example` в корне | Да |
| Webhook и VPS (секреты/хост) | `.env.webhooks` в корне | Нет (.gitignore) |
| Шаблон webhook/VPS | `.env.webhooks.example` в корне | Да |
| Docker/Compose | `docker-compose.yml`, `docker-compose.override.yml` | Да |
| Make | `makefile` | Да |

Docker Compose подхватывает `.env` через `env_file: .env` и переменные окружения при `docker compose --env-file .env up`. Makefile для `dev-python` читает из `.env` значения `DB_TYPE` и `ENABLE_RABBITMQ` (grep).

## Назначение файлов

- **`.env`** — JWT, Bitrix CLIENT_ID/CLIENT_SECRET, VIRTUAL_HOST, SERVER_HOST, DB_*, RabbitMQ, CloudPub, BUILD_TARGET, опционально VPS_* и B24_*. Нужен для `make dev-python`, фронта и API. При ошибке парсинга (например, символ `&`) скрипты, которые только source'ят его, могут падать; `verify-sync.sh` при ошибке загрузки `.env` продолжает и подхватывает переменные из `.env.webhooks`.
- **`.env.webhooks`** — копия `.env.webhooks.example` с подставленными значениями. Содержит `B24_WEBHOOK_URL`, `B24_PROJECT_GROUP_ID` и при необходимости `VPS_DEPLOY_*`, `VPS_HEALTH_URL`. Не обязателен для запуска приложения; нужен для `scripts/bitrix24/roadmap_sync.py` и для `scripts/vps/verify-sync.sh`.
- **`.env.example`** — полный шаблон, включая блок VPS (VPS_DEPLOY_USER, VPS_DEPLOY_HOST, VPS_APP_PATH, VPS_HEALTH_URL). Значения по проекту: deploy, 85.239.54.74, /opt/b24-ai-starter, https://russalp.ru.
- **`.env.webhooks.example`** — шаблон только для webhook и VPS; те же VPS-значения. Рекомендуется скопировать в `.env.webhooks` и заполнить секреты.

## Переменные для скриптов

### Bitrix24 roadmap sync (`scripts/bitrix24/roadmap_sync.py`)

- **B24_WEBHOOK_URL** — обязателен для любых команд, пишущих в Bitrix24 (create, sync-status, sync-metadata, sync-epic-structure, sync-task-results, sync-epic-completion). Берётся из `--webhook-url` или из окружения после загрузки `.env` и `.env.webhooks` (скрипт сам читает оба файла и подставляет в `os.environ` недостающие ключи).
- **B24_PROJECT_GROUP_ID** — ID проекта в Bitrix24 (например 17). Используется в командах с `--project-id` / `--kanban-entity-id`, если не передан аргумент.

Скрипт не использует bash `source`; он парсит `.env` и `.env.webhooks` построчно. Поэтому сложные значения в `.env` (с `&` и т.п.) при запуске Python-скрипта не мешают.

### VPS verify (`scripts/vps/verify-sync.sh`)

- **VPS_DEPLOY_HOST** — обязателен (IP или хост, например 85.239.54.74).
- **VPS_HEALTH_URL** — обязателен (URL для проверки, например https://russalp.ru).
- **VPS_DEPLOY_USER** — по умолчанию deploy.
- **VPS_APP_PATH** — по умолчанию /opt/b24-ai-starter.

Скрипт загружает сначала `.env` (ошибка парсинга игнорируется), затем `.env.webhooks`. Переменные можно задать в любом из них; при отсутствии обеих — сообщение: задать в `.env` или `.env.webhooks` (см. `.env.webhooks.example`). Для проверки нужен SSH по ключу: `ssh ${VPS_DEPLOY_USER}@${VPS_DEPLOY_HOST}` без пароля.

## Кодовые базы (кратко)

- **Backend**: `backends/python/api/main/` — `urls.py` (маршруты), `models.py` (Bitrix24Account и т.д.), `features/*/` (common, installer, strategy, delivery, resources, risks, budget, meetings, sync, rbac). В каждом модуле: `views.py`, `services.py`. Детали: `docs/BACKEND_CODE_STRUCTURE.md`.
- **Frontend**: `frontend/app/` — `pages/` (*.client.vue), `stores/api.ts`, `stores/pmo.ts`, `features/pmo/` (modules/*/api.ts, components). Детали: `docs/FRONTEND_CODE_STRUCTURE.md`.
- **Roadmap/операции**: источник задач — `docs/ROADMAP_TASKS.json`; статусы в репозитории — `docs/ROADMAP_EXECUTION_STATUS.json`; маппинг ключ → task ID в Bitrix24 — `.agent/context/bitrix-task-map.json`; канбан-стадии (снимок) — `.agent/context/bitrix-kanban-stages.json`. Синхронизация: `scripts/bitrix24/roadmap_sync.py` (create, sync-status, sync-metadata, sync-epic-structure, sync-task-results, sync-epic-completion, fetch-stages). После push — обязательно `./scripts/vps/verify-sync.sh` (при настроенных VPS_* в .env или .env.webhooks).

## Что помнить агенту

1. Папки `env` в репозитории нет; все настройки — в корне (`.env`, `.env.example`, `.env.webhooks`, `.env.webhooks.example`).
2. Для Bitrix24 sync достаточно корректного `B24_WEBHOOK_URL` (и при необходимости `B24_PROJECT_GROUP_ID`); удобно держать их в `.env.webhooks`.
3. Для VPS verify нужны `VPS_DEPLOY_HOST` и `VPS_HEALTH_URL` в `.env` или `.env.webhooks`; при проблемах с парсингом `.env` использовать `.env.webhooks` и `cp .env.webhooks.example .env.webhooks`.
4. План и артефакты агента — `.agent/plans/current-plan.md`, `.agent/context/session-summary.md`, `.agent/context/decision-log.jsonl`, `.agent/context/artifact-index.jsonl`; при задачах roadmap обновлять `ROADMAP_EXECUTION_STATUS.json` и при наличии webhook — синхронизировать Bitrix24, после push — запускать verify-sync при наличии VPS-переменных.
