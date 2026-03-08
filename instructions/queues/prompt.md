# Промпт для AI-агента: настройка RabbitMQ (Python стек)

## Контекст
- Репозиторий: `b24-ai-starter`
- Активный стек: `frontend + python`
- Цель: включить и настроить RabbitMQ для фоновых задач (Celery workers)

## Задачи для агента
1. Проверить `.env` на `ENABLE_RABBITMQ=1`.
2. Проверить `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_PREFETCH`, `RABBITMQ_DSN`.
3. Запустить/остановить брокер:
   - `make queue-up`
   - `make queue-down`
4. Проверить статус контейнера `rabbitmq` через `docker compose ps`.
5. Подсказать интеграцию Python воркеров по `instructions/queues/python.md`.

## Важные предупреждения
- После изменения `.env` перезапускайте стек.
- Для продакшена выносите Celery worker в отдельный сервис.
- Не храните секреты брокера в репозитории.
