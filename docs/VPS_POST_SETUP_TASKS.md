# Задачи пост-настройки VPS (последовательность)

После установки сервера через cloud-init в Timeweb выполняем по порядку.

| # | Ключ | Задача | Где выполнять |
|---|------|--------|----------------|
| 1 | **RD-601** | Проверить доступ по SSH (deploy@IP, root@IP) и работу приложения по http | Локально + браузер |
| 2 | **RD-602** | Прописать секреты в .env на VPS (JWT, Bitrix, VIRTUAL_HOST) | SSH на VPS, редактировать /opt/b24-ai-starter/.env |
| 3 | **RD-603** | Выпустить TLS: certbot --nginx -d russalp.ru | SSH на VPS |
| 4 | **RD-604** | Обновить .env.webhooks в репозитории (VPS_DEPLOY_HOST, VPS_HEALTH_URL) | Локально в корне проекта |
| 5 | **RD-605** | Прогнать ./scripts/vps/verify-sync.sh, зафиксировать статус | Локально |

**Связи:** RD-601 → RD-602 → RD-603 → RD-604 → RD-605 (каждая следующая зависит от предыдущей).

**В Bitrix24:** задачи созданы в проекте, эпик EPIC-OPS. Статусы синхронизируются через `scripts/bitrix24/roadmap_sync.py sync-status`.

**Источник задач:** `docs/ROADMAP_TASKS.json` (ключи RD-601 … RD-605). Статусы в репозитории: `docs/ROADMAP_EXECUTION_STATUS.json`.
