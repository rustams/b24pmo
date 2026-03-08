# Центральный узел знаний: PHP + Frontend для Bitrix24

## Назначение
Этот файл — единая точка входа для разработки в текущем репозитории.
Актуальный стек: `frontend (Nuxt 3 + B24 UI/JS SDK)` + `backend PHP (Symfony + b24phpsdk)`.

## Что использовать в первую очередь
- Frontend: `instructions/front/knowledge.md`
- PHP backend: `instructions/php/knowledge.md`
- Bitrix24 platform:
  - `instructions/bitrix24/widget.md`
  - `instructions/bitrix24/crm-robot.md`

## Поддерживаемые направления
- UI на компонентах `@bitrix24/b24ui-nuxt` (префикс `B24*`)
- Работа с Bitrix24 через JS SDK на фронте
- API и бизнес-логика в PHP/Symfony
- Очереди (опционально): RabbitMQ + Symfony Messenger

## Инструкции по очередям (если нужны)
- `instructions/queues/server.md`
- `instructions/queues/php.md`
- `instructions/queues/prompt.md`

## Версионирование проекта
- `instructions/versioning/create-version-prompt.md`

## Быстрый рабочий процесс
1. Реализовать UI/страницы во `frontend/app` (`*.client.vue`).
2. Добавить/изменить API в `backends/php/src/Controller` и сервисах.
3. Проверить интеграцию с Bitrix24 (install/getToken/widgets/events).
4. Прогнать проверки (минимум lint/security по задаче).

## Принципы
- Не использовать удалённые в этом репозитории backend-стеки и связанные инструкции.
- Для Bitrix24 API обращаться к официальной документации только по необходимости.
- Приоритет источников: код репозитория -> локальные инструкции -> официальные docs.
