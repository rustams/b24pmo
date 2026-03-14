# Chat Start Template (b24pmo)

Скопируй блок ниже как первое сообщение в новом чате, чтобы агент быстро вошел в контекст и сразу работал по стандарту проекта.

```text
Работаем в репозитории b24pmo.
Цель старта: быстро синхронизировать контекст, активировать обязательные skills и перейти к реализации без лишних уточнений.
Обязательно загрузи и используй:
- instructions/knowledge.md
- instructions/agents/knowledge.md
- instructions/agents/skill-activation-map.md
- instructions/agents/workflows.md
- .agent/context/session-summary.md
- .agent/context/decision-log.jsonl
- .agent/context/artifact-index.jsonl
- .agent/plans/current-plan.md
- .agent/evaluation/rubric.md

Правила:
1) Всегда активируй обязательные skills: `context-engineering-collection`, `context-fundamentals`, `context-optimization`; затем добавляй минимально нужный набор из .cursor/skills/.claude/skills.
2) Веди plan в .agent/plans/current-plan.md.
3) Все ключевые решения пиши в .agent/context/decision-log.jsonl.
4) Обновляй .agent/context/session-summary.md по ходу работы.
5) После выполнения задачи обнови artifact-index и сделай self-check по .agent/evaluation/rubric.md.
6) Если меняешь код — доводи до готового результата (изменения + проверка + коммит/пуш по моей команде).
7) Для задач roadmap синхронизируй Bitrix24: статус + перемещение по канбану через webhook.
8) Названия задач в Bitrix24: сначала человекопонятный текст, затем `[RD-xxx][EPIC-xxx]`; описания — на русском.
9) Нумерация обязательна: эпик `Эпик N. ...`; задачи эпика N — `Задача N.1`, `Задача N.2`; вложенные — `Задача N.1.1`, `Задача N.1.2` и т.д.
10) В Bitrix24 соблюдай структуру: эпик (базовая задача) -> подзадачи -> вложенные подзадачи; связи по Ганту обязательны.
11) После каждого push обязательно проверяй синхронизацию деплоя на VPS (`./scripts/vps/verify-sync.sh`).
12) При завершении задачи заполняй `Результат задачи` (что сделано + ссылка на commit).
13) Для эпиков включай автозакрытие основной задачи при закрытии подзадач; закрытый эпик помечай словом `Завершена` в названии.
14) Мультиагентный режим: один эпик = один агент; каждый epic-agent пишет результаты в `.agent/context/epics/<EPIC-XXX>/`, а supervisor синхронизирует общий контекст.
15) Dependency gate обязателен: если зависимость (в том числе cross-epic) не завершена, задача переводится в `blocked`; реализацию начинать нельзя до разблокировки и обновления контекста.

Формат первого ответа агента в чате:
- Active Skills (какие активированы и почему)
- Plan (3-7 шагов)
- Start implementation (без ожидания, если нет блокеров)
```

## Второе сообщение (постановка задачи)

```text
Задача: <что сделать>.
Ограничения: <что нельзя/что важно>.
Definition of Done: <критерии готовности>.
```

## Короткие управляющие команды

```text
Синхронизируй контекст и покажи активные skills для этой задачи.
Обнови plan и начинай реализацию.
Сделай промежуточный статус: что готово/что осталось/риски.
Закрой задачу: self-check по rubric + список измененных файлов.
Сделай коммит и push.
```

## Команда для epic-agent режима

```text
Работаем в режиме supervisor + epic agents.
Назначь отдельного агента на эпик <EPIC-XXX>.
Обновляй epic-local память в `.agent/context/epics/<EPIC-XXX>/`:
- summary.md
- decisions.jsonl
- artifacts.jsonl
- handoff.json
После каждого шага эпика синхронизируй общий контекст:
- .agent/context/session-summary.md
- .agent/context/decision-log.jsonl
- .agent/context/artifact-index.jsonl
- .agent/plans/current-plan.md
```

## Как запускать Supervisor

```text
Роль: Supervisor (оркестратор эпиков).
Цель: выбрать следующую задачу roadmap и назначить epic-agent.
Действия:
1) Проверь зависимости задачи (`depends_on` + cross-epic) в `docs/ROADMAP_TASKS.json` и `docs/ROADMAP_EXECUTION_STATUS.json`.
2) Если есть незавершенная зависимость — переведи задачу в `blocked`, обнови:
   - `.agent/context/epics/<EPIC-XXX>/handoff.json`
   - `.agent/context/session-summary.md`
   - `.agent/plans/current-plan.md`
3) Если блокеров нет — назначь epic-agent на `<EPIC-XXX>` с явным DoD и тест-критериями.
4) После шага epic-agent синхронизируй общий контекст:
   - `.agent/context/session-summary.md`
   - `.agent/context/decision-log.jsonl`
   - `.agent/context/artifact-index.jsonl`
   - `.agent/plans/current-plan.md`
5) При необходимости запусти Bitrix24 sync:
   - `sync-epic-structure --apply`
   - `sync-status --sync-kanban --apply`
```

## Как запускать Epic-Agent

```text
Роль: Epic-Agent для <EPIC-XXX>.
Ограничение: работай только в рамках задач этого эпика.
Порядок:
1) Подтверди dependency gate (нет незавершенных блокеров).
2) Выполни реализацию по шагам и фиксируй изменения.
3) Обновляй epic-local память:
   - `.agent/context/epics/<EPIC-XXX>/summary.md`
   - `.agent/context/epics/<EPIC-XXX>/decisions.jsonl`
   - `.agent/context/epics/<EPIC-XXX>/artifacts.jsonl`
   - `.agent/context/epics/<EPIC-XXX>/handoff.json`
4) В handoff.json передай:
   - `completed_tasks`, `changed_files`, `open_risks`, `next_actions`, `bitrix_sync`.
5) Передай результат Supervisor-агенту для merge в общий контекст.
```

## Готовые команды запуска

```text
Запусти supervisor-цикл для EPIC-INS по модели из docs/EPIC_AGENT_OPERATING_MODEL.md.
```

```text
Запусти epic-agent для EPIC-INS, соблюдай dependency gate и обновляй `.agent/context/epics/EPIC-INS/*`.
```

## Быстрый шаблон задачи (рекомендуется)

```text
Контекст: <где сейчас проблема / какой модуль>.
Задача: <конкретный результат>.
Ограничения: <что нельзя ломать / важные условия>.
Проверка: <как понять, что готово>.
Нужно ли: commit / push / sync Bitrix24 / verify-sync.
```
