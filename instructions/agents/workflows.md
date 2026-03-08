# Agent Workflows

## Workflow A: Feature Delivery
1. Analyze requirement.
2. Activate stack skills (`navigate`, `develop-*`, `implement-b24-features` as needed; `bitrix24-project-ops` when task tracking is involved).
3. Draft plan in `.agent/plans/current-plan.md`.
4. Implement backend + frontend slices.
5. Move active task status in Bitrix24 and kanban (`В работе` -> `На тестировании` -> `Сделаны`) and mirror the same in repository status file.
6. Validate endpoint/UI behavior.
7. Record results in artifact files.
8. After `git push`, run VPS sync check: `./scripts/vps/verify-sync.sh`.

## Workflow B: Long-Running/Complex Task
1. Activate `context-fundamentals` + `filesystem-context`.
2. Persist intermediate outputs to `.agent/context/`.
3. If context load increases, activate `context-compression`.
4. If task decomposition is large, activate `multi-agent-patterns`.
5. Validate with `evaluation` rubric.

## Workflow C: Quality/Regression Review
1. Activate `evaluation`.
2. Run checks against functional rubric.
3. If subjective quality ambiguity is high, use `advanced-evaluation`.
4. Log final judgment and unresolved risks.
