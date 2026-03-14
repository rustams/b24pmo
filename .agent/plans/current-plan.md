# Current Plan

## Активная задача
**EPIC-INS / RD-102 + RD-103:** старт реализации UI маппинга Smart Processes/Lists и проверки scope/прав.

## Dependency Gate
1. `RD-101` зависит от `RD-002`; `RD-002=5`, задача завершена.
2. Для `RD-102` и `RD-103` блокер `depends_on=RD-101` снят (`RD-101=5`).
3. `RD-104` не запускать до завершения `RD-102` и `RD-103`.

## План выполнения RD-102 / RD-103
1. Обновить roadmap-статусы: `RD-101 -> DONE`, `RD-102/RD-103 -> IN_PROGRESS`. ✅
2. Синхронизировать статус + канбан в Bitrix24 через webhook. ✅
3. Реализовать backend endpoints для маппинга (`GET/POST`) и scope-check (`GET`). ✅
4. Реализовать frontend каркас на `settings` для редактирования маппинга и отображения scope-check. ✅
5. Убрать первую ошибку на стартовой странице и оставить прямой CTA в flow настройки. ✅
6. Подготовить следующую итерацию: валидации, UX-полировка и критерии приемки RD-102/RD-103. ⏳
7. Обновить epic-local/global контекст и handoff. ✅

## Ограничения по эпику
- Работать только в рамках `EPIC-INS`.
- `RD-104` не начинать до завершения `RD-102` и `RD-103`.
- Bitrix24 sync выполнять только если изменяются roadmap-статусы/канбан.

## Закрытие EPIC-FND (выполнено)
1. `RD-004` переведена в `DONE` в `docs/ROADMAP_EXECUTION_STATUS.json`. ✅
2. Выполнен `sync-status --sync-kanban --apply` для фиксации статуса в Bitrix24. ✅
3. Выполнен `sync-epic-completion --apply`; `EPIC-FND` закрыт в Bitrix24. ✅
4. Epic-local артефакты `EPIC-FND` обновлены (`summary/decisions/artifacts/handoff`). ✅
