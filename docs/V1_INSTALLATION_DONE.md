# V1: Успешная установка и страница настроек

## Что реализовано
- Приложение сохраняет инсталляцию в БД при вызове `/api/install`.
- Добавлен endpoint `/api/pmo/installation-context` для получения данных установки из БД.
- Добавлена страница настроек `/settings`.

## Что видит пользователь
- Сообщение: «Поздравляю, установка прошла успешно. Это страница настройки приложения.»
- Ниже выводится структура данных установки, считанная из нашей БД.

## Основные файлы
- Backend:
  - `backends/python/api/main/features/installer/services.py`
  - `backends/python/api/main/features/installer/views.py`
  - `backends/python/api/main/urls.py`
- Frontend:
  - `frontend/app/pages/settings.client.vue`
  - `frontend/app/stores/api.ts`
  - `frontend/app/pages/install.client.vue`

## Критерий готовности V1
- После установки запись о портале создаётся/обновляется в БД.
- Страница настроек открывается в приложении и отображает данные установки из БД.
