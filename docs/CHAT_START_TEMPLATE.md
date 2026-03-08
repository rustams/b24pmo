# Chat Start Template (b24pmo)

Скопируй блок ниже как первое сообщение в новом чате.

```text
Работаем в репозитории b24pmo.
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
1) Активируй минимально нужный набор skills из .cursor/skills/.claude/skills.
2) Веди plan в .agent/plans/current-plan.md.
3) Все ключевые решения пиши в .agent/context/decision-log.jsonl.
4) Обновляй .agent/context/session-summary.md по ходу работы.
5) После выполнения задачи обнови artifact-index и сделай self-check по .agent/evaluation/rubric.md.
6) Если меняешь код — доводи до готового результата (изменения + проверка + коммит/пуш по моей команде).
7) Для задач roadmap синхронизируй Bitrix24: статус + перемещение по канбану через webhook.
8) Названия задач в Bitrix24: сначала человекопонятный текст, затем `[RD-xxx][EPIC-xxx]`; описания — на русском.
9) После каждого push обязательно проверяй синхронизацию деплоя на VPS (`./scripts/vps/verify-sync.sh`).
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
