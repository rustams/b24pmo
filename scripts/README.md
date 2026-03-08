# Скрипты автоматизации (Python + Frontend)

Папка содержит служебные скрипты для запуска и сопровождения проекта PMO Hub на базе Bitrix24 Starter.

## Основные скрипты

| Скрипт | Назначение | Команда |
|---|---|---|
| `dev-init.sh` | Интерактивная инициализация окружения | `make dev-init` |
| `security-scan.sh` | Быстрый аудит зависимостей | `make security-scan` |
| `security-tests.sh` | Оркестратор security-проверок | `make security-tests` |
| `create-version.sh` | Создать новую версию в `versions/<name>` | `make create-version VERSION=v2` |
| `delete-version.sh` | Удалить версию из `versions/<name>` | `make delete-version VERSION=v2` |
| `test-cloudpub.sh` | Проверка Cloudpub | `./scripts/test-cloudpub.sh` |

## Рекомендуемый рабочий поток

1. Инициализация:
```bash
make dev-init
```

2. Разработка:
```bash
make dev-python
make logs
```

3. Остановка:
```bash
make down
```

4. Проверки перед релизом:
```bash
make quality-check
make security-scan
make security-tests
```

`make quality-check` запускает базовый контур качества (RD-002):
- синтаксическая проверка Python-кода backend,
- валидация ключевых JSON roadmap-файлов,
- линт frontend (если установлен `pnpm`).

## Очереди

При `ENABLE_RABBITMQ=1` можно управлять брокером отдельно:

```bash
make queue-up
make queue-down
```

Детали по интеграции воркеров: `instructions/queues/server.md`, `instructions/queues/python.md`.

## Bitrix24 Roadmap Automation

Для синхронизации roadmap в проект Bitrix24 добавлен CLI:

```bash
python3 scripts/bitrix24/roadmap_sync.py create \
  --webhook-url "https://<portal>/rest/<user>/<hook>/" \
  --project-id <GROUP_ID> \
  --source docs/ROADMAP_TASKS.json \
  --output .agent/context/bitrix-task-map.json \
  --default-responsible-id <USER_ID> \
  --apply
```

Создать только новые задачи, которых ещё нет в map-файле:

```bash
python3 scripts/bitrix24/roadmap_sync.py create-missing \
  --project-id <GROUP_ID> \
  --source docs/ROADMAP_TASKS.json \
  --map-file .agent/context/bitrix-task-map.json \
  --default-responsible-id <USER_ID> \
  --apply
```

Синхронизация статусов выполнения:

```bash
python3 scripts/bitrix24/roadmap_sync.py sync-status \
  --map-file .agent/context/bitrix-task-map.json \
  --status-file docs/ROADMAP_EXECUTION_STATUS.json \
  --sync-kanban \
  --kanban-entity-id <GROUP_ID> \
  --apply
```

По умолчанию скрипт работает в dry-run режиме. Для реальной записи обязателен флаг `--apply`.

Обновление описаний/названий задач из roadmap (эпик, skills, тесты, DoD):

```bash
python3 scripts/bitrix24/roadmap_sync.py sync-metadata \
  --source docs/ROADMAP_TASKS.json \
  --map-file .agent/context/bitrix-task-map.json \
  --apply
```

Рекомендуемое соответствие workflow-статусов:
- `В работе` -> `STATUS=3`
- `На тестировании` -> `STATUS=4`
- `Сделаны` -> `STATUS=5`

Синхронизация структуры эпиков и подзадач (иерархия + связи по Ганту):

```bash
python3 scripts/bitrix24/roadmap_sync.py sync-epic-structure \
  --project-id <GROUP_ID> \
  --source docs/ROADMAP_TASKS.json \
  --map-file .agent/context/bitrix-task-map.json \
  --default-responsible-id <USER_ID> \
  --apply
```

Правила структуры в Bitrix24:
- Эпик — отдельная базовая задача верхнего уровня.
- Все roadmap-задачи эпика — подзадачи эпика.
- Вложенные подзадачи (`2.1`, `2.2`) задаются через поле `parent` в `docs/ROADMAP_TASKS.json`.
- Последовательность выполнения отражается зависимостями (Gantt links).
- Межэпиковые зависимости также создаются через связи задач.

Получение актуальных канбан-стадий из Bitrix24:

```bash
python3 scripts/bitrix24/roadmap_sync.py fetch-stages \
  --entity-id <GROUP_ID> \
  --output .agent/context/bitrix-kanban-stages.json
```

Важно: если `--webhook-url` не передан, скрипт использует `B24_WEBHOOK_URL` из `.env` или `.env.webhooks`.

## Проверка синхронизации деплоя на VPS (обязательно после push)

```bash
./scripts/vps/verify-sync.sh
```

Скрипт проверяет:
- совпадение локального commit и commit на VPS,
- совпадение commit на VPS с `origin/master`,
- активность сервисов `b24-ai-starter` и `b24-webhook`,
- health-check `200` на `VPS_HEALTH_URL`.
