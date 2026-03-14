# Центральный узел знаний: Python + Frontend для Bitrix24

## Назначение
Этот файл — единая точка входа для разработки в текущем репозитории.
Актуальный стек: `frontend (Nuxt 3 + B24 UI/JS SDK)` + `backend Python (Django + b24pysdk)`.

## Окружение и конфигурация (обязательно для агента)
- **Единый источник правды по env и скриптам**: `instructions/env-and-config.md`
- Там: где лежат настройки (в репозитории нет папки `env`, только корневые `.env*`), какие переменные нужны для VPS verify и Bitrix24 sync, как устроены backend/frontend и roadmap-артефакты. Использовать при любых вопросах по конфигу, деплою и скриптам.

## Что использовать в первую очередь
- Frontend: `instructions/front/knowledge.md`
- Python backend: `instructions/python/knowledge.md`
- Bitrix24 platform:
  - `instructions/bitrix24/widget.md`
  - `instructions/bitrix24/crm-robot.md`

## Поддерживаемые направления
- UI на компонентах `@bitrix24/b24ui-nuxt` (префикс `B24*`)
- Работа с Bitrix24 через JS SDK на фронте
- API и бизнес-логика в Django
- Очереди (опционально): RabbitMQ + Celery

## Инструкции по очередям (если нужны)
- `instructions/queues/server.md`
- `instructions/queues/python.md`
- `instructions/queues/prompt.md`

## Версионирование проекта
- `instructions/versioning/create-version-prompt.md`

## Быстрый рабочий процесс
1. Реализовать UI/страницы во `frontend/app` (`*.client.vue`).
2. Добавить/изменить API в `backends/python/api/main/views.py` и сервисной логике.
3. Проверить интеграцию с Bitrix24 (install/getToken/widgets/events).
4. Прогнать проверки (минимум lint/security по задаче).
5. Для roadmap-задач: синхронизировать Bitrix24 статусы и канбан через `scripts/bitrix24/roadmap_sync.py`.
6. Для завершенных roadmap-задач: фиксировать `Результат задачи` (что сделано + commit URL) и синхронизировать закрытие эпиков.
7. После `git push`: выполнить `./scripts/vps/verify-sync.sh`.

## Принципы
- Не использовать удалённый в этом репозитории PHP-стек и связанные инструкции.
- Для Bitrix24 API обращаться к официальной документации только по необходимости.
- Приоритет источников: код репозитория -> локальные инструкции -> официальные docs.

## Архитектура работы агентов
- Базовая архитектура: `instructions/agents/knowledge.md`
- Матрица активации скиллов: `instructions/agents/skill-activation-map.md`
- Стандартные workflow: `instructions/agents/workflows.md`
- Операционные артефакты состояния: `.agent/context/*`, `.agent/plans/*`, `.agent/evaluation/*`
- Отдельный skill для Bitrix24 task ops: `.cursor/skills/bitrix24-project-ops/SKILL.md` (и зеркально в `.claude/skills/`).

## Краткий контекст для агента
- **Конфиг**: только корневые файлы `.env`, `.env.example`, `.env.webhooks`, `.env.webhooks.example`; папки env нет.
- **VPS verify**: переменные `VPS_DEPLOY_HOST`, `VPS_HEALTH_URL` (и опционально `VPS_DEPLOY_USER`, `VPS_APP_PATH`) — в `.env` или `.env.webhooks`; при ошибке парсинга `.env` скрипт подхватывает из `.env.webhooks`. После каждого push — `./scripts/vps/verify-sync.sh` при настроенных переменных.
- **Bitrix24 sync**: `B24_WEBHOOK_URL` (и при необходимости `B24_PROJECT_GROUP_ID`) — в `.env` или `.env.webhooks`; скрипт `scripts/bitrix24/roadmap_sync.py` сам читает оба файла. Источник статусов — `docs/ROADMAP_EXECUTION_STATUS.json`; маппинг — `.agent/context/bitrix-task-map.json`.
- **Код**: backend по модулям в `backends/python/api/main/features/`, frontend в `frontend/app/` (pages, stores, features/pmo). Подробно — `docs/BACKEND_CODE_STRUCTURE.md`, `docs/FRONTEND_CODE_STRUCTURE.md` и `instructions/env-and-config.md`.
