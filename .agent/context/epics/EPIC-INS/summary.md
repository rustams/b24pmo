# EPIC-INS Summary

## Scope
- Epic: `EPIC-INS`
- Completed task: `RD-101`
- Current tasks in progress: `RD-102`, `RD-103`

## Dependency Gate
- `RD-101` depends_on `RD-002`: `RD-002=5` -> unblocked.
- `RD-102`/`RD-103` depend_on `RD-101`: после перевода `RD-101=5` блокеры сняты.
- `RD-104` remains blocked by `RD-102` + `RD-103`.

## What Was Implemented
- `RD-101` closed:
  - зафиксирован versioned контракт установщика;
  - добавлена идемпотентность `POST /api/install`;
  - закреплена модель хранения маппингов в `status_code.mapping`.
- Старт `RD-102`:
  - backend endpoints `GET /api/pmo/installer/mapping` и `POST /api/pmo/installer/mapping/save`;
  - frontend каркас на `settings` для редактирования JSON маппинга и сохранения в backend.
- Старт `RD-103`:
  - backend endpoint `GET /api/pmo/installer/scope-check` (required/current/missing scopes + admin check + readiness);
  - вывод результата scope-check в UI `settings`.
- Roadmap sync:
  - `RD-101` -> `DONE (5)`;
  - `RD-102` и `RD-103` -> `IN_PROGRESS (3)`;
  - sync-status + kanban applied в Bitrix24.

## Validation
- `python3 -m compileall backends/python/api/main/features/installer/services.py backends/python/api/main/features/installer/views.py backends/python/api/main/urls.py` passed.
- Lints для backend/frontend измененных файлов: ошибок нет.

## Risks / Follow-ups
- Текущий UI маппинга использует JSON-редактор; требуется UX-полировка для бизнес-пользователя.
- Нужна валидация полей маппинга на уровне схемы перед переводом `RD-102` в `TESTING`.

## UX Fix Iteration (user-reported)
- Убрана первая ошибка на стартовой странице:
  - удален блок `BackendStatus` с красной ошибкой;
  - добавлена одна целевая кнопка `Настроить приложение`.
- Улучшена стабильность открытия `Settings`:
  - загрузка данных переведена на `Promise.allSettled`;
  - для сбоев backend добавлены безопасные fallback-объекты;
  - в `apiStore` включен demo fallback даже при наличии JWT, если сеть/API недоступны.
- Итог: пользователь попадает из главной страницы напрямую в рабочий экран настройки RD-102 без блокирующей ошибки.

## Working Interface Iteration (RD-102)
- JSON-редактор заменен на рабочую форму:
  - отдельные строки для Smart Processes (`key + entityTypeId`);
  - отдельные строки для Lists (`key + iblockId`);
  - добавление/удаление строк через UI-кнопки.
- Добавлена валидация:
  - `entityTypeId` и `iblockId` должны быть числовыми;
  - ошибки валидации выводятся до отправки.
- Добавлены операционные действия:
  - `Сохранить настройки` (persist в backend);
  - `Обновить данные` (reload актуального состояния).
- Debug-информация убрана из основного потока в `details`, чтобы интерфейс оставался рабочим и чистым для пользователя.

## RD-102 Scenario Pivot (requested)
- Выбор Smart Process/List из логики убран.
- Новый flow в `Settings`:
  1. Пользователь вводит название цифрового рабочего места и нажимает `Продолжить`.
  2. Выполняется `crm.automatedsolution.add`, показывается progress bar, затем сообщение об успехе и ссылка на рабочее место.
  3. Пользователь нажимает `Продолжить` для создания смарт-процесса `Цели`.
  4. Выполняется `crm.type.add` (привязка к созданному рабочему месту), показывается progress bar, затем сообщение об успехе и ссылка на процесс.
- Методическая база проверена через MCP (`bitrix-method-details`):
  - `crm.automatedsolution.add`
  - `crm.type.add`
- Roadmap metadata обновлена:
  - `docs/ROADMAP_TASKS.json` для `RD-102` (title + description);
  - `sync-metadata --apply` выполнен в Bitrix24.

## RD-102 Demo Acceptance
- Пользователь подтвердил, что в демо-режиме весь сценарий проходит без ошибок:
  - шаг создания цифрового рабочего места;
  - шаг создания смарт-процесса `Цели`;
  - прогресс и сообщения отображаются корректно.
- `RD-102` переведена в `TESTING` (`STATUS=4`) в `docs/ROADMAP_EXECUTION_STATUS.json`.
- Выполнена синхронизация статусов и канбана в Bitrix24 (`sync-status --sync-kanban --apply`).

## RD-103 Progress (permissions guidance)
- Расширен backend-ответ `installer/scope-check`:
  - добавлены `scope_recommendations` с объяснением по каждому недостающему разрешению;
  - добавлены `next_steps` для администратора.
- Обновлен UI шага 1 в `Settings`:
  - показ обязательных/текущих/недостающих разрешений;
  - блок `Что нужно исправить` с практическими подсказками;
  - блок `Дальнейшие действия` с последовательными шагами.

## RD-107 (subtask of RD-102): installer setup-state persistence
- Добавлена отдельная подзадача `RD-107` как дочерняя к `RD-102` в `docs/ROADMAP_TASKS.json`.
- Реализован backend API для состояния мастера установки:
  - `GET /api/pmo/installer/setup-state`;
  - `POST /api/pmo/installer/setup-state/save`.
- Состояние теперь хранится в `application_installation.status_code.setup_state`:
  - текущий шаг (`current_step`);
  - данные созданного DWS (`workplace`);
  - данные созданного СП `Цели` (`goals_process`);
  - список завершенных шагов (`completed_steps`).
- UI `settings` теперь:
  - восстанавливает сохраненное состояние при открытии страницы;
  - сохраняет прогресс после успешного создания DWS и СП `Цели`.
- Совместимость сохранена: при повторном `POST /api/install` ранее сохраненные `mapping` и `setup_state` не теряются.
- Задача закрыта:
  - `RD-107` переведена в `DONE (5)` в `docs/ROADMAP_EXECUTION_STATUS.json`;
  - commit/push: `e470979a0bcc44e5ab9fa1f44f58c4c70654767c` (`master`).

## RD-102 Follow-up: Goals fields + card configuration
- В мастер `Settings` добавлены новые шаги после создания СП `Цели`:
  1. Создание полей СП `Цели` по `docs/GOALS.md` (кнопка `Продолжить`, progress bar, сообщение об успехе).
  2. Настройка карточки цели через:
     - `crm.item.details.configuration.reset`
     - `crm.item.details.configuration.get`
     - `crm.item.details.configuration.set`
     - `crm.item.details.configuration.forceCommonScopeForAll`
- Для кодов полей используется только суффикс начиная с `GOAL`/`GAOL` (без `UF_CRM_...` префикса).
- Финальное состояние сохраняется в `setup_state`:
  - `goals_fields` (созданные поля, `field_id`, `codes_added`);
  - `goals_card_configuration` (статус, признак common scope, тех.детали).

## RD-102 Expansion: Workgroup + Lists + Knowledge Base (RD-108/109/110)
- Roadmap расширен тремя подзадачами под `RD-102`:
  - `RD-108` — рабочая группа + справочники;
  - `RD-109` — база знаний и привязка к группе;
  - `RD-110` — UI-прогресс и финальная верификация.
- Backend `setup_state` расширен новыми контейнерами:
  - `workgroup` (id/name/link/status/tools_updated),
  - `reference_lists` (group_id/lists/field_bindings/status),
  - `knowledge_base` (site_id/link/binding_status/changes_log/status).
- Frontend мастер перестроен в последовательность 1..9:
  1) scope-check, 2) DWS, 3) Goals SP, 4) workgroup, 5) lists, 6) Goals fields (через `userfieldconfig.add`), 7) card config, 8) knowledge base, 9) verification.
- Поля Goals переведены с `crm.item.userfield.*` на подтвержденный MCP метод `userfieldconfig.*`:
  - создание через `userfieldconfig.add` (`moduleId=crm`, `entityId=CRM_<entityTypeId>`),
  - проверка через `userfieldconfig.list`.
- Для полей типа "Привязка к элементам инф. блоков" добавлена реальная привязка к ID созданных списков (`IBLOCK_ID` в `settings` поля).
- Bitrix24 sync выполнен:
  - `sync-metadata --apply`;
  - `create-missing --apply` (созданы `RD-107/108/109/110` в map-файле);
  - `sync-epic-structure --apply` (подзадачи привязаны к `RD-102`);
  - `sync-status --apply` (статусы применены).
