# Agent Workflows

## Workflow A: Feature Delivery
1. Analyze requirement.
2. Activate mandatory context baseline skills: `context-engineering-collection`, `context-fundamentals`, `context-optimization`.
3. Activate stack skills (`navigate`, `develop-*`, `implement-b24-features` as needed; `bitrix24-project-ops` when task tracking is involved).
4. Draft plan in `.agent/plans/current-plan.md`.
5. Implement backend + frontend slices.
6. Keep Bitrix24 task tree in sync (`эпик -> подзадачи -> вложенные подзадачи`) and gantt links for sequence/cross-epic dependencies.
7. Enforce naming hierarchy:
   - Epic number `N`: `Эпик N. ...`
   - First-level tasks: `Задача N.1`, `Задача N.2`
   - Nested tasks: `Задача N.1.1`, `Задача N.1.2`, etc.
8. Move active task status in Bitrix24 and kanban (`В работе` -> `На тестировании` -> `Сделаны`) and mirror the same in repository status file.
9. При завершении задачи записать `Результат задачи` в Bitrix24: что сделано + ссылка на коммит.
10. Для базовых задач (эпиков) включить автозакрытие при закрытии подзадач; после фактического закрытия добавить в название `Завершена`.
11. Validate endpoint/UI behavior.
12. Record results in artifact files.
13. After `git push`, run VPS sync check: `./scripts/vps/verify-sync.sh`.

## Workflow B: Long-Running/Complex Task
1. Activate mandatory baseline: `context-engineering-collection`, `context-fundamentals`, `context-optimization`.
2. Add `filesystem-context`.
3. Persist intermediate outputs to `.agent/context/`.
4. If context load increases, activate `context-compression`.
5. If task decomposition is large, activate `multi-agent-patterns`.
6. Validate with `evaluation` rubric.

## Workflow C: Quality/Regression Review
1. Activate `evaluation`.
2. Run checks against functional rubric.
3. If subjective quality ambiguity is high, use `advanced-evaluation`.
4. Log final judgment and unresolved risks.
