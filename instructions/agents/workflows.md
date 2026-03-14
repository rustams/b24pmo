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

## Workflow D: Supervisor + Epic Agents
1. Supervisor defines epic queue and execution order.
2. Each epic is assigned to a dedicated agent/session (`EPIC-FND`, `EPIC-INS`, `EPIC-CORE`, `EPIC-OPS`, `EPIC-SEC`, `EPIC-V11`).
3. Epic agent works only in epic scope and writes outputs to `.agent/context/epics/<EPIC>/`.
4. On each meaningful step, epic agent must update:
   - `.agent/context/epics/<EPIC>/summary.md`
   - `.agent/context/epics/<EPIC>/decisions.jsonl`
   - `.agent/context/epics/<EPIC>/artifacts.jsonl`
   - `.agent/context/epics/<EPIC>/handoff.json`
5. Supervisor merges epic outputs into shared memory:
   - `.agent/context/session-summary.md`
   - `.agent/context/decision-log.jsonl`
   - `.agent/context/artifact-index.jsonl`
   - `.agent/plans/current-plan.md`
6. Bitrix24 sync is executed after epic-agent step when relevant:
   - `sync-epic-structure --apply`
   - `sync-status --sync-kanban --apply` (if statuses changed)
7. Commit policy:
   - administrative/intermediate commits are allowed without VPS verify
   - run `./scripts/vps/verify-sync.sh` only after large integration commit or functional completion milestone.
