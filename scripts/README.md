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
make security-scan
make security-tests
```

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

Синхронизация статусов выполнения:

```bash
python3 scripts/bitrix24/roadmap_sync.py sync-status \
  --webhook-url "https://<portal>/rest/<user>/<hook>/" \
  --map-file .agent/context/bitrix-task-map.json \
  --status-file docs/ROADMAP_STATUS.example.json \
  --apply
```

По умолчанию скрипт работает в dry-run режиме. Для реальной записи обязателен флаг `--apply`.
