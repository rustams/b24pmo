# Центральный узел знаний: Python + Frontend для Bitrix24

## Назначение
Этот файл — единая точка входа для разработки в текущем репозитории.
Актуальный стек: `frontend (Nuxt 3 + B24 UI/JS SDK)` + `backend Python (Django + b24pysdk)`.

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

## Принципы
- Не использовать удалённый в этом репозитории PHP-стек и связанные инструкции.
- Для Bitrix24 API обращаться к официальной документации только по необходимости.
- Приоритет источников: код репозитория -> локальные инструкции -> официальные docs.

## Архитектура работы агентов
- Базовая архитектура: `instructions/agents/knowledge.md`
- Матрица активации скиллов: `instructions/agents/skill-activation-map.md`
- Стандартные workflow: `instructions/agents/workflows.md`
- Операционные артефакты состояния: `.agent/context/*`, `.agent/plans/*`, `.agent/evaluation/*`
