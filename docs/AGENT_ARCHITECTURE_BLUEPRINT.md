# Unified Agent Architecture Blueprint

This project uses a hybrid agent architecture:
- Domain layer: Bitrix24 + PMO Hub stack skills
- Context-engineering layer: imported full skill set from Agent-Skills-for-Context-Engineering
- Execution layer: filesystem-backed orchestration artifacts in `.agent/`

Primary references:
- `instructions/agents/knowledge.md`
- `instructions/agents/skill-activation-map.md`
- `instructions/agents/workflows.md`

The architecture is intentionally progressive-disclosure and file-centric:
- minimal skills active by default,
- state persisted in deterministic artifacts,
- optional escalation to multi-agent/evaluation patterns when complexity rises.

Operational guardrails:
- roadmap/task execution state is mirrored in repository and Bitrix24;
- Bitrix24 task cards are moved across kanban stages based on workflow status;
- after each push, VPS deployment sync (`HEAD/local/origin`) and health are verified.
