# Current Plan

## Активная задача
**RD-101** — Определить контракт сервиса установщика (API, идемпотентность, модель маппингов). Stage 1 - Installer, EPIC-INS.

## Статус в системах
- **Репозиторий**: `docs/ROADMAP_EXECUTION_STATUS.json` — RD-101 = IN_PROGRESS (3), active_task = RD-101.
- **Bitrix24**: обновление статуса и канбана выполнить локально командой (при заданных B24_WEBHOOK_URL и B24_PROJECT_GROUP_ID):
  ```bash
  python3 scripts/bitrix24/roadmap_sync.py sync-status \
    --map-file .agent/context/bitrix-task-map.json \
    --status-file docs/ROADMAP_EXECUTION_STATUS.json \
    --sync-kanban --kanban-entity-id "$B24_PROJECT_GROUP_ID" --apply
  ```

## Следующие шаги по RD-101
1. Зафиксировать API-контракт установщика (эндпоинты, входы/выходы).
2. Описать правила идемпотентности установки и обновления токенов.
3. Описать модель хранения маппингов (Smart Processes / Lists) в БД или конфиге.

## Дисциплина контекста
- План и решения в `.agent/`; в чате — краткие отсылки.
