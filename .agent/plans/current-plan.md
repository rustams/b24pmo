# Current Plan

## Активная задача
**Выполняется:** стандартизация обязательных context-skills + принудительная иерархическая нумерация эпиков/задач (`N`, `N.1`, `N.1.1`) в документации и Bitrix24.

## План выполнения текущей задачи
1. Обновить правила проекта и гайды: сделать `context-engineering-collection`, `context-fundamentals`, `context-optimization` обязательными.
2. Обновить workflow/skills с правилом нумерации задач по эпику (`N.1`, `N.1.1`).
3. Обновить логику генерации заголовков в `roadmap_sync.py`.
4. Применить `sync-epic-structure --apply` и проверить названия задач в Bitrix24.
5. Синхронизировать `.agent`-артефакты, выполнить self-check, commit + push.

## Цепочка задач VPS post-setup (последовательно)
1. **RD-601** — Проверить SSH (deploy@IP, root@IP) и доступность сервера ✅
2. **RD-602** — Прописать `CLIENT_ID`/`CLIENT_SECRET` после регистрации приложения ✅
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
- На VPS в `.env` внесены рабочие `CLIENT_ID`/`CLIENT_SECRET` для нового приложения; сервис перезапущен.
- Подтверждена запись установки в БД (`bitrix24account` с `domain_url=rgflow.bitrix24.ru`, токены сохранены).
- Белые экраны на фронтенде устранены: добавлен demo-fallback режим для страниц/модулей вне B24 iframe.

## Следующий шаг
Завершить фиксацию изменений коммитом и пушем, затем продолжить продуктовый roadmap (RD-101+).

## Дисциплина контекста
- План и решения в `.agent/`; в чате — краткие отсылки.
