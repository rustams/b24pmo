# Current Plan

## Активная задача
**RD-601** — Проверить доступ по SSH и работу приложения на новом VPS (первая задача цепочки пост-настройки).

## Цепочка задач VPS post-setup (последовательно)
1. **RD-601** — Проверить SSH (deploy@IP, root@IP) и http на сервере
2. **RD-602** — Прописать секреты в .env на VPS
3. **RD-603** — certbot --nginx -d russalp.ru
4. **RD-604** — Обновить .env.webhooks локально (VPS_DEPLOY_HOST, VPS_HEALTH_URL)
5. **RD-605** — Прогнать verify-sync.sh, зафиксировать статус

Подробно: `docs/VPS_POST_SETUP_TASKS.md`.

## Статус в системах
- **Репозиторий**: задачи RD-601…RD-605 добавлены в `docs/ROADMAP_TASKS.json` и `docs/ROADMAP_EXECUTION_STATUS.json` (все NEW). active_task = RD-601.
- **Bitrix24**: создание задач вернуло 403 (webhook без прав или неверный URL). После настройки webhook выполнить:
  ```bash
  python3 scripts/bitrix24/roadmap_sync.py create-missing --project-id 17 --source docs/ROADMAP_TASKS.json --map-file .agent/context/bitrix-task-map.json --default-responsible-id 1 --apply
  python3 scripts/bitrix24/roadmap_sync.py sync-epic-structure --project-id 17 --source docs/ROADMAP_TASKS.json --map-file .agent/context/bitrix-task-map.json --default-responsible-id 1 --apply
  ```

## После RD-605
Вернуться к **RD-101** (контракт установщика) или к следующей задаче по приоритету.

## Дисциплина контекста
- План и решения в `.agent/`; в чате — краткие отсылки.
