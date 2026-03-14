# Current Plan

## Активная задача
**RD-602** — Прописать финальные OAuth-секреты (`CLIENT_ID`/`CLIENT_SECRET`) в `.env` на новом VPS после регистрации приложения.

## Цепочка задач VPS post-setup (последовательно)
1. **RD-601** — Проверить SSH (deploy@IP, root@IP) и доступность сервера ✅
2. **RD-602** — Прописать `CLIENT_ID`/`CLIENT_SECRET` после регистрации приложения ⏳
3. **RD-603** — Выпустить TLS через `certbot` ✅ (`https://pmo.russaldi.com`)
4. **RD-604** — Обновить локальный `.env.webhooks` под новый VPS ✅ (`5.42.119.99`, `https://pmo.russaldi.com`)
5. **RD-605** — Прогнать `verify-sync.sh`, зафиксировать статус ✅

Подробно: `docs/VPS_POST_SETUP_TASKS.md`.

## Статус в системах
- **Репозиторий**: `docs/ROADMAP_TASKS.json`, `docs/ROADMAP_EXECUTION_STATUS.json`, `.agent/context/bitrix-task-map.json` консистентны (31/31/31).
- **Bitrix24**: `sync-status --sync-kanban --apply` выполнен; статусы и канбан приведены к источнику из репозитория.

## Фактический результат текущей сессии
- Новый VPS `5.42.119.99` полностью инициализирован: Docker, compose v2, nginx, certbot, firewall, `deploy` user.
- Развернут стек приложения в `/opt/b24-ai-starter`, настроены сервисы `b24-ai-starter` и `b24-webhook`.
- Выпущен TLS-сертификат для `pmo.russaldi.com`; публичный URL: `https://pmo.russaldi.com`.
- Автодеплойный endpoint поднят: `POST /deploy-webhook`, проверен вручную (unsigned=401, signed ping=200, signed push=200).
- Локальная проверка деплоя успешна: `./scripts/vps/verify-sync.sh` => `OK: VPS deploy is synchronized`.

## После завершения текущего шага
1) Зарегистрировать новое Bitrix24-приложение для домена `https://pmo.russaldi.com` и получить `CLIENT_ID`/`CLIENT_SECRET`.
2) Прописать эти значения в `/opt/b24-ai-starter/.env` и перезапустить `b24-ai-starter`.
3) Привязать GitHub webhook репозитория к `https://pmo.russaldi.com/deploy-webhook` с текущим секретом из `/etc/b24/webhook.env` (серверная часть уже готова и проверена).
4) Только после этого переходить к следующей продуктовой задаче (RD-101 или по приоритету).

## Дисциплина контекста
- План и решения в `.agent/`; в чате — краткие отсылки.
