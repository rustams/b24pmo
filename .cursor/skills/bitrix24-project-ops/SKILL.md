---
name: bitrix24-project-ops
description: Управление задачами проекта в Bitrix24 через webhook: синхронизация статусов и канбана, обновление описаний, запись результата задачи, автозакрытие эпиков и обязательная проверка синхронизации деплоя на VPS после push.
---

# Bitrix24 Project Ops

Используй этот skill, когда задача требует:
- обновить статусы roadmap-задач в Bitrix24,
- переместить карточки по канбан-стадиям,
- синхронизировать названия/описания задач по шаблону roadmap,
- проверить, что деплой на VPS синхронизирован с `origin/master`.

## Обязательные правила

1. Источник истины — репозиторий (`docs/ROADMAP_TASKS.json`, `docs/ROADMAP_EXECUTION_STATUS.json`, `.agent/*`).
2. Bitrix24 используется для визуального контроля, но статусы должны дублироваться в репозитории.
3. Название задачи в Bitrix24:
- сначала человекопонятное название,
- потом служебный хвост: `[RD-xxx][EPIC-xxx]`.
4. Эпик в Bitrix24 — это отдельная базовая задача верхнего уровня.
5. Задачи эпика оформляются как подзадачи эпика; вложенные уровни (`2.1`, `2.2`) — через `parent`.
6. В описании эпика обязательно: состав задач, используемые skills/инструменты, критерий завершения эпика.
7. Описание задач — на русском языке.
8. При завершении задачи обязательно заполнить в Bitrix24 `Результат задачи`: что сделано + ссылка на commit.
9. Для эпиков включить опцию автозакрытия основной задачи при закрытии подзадач.
10. Если эпик закрыт, добавить в его название слово `Завершена`.
11. После `git push` обязательно запускать `./scripts/vps/verify-sync.sh`.

## Базовые команды

Получить актуальные канбан-стадии:
```bash
python3 scripts/bitrix24/roadmap_sync.py fetch-stages \
  --entity-id "$B24_PROJECT_GROUP_ID" \
  --output .agent/context/bitrix-kanban-stages.json
```

Обновить названия/описания/теги:
```bash
python3 scripts/bitrix24/roadmap_sync.py sync-metadata \
  --source docs/ROADMAP_TASKS.json \
  --map-file .agent/context/bitrix-task-map.json \
  --apply
```

Обновить статусы и переместить карточки по канбану:
```bash
python3 scripts/bitrix24/roadmap_sync.py sync-status \
  --map-file .agent/context/bitrix-task-map.json \
  --status-file docs/ROADMAP_EXECUTION_STATUS.json \
  --sync-kanban \
  --kanban-entity-id "$B24_PROJECT_GROUP_ID" \
  --apply
```

Синхронизировать иерархию эпиков/подзадач и связи по Ганту:
```bash
python3 scripts/bitrix24/roadmap_sync.py sync-epic-structure \
  --project-id "$B24_PROJECT_GROUP_ID" \
  --source docs/ROADMAP_TASKS.json \
  --map-file .agent/context/bitrix-task-map.json \
  --default-responsible-id 1 \
  --apply
```

Записать результаты завершенных задач (включая уже завершенные):
```bash
python3 scripts/bitrix24/roadmap_sync.py sync-task-results \
  --source docs/ROADMAP_TASKS.json \
  --map-file .agent/context/bitrix-task-map.json \
  --status-file docs/ROADMAP_EXECUTION_STATUS.json \
  --commit-url "https://github.com/rustams/b24pmo/commit/<hash>" \
  --apply
```

Синхронизировать автозакрытие эпиков и закрыть/переименовать завершенные эпики:
```bash
python3 scripts/bitrix24/roadmap_sync.py sync-epic-completion \
  --source docs/ROADMAP_TASKS.json \
  --map-file .agent/context/bitrix-task-map.json \
  --status-file docs/ROADMAP_EXECUTION_STATUS.json \
  --apply
```

Проверить синхронизацию деплоя на VPS:
```bash
./scripts/vps/verify-sync.sh
```

## Workflow статусов

- `В работе` -> `STATUS=3`
- `На тестировании` -> `STATUS=4`
- `Сделаны` -> `STATUS=5`

При переходе статуса сначала обнови `docs/ROADMAP_EXECUTION_STATUS.json`, затем выполни `sync-status --sync-kanban --apply`.
