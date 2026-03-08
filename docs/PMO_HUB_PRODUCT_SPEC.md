# PMO Hub Product Specification (Adapted for This Repository)

Дата: 2026-03-08
Статус: Draft v1.0
Целевой стек: `frontend (Nuxt 3)` + `backend (Python/Django)` + `PostgreSQL` + `Redis/RabbitMQ workers`

## 1. Product Summary
PMO Hub расширяет Bitrix24 до уровня проектного офиса: стратегия (Goals/OKR/KPI), инициативы, портфели, программы, проекты, ресурсы, бюджеты, риски, встречи и управленческая отчётность.

В рамках этого репозитория принимается архитектура:
- Frontend: Nuxt 3 + Bitrix24 UI Kit + Bitrix24 JS SDK.
- Backend: Django + b24pysdk + DRF-style API patterns.
- Storage:
  - Bitrix24 Smart Processes: стратегическое ядро.
  - Bitrix24 Lists: массовые операционные записи.
  - PostgreSQL приложения: агрегаты, токены, sync, audit, jobs.
- Async: Celery workers (Redis/RabbitMQ брокер).

## 2. Why Python Backend (Decision)
Решение: использовать Python backend как основной.

Причины:
- Быстрое создание админ-интерфейса и операционного контроля через Django Admin.
- Удобная реализация ETL/sync/фоновых расчётов (Celery ecosystem).
- Более низкая стоимость реализации аналитики/AI-пайплайнов (риски, классификация, прогнозы).
- Простая масштабируемость backend+workers независимо от UI.

## 3. Goals and KPI
- Снижение времени планирования ресурсов: 4ч -> 1ч/нед.
- Снижение ручного сбора статусов: -90%.
- План/факт бюджета: отклонение <= 10%.
- SLA backend+workers: 99.5%.
- P95 latency ключевых API: < 2s.

## 4. RBAC Model
Bitrix права + внутренний RBAC по `portal_id`.

Роли:
- Owner/CEO
- Director
- Portfolio Manager
- Program Manager
- Project Manager
- Team Member
- Finance Controller
- HR/Resource Manager
- CRM Admin

Минимум MVP:
- Owner, Project Manager, Team Member, Finance, HR.

## 5. Entity Storage Strategy
Smart Processes:
- Goals, Initiatives, Portfolios, Programs, Projects.

Lists:
- Milestones, Risks, BudgetTransactions, ResourceAllocations, Meetings, Roles, Skills.

App DB (PostgreSQL):
- app_config
- portal_auth
- resource_capacity_cache
- sync_log
- ai_risk_analysis
- audit_log
- jobs_queue, jobs_history

## 6. Installer / Onboarding (Idempotent)
1. OAuth install -> сохранить `portal_id`, tokens.
2. Проверка/создание/маппинг Smart Processes и Lists.
3. Проверка scope и прав администратора.
4. Добавление обязательных task userfields (если отсутствуют).
5. Первичная синхронизация users/tasks/calendar/projects.
6. Заполнение `resource_capacity_cache` на 90 дней.
7. Сохранение mapping в `app_config`.

Все шаги логируются в `sync_log`.

## 7. REST Integration Baseline
Основные методы:
- CRM: `crm.item.get|add|update|list`
- Lists: `lists.element.get|add|update|list`
- Tasks: `tasks.task.get|list`, `task.item.update`, `task.elapseditem.get`
- Users: `user.get|list`
- Groups: `sonet_group.get|add`
- Calendar: `calendar.accessibility.get`, `calendar.event.get`
- Disk: `disk.file.upload|get`

Стратегия вызовов:
- Batch до 50 операций.
- Per-portal limiter: 2-3 req/sec для критичных путей.
- Retry с backoff (до 3 попыток).
- Heavy operations -> очередь.

## 8. Event and Sync Model
Webhook handlers:
- onCrmItemAdd/onCrmItemUpdate (Goals/Initiatives/Projects)
- onTaskAdd/onTaskUpdate/onTaskDelete
- onUserUpdate
- calendar updates (если доступны)

Workers:
- sync_resource_cache_worker
- ai_risk_worker
- bulk_recalc_worker
- file_cleanup_worker

## 9. Resource Planner Logic
Источники:
- List ResourceAllocations
- Tasks + elapsed
- Calendar absences
- Roles capacity

Дневной расчёт:
- capacity_hours
- planned_hours
- task_hours
- absence_flag
- effective_availability

Кэш:
`resource_capacity_cache(portal_id, user_id, date, capacity_hours, planned_hours, task_hours, absence_flag, computed_load_percent, updated_at)`

## 10. UI/Placement (For Current Nuxt Frontend)
Важно: в этом проекте frontend остаётся Nuxt 3 (не React).

Placements:
- CRM detail tabs для Project.
- Главные страницы PMO Hub (Strategy, Portfolio, Resource Planner, Budget Center).
- Интеграция с Task detail (поля milestone/risk).
- Пункт меню PMO Hub.

## 11. Security and Compliance
Scopes:
`crm`, `tasks`, `user`, `sonet`, `calendar`, `lists`, `disk`, `placement`, `event`, `bizproc`.

Требования:
- Минимизация PII в БД.
- Шифрование токенов и секретов.
- Audit trail (`audit_log`) и регламент retention.
- Uninstall flow с очисткой данных портала.

## 12. Non-Functional Requirements
- 20-50 одновременных пользователей на портал.
- До 500 порталов.
- До 50k API операций/сутки суммарно.
- Горизонтальное масштабирование API и workers отдельно.
- Наблюдаемость: metrics, traces, errors, queue lag.

## 13. MVP Scope (v1.0)
Обязательно:
1. Installer + mapping UI.
2. Goals/Initiatives/Projects (SP).
3. Milestones/Risks/ResourceAllocations/BudgetTransactions (Lists, базово).
4. PMO tab in Project card.
5. Resource timeline (view + create allocation).
6. Task -> milestone progress sync via webhooks.
7. PM dashboard.
8. Базовый RBAC.
9. Health checks + critical audit logs.

## 14. v1.1 / v2
v1.1:
- Budget plan/fact reports.
- Portfolio/CEO dashboards.
- MVP AI risk detector (keyword).
- Roles/skills matching.

v2:
- LLM risk analysis.
- Portfolio optimization.
- Cross-portal analytics.

## 15. Development Sequence (Repository-Level)
Phase 1: Foundation
- Restore Python backend as primary.
- Align docs/skills/config to python+frontend.
- Prepare installer domain model and migrations.

Phase 2: Core Model + Installer
- App config + portal auth + mapping UI.
- Smart Process/List bootstrap and mapping.

Phase 3: PMO Core Flows
- Goals/Initiatives/Projects API.
- Milestones/Risks/Allocations CRUD.
- Project PMO tab and timeline.

Phase 4: Sync + Workers
- Webhook endpoints.
- Resource cache recompute pipeline.
- Queue hardening/retry.

Phase 5: Product Hardening
- RBAC enforcement.
- Audit/compliance.
- Load tests and release checklist.

## 16. Definition of Done
- Unit tests >= 70% (business logic).
- Integration tests for install/mapping/webhooks/sync.
- UI acceptance for key user flows.
- Security checks and token handling review.
- Monitoring dashboards + alert rules configured.
- Admin/User operational docs complete.
