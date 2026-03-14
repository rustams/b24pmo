#!/usr/bin/env python3
"""Sync local roadmap tasks with Bitrix24 project tasks via incoming webhook.

Usage examples:
  python3 scripts/bitrix24/roadmap_sync.py create \
    --project-id 42 \
    --source docs/ROADMAP_TASKS.json \
    --output .agent/context/bitrix-task-map.json \
    --default-responsible-id 1 \
    --apply

  python3 scripts/bitrix24/roadmap_sync.py sync-status \
    --map-file .agent/context/bitrix-task-map.json \
    --status-file docs/ROADMAP_EXECUTION_STATUS.json \
    --sync-kanban \
    --kanban-entity-id 17 \
    --apply

Webhook is resolved from --webhook-url or env B24_WEBHOOK_URL (.env/.env.webhooks).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BITRIX_STATUS_ALIAS = {
    "NEW": 1,
    "PENDING": 2,
    "IN_PROGRESS": 3,
    "SUPPOSEDLY_COMPLETED": 4,
    "COMPLETED": 5,
    "DEFERRED": 6,
    "DECLINED": 7,
}

STATUS_TO_STAGE_TYPES = {
    1: ["NEW"],
    2: ["PROGRESS", "WORK"],
    3: ["WORK", "PROGRESS"],
    4: ["REVIEW"],
    5: ["FINISH"],
    6: ["WORK", "PROGRESS"],
    7: ["REVIEW", "WORK"],
}

STAGE_EPIC_MAP = {
    "Stage 0 - Foundation": "EPIC-FND Foundation & Delivery Ops",
    "Stage 1 - Installer": "EPIC-INS Installer & Mapping",
    "Stage 2 - Strategy & Delivery": "EPIC-CORE Strategy & Delivery Core",
    "Stage 3 - Operations Domains": "EPIC-OPS Resources/Risks/Budget/Meetings",
    "Stage 4 - RBAC & Hardening": "EPIC-SEC RBAC & Quality Hardening",
    "Stage 5 - v1.1": "EPIC-V11 Product Extensions",
}

EPIC_TITLES_RU = {
    "EPIC-FND": "Подготовка проекта и контроль поставки",
    "EPIC-INS": "Установка приложения и базовая настройка",
    "EPIC-CORE": "Ядро стратегии и проектной доставки",
    "EPIC-OPS": "Операционные домены PMO Hub",
    "EPIC-SEC": "RBAC и качество промышленной эксплуатации",
    "EPIC-V11": "Развитие версии v1.1",
}

EPIC_ORDER = {
    "EPIC-FND": 1,
    "EPIC-INS": 2,
    "EPIC-CORE": 3,
    "EPIC-OPS": 4,
    "EPIC-SEC": 5,
    "EPIC-V11": 6,
}


@dataclass
class RoadmapTask:
    key: str
    title: str
    description: str
    stage: str
    depends_on: list[str] = field(default_factory=list)
    parent: str | None = None
    tags: list[str] = field(default_factory=list)
    responsible_id: int | None = None
    status: str | int | None = None
    epic: str | None = None
    skills: list[str] = field(default_factory=list)
    technical_test: list[str] = field(default_factory=list)
    ui_test: list[str] = field(default_factory=list)
    done_definition: list[str] = field(default_factory=list)
    bitrix_task_id: int | None = None


@dataclass
class EpicTask:
    key: str
    code: str
    title: str
    description: str
    stage: str
    tags: list[str] = field(default_factory=list)
    bitrix_task_id: int | None = None


class BitrixWebhookClient:
    def __init__(self, webhook_url: str, timeout: int = 30) -> None:
        self.webhook_url = webhook_url.rstrip("/")
        self.timeout = timeout

    def call(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.webhook_url}/{method}.json"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {err.code} for {method}: {detail}") from err
        except urllib.error.URLError as err:
            raise RuntimeError(f"Network error for {method}: {err}") from err

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as err:
            raise RuntimeError(f"Invalid JSON for {method}: {body}") from err

        if "error" in parsed:
            raise RuntimeError(
                f"Bitrix error for {method}: {parsed.get('error')} - {parsed.get('error_description')}"
            )
        return parsed

    def call_form(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Call legacy Bitrix methods that expect form-encoded payload."""
        url = f"{self.webhook_url}/{method}.json"
        encoded = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {err.code} for {method}: {detail}") from err
        except urllib.error.URLError as err:
            raise RuntimeError(f"Network error for {method}: {err}") from err

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as err:
            raise RuntimeError(f"Invalid JSON for {method}: {body}") from err

        if "error" in parsed:
            raise RuntimeError(
                f"Bitrix error for {method}: {parsed.get('error')} - {parsed.get('error_description')}"
            )
        return parsed


def load_local_env() -> None:
    for env_path in [Path(".env"), Path(".env.webhooks")]:
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value


def resolve_webhook_url(webhook_arg: str | None) -> str:
    if webhook_arg:
        return webhook_arg
    env_value = os.environ.get("B24_WEBHOOK_URL", "").strip()
    if env_value:
        return env_value
    raise ValueError("Webhook URL is required: pass --webhook-url or set B24_WEBHOOK_URL in env")


def get_stages(client: BitrixWebhookClient, entity_id: int) -> list[dict[str, Any]]:
    response = client.call("task.stages.get", {"entityId": int(entity_id)})
    result = response.get("result", {})
    stages: list[dict[str, Any]] = []
    if isinstance(result, dict):
        for stage_id, stage_data in result.items():
            stage = dict(stage_data or {})
            if "ID" not in stage:
                stage["ID"] = int(stage_id)
            stages.append(stage)
    elif isinstance(result, list):
        stages = [dict(stage or {}) for stage in result]
    stages.sort(key=lambda item: int(item.get("SORT", 0)))
    return stages


def build_stage_map(stages: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for stage in stages:
        system_type = str(stage.get("SYSTEM_TYPE", "")).upper()
        if not system_type:
            continue
        grouped.setdefault(system_type, []).append(stage)
    return grouped


def resolve_stage_id_for_status(stage_map: dict[str, list[dict[str, Any]]], status_code: int) -> int | None:
    for system_type in STATUS_TO_STAGE_TYPES.get(status_code, []):
        candidates = stage_map.get(system_type, [])
        if candidates:
            return int(candidates[0]["ID"])
    return None


def resolve_stage_id_by_title(stages: list[dict[str, Any]], status_code: int) -> int | None:
    title_rules = {
        1: ["нов", "new", "to do"],
        2: ["выполн", "работ", "progress", "doing", "in work"],
        3: ["выполн", "работ", "progress", "doing", "in work"],
        4: ["тест", "review", "qa", "провер"],
        5: ["сделан", "готов", "done", "finish", "completed"],
    }
    rules = title_rules.get(int(status_code), [])
    if not rules:
        return None
    for stage in sorted(stages, key=lambda item: int(item.get("SORT", 0))):
        title = str(stage.get("TITLE", "")).lower()
        if any(rule in title for rule in rules):
            return int(stage["ID"])
    return None


def save_stage_snapshot(output: Path, stages: list[dict[str, Any]], entity_id: int) -> None:
    grouped = {
        key: [int(item["ID"]) for item in values]
        for key, values in build_stage_map(stages).items()
    }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entity_id": int(entity_id),
        "stages": stages,
        "system_type_map": grouped,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_roadmap(path: Path) -> list[RoadmapTask]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    task_ids_from_source = raw.get("bitrix_ids", {}).get("tasks", {})
    tasks: list[RoadmapTask] = []
    keys: set[str] = set()
    for item in raw.get("tasks", []):
        task = RoadmapTask(
            key=item["key"],
            title=item["title"],
            description=item.get("description", ""),
            stage=item.get("stage", "Roadmap"),
            depends_on=item.get("depends_on", []),
            parent=item.get("parent"),
            tags=item.get("tags", []),
            responsible_id=item.get("responsible_id"),
            status=item.get("status"),
            epic=item.get("epic"),
            skills=item.get("skills", []),
            technical_test=item.get("technical_test", []),
            ui_test=item.get("ui_test", []),
            done_definition=item.get("done_definition", []),
            bitrix_task_id=item.get("bitrix_task_id", task_ids_from_source.get(item["key"])),
        )
        if task.key in keys:
            raise ValueError(f"Duplicate task key: {task.key}")
        keys.add(task.key)
        tasks.append(task)

    for task in tasks:
        for dep in task.depends_on:
            if dep not in keys:
                raise ValueError(f"Task {task.key} depends on unknown key: {dep}")
        if task.parent and task.parent not in keys:
            raise ValueError(f"Task {task.key} has unknown parent: {task.parent}")
    return tasks


def load_epic_ids(path: Path) -> dict[str, int]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    epic_ids: dict[str, int] = {}
    for code, task_id_raw in raw.get("bitrix_ids", {}).get("epics", {}).items():
        code_str = str(code).strip()
        task_id = int(task_id_raw or 0)
        if code_str and task_id > 0:
            epic_ids[code_str] = task_id
    for item in raw.get("epics", []):
        code = str(item.get("code", "")).strip()
        task_id = int(item.get("bitrix_task_id", 0) or 0)
        if code and task_id > 0:
            epic_ids[code] = task_id
    return epic_ids


def normalize_status(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if str(value).isdigit():
        return int(value)
    normalized = str(value).strip().upper()
    ru_alias = {
        "В РАБОТЕ": "IN_PROGRESS",
        "НА ТЕСТИРОВАНИИ": "SUPPOSEDLY_COMPLETED",
        "СДЕЛАНЫ": "COMPLETED",
    }
    normalized = ru_alias.get(normalized, normalized)
    return BITRIX_STATUS_ALIAS.get(normalized)


def derive_skills(task: RoadmapTask) -> list[str]:
    if task.skills:
        return task.skills

    skills = ["navigate-b24-project", "project-development", "filesystem-context"]
    if "backend" in task.tags:
        skills.extend(["develop-b24-python", "implement-b24-features"])
    if "frontend" in task.tags:
        skills.extend(["develop-b24-frontend"])
    if "security" in task.tags or "ops" in task.tags:
        skills.extend(["evaluation"])
    if "automation" in task.tags:
        skills.extend(["tool-design"])
    return sorted(set(skills))


def derive_technical_test(task: RoadmapTask) -> list[str]:
    if task.technical_test:
        return task.technical_test
    tests = [
        "Проверить соответствие изменений требованиям задачи и зависимостям.",
        "Прогнать профильные проверки (линт/валидация/скрипты по модулю задачи).",
        "Проверить отсутствие регрессий в связанных backend/frontend модулях.",
    ]
    if "backend" in task.tags:
        tests.append("Проверить API-ответы и обработку ошибок для измененного backend flow.")
    if "frontend" in task.tags:
        tests.append("Проверить успешную загрузку страницы и корректные API-вызовы в UI.")
    return tests


def derive_ui_test(task: RoadmapTask) -> list[str]:
    if task.ui_test:
        return task.ui_test
    if "frontend" not in task.tags and "dashboard" not in task.tags:
        return ["UI-проверка не требуется для этой задачи (backend/операционная задача)."]
    return [
        "Проверить целевой пользовательский сценарий в интерфейсе PMO Hub.",
        "Проверить отображение состояний загрузки/ошибок и корректность данных.",
        "Проверить поведение на desktop и мобильной ширине.",
    ]


def derive_done_definition(task: RoadmapTask) -> list[str]:
    if task.done_definition:
        return task.done_definition
    return [
        "Результат задачи зафиксирован в репозитории (код/документация/артефакты).",
        "Техническое и UI-тестирование выполнено по чеклисту задачи.",
        "Статусы синхронизированы в Bitrix24 и репозиторном трекере.",
    ]


def render_task_description(task: RoadmapTask) -> str:
    epic = task.epic or STAGE_EPIC_MAP.get(task.stage, "EPIC-MISC")
    deps = ", ".join(task.depends_on) if task.depends_on else "Нет"
    skills = derive_skills(task)
    technical_test = derive_technical_test(task)
    ui_test = derive_ui_test(task)
    done_definition = derive_done_definition(task)

    parts = [
        f"Roadmap key: {task.key}",
        f"Epic: {epic}",
        f"Stage: {task.stage}",
        "",
        "Что нужно сделать:",
        f"- {task.description}",
        "",
        "Зависимости:",
        f"- {deps}",
        "",
        "Какие skills использовать:",
        *[f"- {skill}" for skill in skills],
        "",
        "Как тестировать (технически):",
        *[f"- {item}" for item in technical_test],
        "",
        "Как тестировать (UI):",
        *[f"- {item}" for item in ui_test],
        "",
        "Как понять, что задача выполнена:",
        *[f"- {item}" for item in done_definition],
        "",
        "Workflow статусов Bitrix24:",
        "- В работе -> STATUS=3 (IN_PROGRESS)",
        "- На тестировании -> STATUS=4 (SUPPOSEDLY_COMPLETED)",
        "- Сделаны -> STATUS=5 (COMPLETED)",
        "",
        "Правило именования:",
        "- Сначала человекопонятное название, затем служебная часть [RD-xxx][EPIC-xxx].",
        "",
        "Источник истины: репозиторий (`docs/ROADMAP_TASKS.json`, `.agent/*`).",
    ]
    return "\n".join(parts)


def render_task_title(task: RoadmapTask) -> str:
    epic = task.epic or STAGE_EPIC_MAP.get(task.stage, "EPIC-MISC")
    short_epic = epic.split(" ", 1)[0]
    return f"{task.title} [{task.key}][{short_epic}]"


def _task_key_sort_value(task_key: str) -> int:
    try:
        return int(task_key.split("-", 1)[1])
    except (IndexError, ValueError):
        return 999999


def build_task_numbering(tasks: list[RoadmapTask]) -> dict[str, str]:
    by_key = {task.key: task for task in tasks}
    numbering: dict[str, str] = {}

    epics: dict[str, list[RoadmapTask]] = {}
    for task in tasks:
        epic_code = _epic_code(task.epic or STAGE_EPIC_MAP.get(task.stage, "EPIC-MISC"))
        epics.setdefault(epic_code, []).append(task)

    for epic_code, epic_tasks in epics.items():
        epic_keys = {task.key for task in epic_tasks}
        children: dict[str, list[str]] = {}
        roots: list[str] = []

        for task in epic_tasks:
            parent = task.parent
            if parent and parent in epic_keys:
                children.setdefault(parent, []).append(task.key)
            else:
                roots.append(task.key)

        roots.sort(key=_task_key_sort_value)
        for child_list in children.values():
            child_list.sort(key=_task_key_sort_value)

        def visit(node_key: str, prefix: str) -> None:
            numbering[node_key] = prefix
            for idx, child_key in enumerate(children.get(node_key, []), start=1):
                visit(child_key, f"{prefix}.{idx}")

        for idx, root_key in enumerate(roots, start=1):
            visit(root_key, str(idx))

        # Fallback: include orphaned/cyclic nodes not reached by DFS
        for task in epic_tasks:
            if task.key not in numbering:
                numbering[task.key] = str(len(numbering) + 1)

    return numbering


def render_task_title_for_bitrix(task: RoadmapTask, task_number: str | None) -> str:
    base_title = task.title
    if task_number:
        base_title = f"Задача {task_number}. {base_title}"
    epic = task.epic or STAGE_EPIC_MAP.get(task.stage, "EPIC-MISC")
    short_epic = epic.split(" ", 1)[0]
    return f"{base_title} [{task.key}][{short_epic}]"


def render_task_tags(task: RoadmapTask) -> list[str]:
    epic = task.epic or STAGE_EPIC_MAP.get(task.stage, "EPIC-MISC")
    epic_tag = epic.split(" ", 1)[0]
    merged = list(task.tags) + ["pmo-roadmap", task.stage, epic_tag]
    seen: set[str] = set()
    unique: list[str] = []
    for tag in merged:
        if tag not in seen:
            seen.add(tag)
            unique.append(tag)
    return unique


def _epic_code(epic_value: str) -> str:
    return epic_value.split(" ", 1)[0].strip()


RD_KEY_PATTERN = re.compile(r"\[(RD-\d+)\]")
EPIC_CODE_PATTERN = re.compile(r"\[(EPIC-[^\]]+)\]")


def list_project_tasks(
    client: BitrixWebhookClient,
    project_id: int,
    select_fields: list[str] | None = None,
) -> list[dict[str, Any]]:
    fields = select_fields or ["ID", "TITLE", "STATUS", "PARENT_ID"]
    start = 0
    tasks: list[dict[str, Any]] = []
    while True:
        response = client.call(
            "tasks.task.list",
            {
                "filter": {"GROUP_ID": int(project_id)},
                "order": {"ID": "asc"},
                "select": fields,
                "start": int(start),
            },
        )
        batch = response.get("result", {}).get("tasks", [])
        tasks.extend(batch)
        next_offset = response.get("next")
        if next_offset is None:
            break
        start = int(next_offset)
    return tasks


def find_existing_task_ids_by_key(tasks: list[dict[str, Any]]) -> dict[str, int]:
    found: dict[str, int] = {}
    for task in tasks:
        title = str(task.get("title", ""))
        match = RD_KEY_PATTERN.search(title)
        if not match:
            continue
        key = match.group(1)
        task_id = int(task.get("id", 0) or 0)
        if task_id <= 0:
            continue
        # Keep latest by id if multiple records accidentally exist.
        if key not in found or task_id > found[key]:
            found[key] = task_id
    return found


def find_existing_epic_root_ids(tasks: list[dict[str, Any]]) -> dict[str, int]:
    found: dict[str, int] = {}
    for task in tasks:
        title = str(task.get("title", ""))
        epic_match = EPIC_CODE_PATTERN.search(title)
        rd_match = RD_KEY_PATTERN.search(title)
        if not epic_match or rd_match:
            continue
        epic_code = epic_match.group(1)
        task_id = int(task.get("id", 0) or 0)
        if task_id <= 0:
            continue
        if epic_code not in found or task_id > found[epic_code]:
            found[epic_code] = task_id
    return found


def build_epics(tasks: list[RoadmapTask]) -> list[EpicTask]:
    grouped: dict[str, list[RoadmapTask]] = {}
    for task in tasks:
        epic_value = task.epic or STAGE_EPIC_MAP.get(task.stage, "EPIC-MISC Misc")
        code = _epic_code(epic_value)
        grouped.setdefault(code, []).append(task)

    epics: list[EpicTask] = []
    for code, epic_tasks in grouped.items():
        epic_tasks_sorted = sorted(epic_tasks, key=lambda item: item.key)
        stage = epic_tasks_sorted[0].stage
        title = EPIC_TITLES_RU.get(code, f"Эпик {code}")
        epic_key = f"{code}-ROOT"
        description = render_epic_description(code, title, stage, epic_tasks_sorted)
        epics.append(
            EpicTask(
                key=epic_key,
                code=code,
                title=title,
                description=description,
                stage=stage,
                tags=["pmo-epic", code, stage],
            )
        )
    epics.sort(key=lambda item: item.code)
    return epics


def render_epic_title(epic: EpicTask) -> str:
    order = EPIC_ORDER.get(epic.code, 99)
    return f"Эпик {order}. {epic.title} [{epic.code}]"


def render_epic_description(code: str, title: str, stage: str, tasks: list[RoadmapTask]) -> str:
    task_lines = [f"- {task.title} [{task.key}]" for task in tasks]
    skills = sorted({skill for task in tasks for skill in derive_skills(task)})
    tools = [
        "Bitrix24 REST webhook",
        "scripts/bitrix24/roadmap_sync.py",
        "docs/ROADMAP_TASKS.json",
        "docs/ROADMAP_EXECUTION_STATUS.json",
    ]
    done = [
        "Все задачи эпика выполнены и синхронизированы в Bitrix24 и репозитории.",
        "По задачам соблюден workflow: В работе -> На тестировании -> Сделаны.",
        "Смежные зависимости по Ганту проставлены и актуальны.",
    ]
    parts = [
        f"Эпик: {title}",
        f"Код эпика: {code}",
        f"Стадия roadmap: {stage}",
        "",
        "Какие задачи решаем в эпике:",
        *task_lines,
        "",
        "Какие skills используем:",
        *[f"- {skill}" for skill in skills],
        "",
        "Инструменты:",
        *[f"- {item}" for item in tools],
        "",
        "Результат завершения эпика:",
        *[f"- {item}" for item in done],
    ]
    return "\n".join(parts)


def topological_order(tasks: list[RoadmapTask]) -> list[RoadmapTask]:
    by_key = {task.key: task for task in tasks}
    deps: dict[str, set[str]] = {}
    reverse_edges: dict[str, set[str]] = {task.key: set() for task in tasks}

    for task in tasks:
        required = set(task.depends_on)
        if task.parent:
            required.add(task.parent)
        deps[task.key] = required
        for req in required:
            reverse_edges[req].add(task.key)

    queue = [key for key, required in deps.items() if not required]
    queue.sort()

    ordered_keys: list[str] = []
    while queue:
        current = queue.pop(0)
        ordered_keys.append(current)
        for nxt in sorted(reverse_edges[current]):
            deps[nxt].discard(current)
            if not deps[nxt] and nxt not in ordered_keys and nxt not in queue:
                queue.append(nxt)

    if len(ordered_keys) != len(tasks):
        unresolved = [key for key, required in deps.items() if required]
        raise ValueError(f"Dependency cycle detected for keys: {', '.join(unresolved)}")

    return [by_key[key] for key in ordered_keys]


def create_mode(args: argparse.Namespace) -> int:
    source = Path(args.source)
    output = Path(args.output)
    tasks = load_roadmap(source)
    ordered = topological_order(tasks)
    task_numbering = build_task_numbering(tasks)

    print(f"Loaded {len(ordered)} roadmap tasks from {source}")

    client = BitrixWebhookClient(resolve_webhook_url(args.webhook_url))
    task_id_map: dict[str, int] = {
        task.key: int(task.bitrix_task_id)
        for task in ordered
        if task.bitrix_task_id and int(task.bitrix_task_id) > 0
    }
    existing_project_tasks = list_project_tasks(client, int(args.project_id), ["ID", "TITLE"])
    discovered_ids = find_existing_task_ids_by_key(existing_project_tasks)
    for key, task_id in discovered_ids.items():
        if int(task_id_map.get(key, 0)) <= 0:
            task_id_map[key] = int(task_id)

    for task in ordered:
        existing_id = int(task_id_map.get(task.key, 0))
        if existing_id > 0:
            print(f"Skip create {task.key}: already exists as task #{existing_id}")
            continue
        parent_id = task_id_map.get(task.parent) if task.parent else None
        responsible_id = task.responsible_id or args.default_responsible_id

        fields: dict[str, Any] = {
            "TITLE": render_task_title_for_bitrix(task, task_numbering.get(task.key)),
            "DESCRIPTION": render_task_description(task),
            "GROUP_ID": int(args.project_id),
            "TAGS": render_task_tags(task),
        }
        if parent_id:
            fields["PARENT_ID"] = int(parent_id)
        if responsible_id:
            fields["RESPONSIBLE_ID"] = int(responsible_id)
        if args.created_by:
            fields["CREATED_BY"] = int(args.created_by)

        payload = {"fields": fields}

        if not args.apply:
            print(f"[DRY-RUN] create {task.key}: {json.dumps(payload, ensure_ascii=False)}")
            task_id_map[task.key] = -1
            continue

        result = client.call("tasks.task.add", payload)
        task_id = int(result["result"]["task"]["id"])
        task_id_map[task.key] = task_id
        print(f"Created {task.key} -> task #{task_id}")

        status_code = normalize_status(task.status)
        if status_code is not None:
            client.call("tasks.task.update", {"taskId": task_id, "fields": {"STATUS": status_code}})
            print(f"  set status {status_code} for {task.key}")

    for task in ordered:
        if not task.depends_on:
            continue
        for dep in task.depends_on:
            if not args.apply:
                print(f"[DRY-RUN] link {dep} -> {task.key} (finish-start)")
                continue
            from_id = task_id_map[dep]
            to_id = task_id_map[task.key]
            client.call("task.dependence.add", {"taskIdFrom": from_id, "taskIdTo": to_id, "linkType": 2})
            print(f"Linked dependency {dep}({from_id}) -> {task.key}({to_id})")

    output.parent.mkdir(parents=True, exist_ok=True)
    mapping_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "project_id": int(args.project_id),
        "dry_run": not args.apply,
        "tasks": task_id_map,
    }
    output.write_text(json.dumps(mapping_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved mapping to {output}")

    return 0


def create_missing_mode(args: argparse.Namespace) -> int:
    source = Path(args.source)
    map_file = Path(args.map_file)
    tasks = load_roadmap(source)
    ordered = topological_order(tasks)
    task_numbering = build_task_numbering(tasks)

    mapping = {"tasks": {}}
    if map_file.exists():
        mapping = json.loads(map_file.read_text(encoding="utf-8"))
    task_id_map: dict[str, int] = dict(mapping.get("tasks", {}))
    for task in tasks:
        if task.bitrix_task_id and int(task.bitrix_task_id) > 0 and int(task_id_map.get(task.key, 0)) <= 0:
            task_id_map[task.key] = int(task.bitrix_task_id)

    client = BitrixWebhookClient(resolve_webhook_url(args.webhook_url))
    existing_project_tasks = list_project_tasks(client, int(args.project_id), ["ID", "TITLE"])
    discovered_ids = find_existing_task_ids_by_key(existing_project_tasks)
    for key, task_id in discovered_ids.items():
        if int(task_id_map.get(key, 0)) <= 0:
            task_id_map[key] = int(task_id)
    created = 0

    for task in ordered:
        existing_id = int(task_id_map.get(task.key, 0))
        if existing_id > 0:
            continue

        responsible_id = task.responsible_id or args.default_responsible_id
        fields: dict[str, Any] = {
            "TITLE": render_task_title_for_bitrix(task, task_numbering.get(task.key)),
            "DESCRIPTION": render_task_description(task),
            "GROUP_ID": int(args.project_id),
            "TAGS": render_task_tags(task),
        }
        if responsible_id:
            fields["RESPONSIBLE_ID"] = int(responsible_id)
        if args.created_by:
            fields["CREATED_BY"] = int(args.created_by)

        payload = {"fields": fields}
        if not args.apply:
            print(f"[DRY-RUN] create missing {task.key}: {json.dumps(payload, ensure_ascii=False)}")
            continue

        result = client.call("tasks.task.add", payload)
        task_id = int(result["result"]["task"]["id"])
        task_id_map[task.key] = task_id
        created += 1
        print(f"Created missing {task.key} -> task #{task_id}")

    map_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "project_id": int(args.project_id),
        "dry_run": not args.apply,
        "tasks": task_id_map,
    }
    map_file.parent.mkdir(parents=True, exist_ok=True)
    map_file.write_text(json.dumps(map_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved mapping to {map_file}; created {created} tasks")
    return 0


def _link_dependency_safe(client: BitrixWebhookClient, from_id: int, to_id: int) -> None:
    try:
        client.call("task.dependence.add", {"taskIdFrom": int(from_id), "taskIdTo": int(to_id), "linkType": 2})
    except RuntimeError as error:
        message = str(error)
        if "ILLEGAL_NEW_LINK" in message or "ACTION_FAILED" in message:
            return
        raise


def _task_exists(client: BitrixWebhookClient, task_id: int) -> bool:
    try:
        client.call("tasks.task.get", {"taskId": int(task_id)})
        return True
    except RuntimeError:
        return False


def sync_epic_structure_mode(args: argparse.Namespace) -> int:
    source = Path(args.source)
    map_file = Path(args.map_file)
    tasks = load_roadmap(source)
    by_key = {task.key: task for task in tasks}
    task_numbering = build_task_numbering(tasks)
    epics = build_epics(tasks)

    source_epic_ids = load_epic_ids(source)
    mapping = {"tasks": {}, "epics": {}}
    if map_file.exists():
        mapping = json.loads(map_file.read_text(encoding="utf-8"))
    task_id_map: dict[str, int] = dict(mapping.get("tasks", {}))
    for task in tasks:
        if task.bitrix_task_id and int(task.bitrix_task_id) > 0 and int(task_id_map.get(task.key, 0)) <= 0:
            task_id_map[task.key] = int(task.bitrix_task_id)
    epic_id_map: dict[str, int] = dict(mapping.get("epics", {}))
    for code, epic_id in source_epic_ids.items():
        if int(epic_id_map.get(code, 0)) <= 0:
            epic_id_map[code] = int(epic_id)

    client = BitrixWebhookClient(resolve_webhook_url(args.webhook_url))
    changed = 0
    project_tasks = list_project_tasks(client, int(args.project_id), ["ID", "TITLE", "STATUS", "PARENT_ID"])
    discovered_task_ids = find_existing_task_ids_by_key(project_tasks)
    for key, task_id in discovered_task_ids.items():
        if int(task_id_map.get(key, 0)) <= 0:
            task_id_map[key] = int(task_id)
    discovered_epic_ids = find_existing_epic_root_ids(project_tasks)
    for code, task_id in discovered_epic_ids.items():
        if int(epic_id_map.get(code, 0)) <= 0:
            epic_id_map[code] = int(task_id)

    # Ensure epic root tasks
    for epic in epics:
        epic_id = int(epic_id_map.get(epic.code, 0))
        if epic_id > 0 and not _task_exists(client, epic_id):
            fallback_id = int(discovered_epic_ids.get(epic.code, 0))
            if fallback_id > 0 and fallback_id != epic_id:
                print(f"[WARN] Epic {epic.code} mapping #{epic_id} is stale, switch to discovered #{fallback_id}")
                epic_id = fallback_id
                epic_id_map[epic.code] = fallback_id
            else:
                print(f"[WARN] Epic {epic.code} mapping #{epic_id} is stale, will create or discover")
                epic_id = 0
                epic_id_map[epic.code] = 0
        fields = {
            "TITLE": render_epic_title(epic),
            "DESCRIPTION": epic.description,
            "GROUP_ID": int(args.project_id),
            "TAGS": epic.tags,
        }
        if args.default_responsible_id:
            fields["RESPONSIBLE_ID"] = int(args.default_responsible_id)

        if epic_id <= 0:
            payload = {"fields": fields}
            if not args.apply:
                print(f"[DRY-RUN] create epic {epic.code}: {json.dumps(payload, ensure_ascii=False)}")
                continue
            result = client.call("tasks.task.add", payload)
            epic_id = int(result["result"]["task"]["id"])
            epic_id_map[epic.code] = epic_id
            changed += 1
            print(f"Created epic {epic.code} -> task #{epic_id}")
        else:
            payload = {"taskId": epic_id, "fields": fields}
            if not args.apply:
                print(f"[DRY-RUN] update epic {epic.code}#{epic_id}")
                continue
            client.call("tasks.task.update", payload)
            changed += 1
            print(f"Updated epic {epic.code}#{epic_id}")

    # Update task parent links and metadata
    for task in tasks:
        task_id = int(task_id_map.get(task.key, 0))
        if task_id > 0 and not _task_exists(client, task_id):
            fallback_id = int(discovered_task_ids.get(task.key, 0))
            if fallback_id > 0 and fallback_id != task_id:
                print(f"[WARN] Task {task.key} mapping #{task_id} is stale, switch to discovered #{fallback_id}")
                task_id = fallback_id
                task_id_map[task.key] = fallback_id
            else:
                print(f"[WARN] Task {task.key} mapping #{task_id} is stale, skip parent sync")
                task_id = 0
                task_id_map[task.key] = 0
        if task_id <= 0:
            print(f"[WARN] Task {task.key} missing in mapping, skip parent sync")
            continue

        epic_value = task.epic or STAGE_EPIC_MAP.get(task.stage, "EPIC-MISC")
        epic_code = _epic_code(epic_value)
        epic_parent_id = int(epic_id_map.get(epic_code, 0))
        direct_parent_key = task.parent
        parent_id = epic_parent_id
        if direct_parent_key:
            direct_parent_id = int(task_id_map.get(direct_parent_key, 0))
            has_conflict = False
            if direct_parent_key in task.depends_on:
                has_conflict = True
            elif direct_parent_key in by_key and task.key in by_key[direct_parent_key].depends_on:
                has_conflict = True

            if has_conflict:
                print(
                    f"[WARN] Skip direct parent {direct_parent_key} for {task.key} due to dependency conflict; "
                    f"use epic parent"
                )
            elif direct_parent_id > 0:
                parent_id = direct_parent_id

        fields = {
            "TITLE": render_task_title_for_bitrix(task, task_numbering.get(task.key)),
            "DESCRIPTION": render_task_description(task),
            "TAGS": render_task_tags(task),
        }
        if parent_id > 0:
            fields["PARENT_ID"] = parent_id

        if not args.apply:
            print(f"[DRY-RUN] update task {task.key}#{task_id} parent={parent_id}")
            continue
        try:
            client.call("tasks.task.update", {"taskId": task_id, "fields": fields})
            changed += 1
            print(f"Updated task {task.key}#{task_id} parent={parent_id}")
        except RuntimeError as error:
            if "Невозможно назначить родительскую задачу" in str(error) and "PARENT_ID" in fields:
                fallback_fields = dict(fields)
                fallback_fields.pop("PARENT_ID", None)
                client.call("tasks.task.update", {"taskId": task_id, "fields": fallback_fields})
                changed += 1
                print(f"[WARN] Parent removed for {task.key}#{task_id} due dependency conflict")
            else:
                print(f"[WARN] Failed to update task {task.key}#{task_id}: {error}")

    # Gantt dependencies between tasks
    for task in tasks:
        to_id = int(task_id_map.get(task.key, 0))
        if to_id <= 0:
            continue
        for dep_key in task.depends_on:
            from_id = int(task_id_map.get(dep_key, 0))
            if from_id <= 0:
                continue
            if not args.apply:
                print(f"[DRY-RUN] link {dep_key}({from_id}) -> {task.key}({to_id})")
                continue
            _link_dependency_safe(client, from_id, to_id)

    # Cross-epic gantt dependencies on epic roots
    cross_epic_edges: set[tuple[str, str]] = set()
    for task in tasks:
        to_epic = _epic_code(task.epic or STAGE_EPIC_MAP.get(task.stage, "EPIC-MISC"))
        for dep_key in task.depends_on:
            if dep_key not in by_key:
                continue
            dep_task = by_key[dep_key]
            from_epic = _epic_code(dep_task.epic or STAGE_EPIC_MAP.get(dep_task.stage, "EPIC-MISC"))
            if from_epic != to_epic:
                cross_epic_edges.add((from_epic, to_epic))

    for from_epic, to_epic in sorted(cross_epic_edges):
        from_id = int(epic_id_map.get(from_epic, 0))
        to_id = int(epic_id_map.get(to_epic, 0))
        if from_id <= 0 or to_id <= 0:
            continue
        if not args.apply:
            print(f"[DRY-RUN] epic-link {from_epic}({from_id}) -> {to_epic}({to_id})")
            continue
        _link_dependency_safe(client, from_id, to_id)
        print(f"Linked epic dependency {from_epic}({from_id}) -> {to_epic}({to_id})")

    mapping_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "project_id": int(args.project_id),
        "dry_run": not args.apply,
        "tasks": task_id_map,
        "epics": epic_id_map,
    }
    map_file.parent.mkdir(parents=True, exist_ok=True)
    map_file.write_text(json.dumps(mapping_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved mapping to {map_file}; structure updates: {changed}")
    return 0


def sync_status_mode(args: argparse.Namespace) -> int:
    map_file = Path(args.map_file)
    status_file = Path(args.status_file)

    mapping = json.loads(map_file.read_text(encoding="utf-8"))
    statuses = json.loads(status_file.read_text(encoding="utf-8"))

    task_ids: dict[str, int] = mapping.get("tasks", {})
    requested_statuses: dict[str, Any] = statuses.get("tasks", {})

    client = BitrixWebhookClient(resolve_webhook_url(args.webhook_url))
    stage_map: dict[str, list[dict[str, Any]]] = {}
    stages: list[dict[str, Any]] = []
    can_move = False
    if args.sync_kanban:
        if not args.kanban_entity_id:
            raise ValueError("--kanban-entity-id is required when --sync-kanban is used")
        stages = get_stages(client, int(args.kanban_entity_id))
        stage_map = build_stage_map(stages)
        can_move_response = client.call(
            "task.stages.canmovetask",
            {"entityId": int(args.kanban_entity_id), "entityType": args.kanban_entity_type},
        )
        can_move = bool(can_move_response.get("result", False))
        if not can_move:
            print("[WARN] Current webhook user cannot move tasks in this kanban entity")
        if args.stage_output:
            save_stage_snapshot(Path(args.stage_output), stages, int(args.kanban_entity_id))

    changed = 0
    for key, status_value in requested_statuses.items():
        if key not in task_ids:
            print(f"[WARN] Task key {key} is missing in mapping file, skip")
            continue
        task_id = task_ids[key]
        if task_id <= 0:
            print(f"[WARN] Task key {key} has dry-run id in mapping, skip")
            continue

        status_code = normalize_status(status_value)
        if status_code is None:
            print(f"[WARN] Unsupported status for {key}: {status_value}")
            continue

        payload = {"taskId": int(task_id), "fields": {"STATUS": int(status_code)}}
        if not args.apply:
            print(f"[DRY-RUN] update {key}#{task_id} -> STATUS={status_code}")
            if args.sync_kanban:
                stage_id = resolve_stage_id_for_status(stage_map, int(status_code))
                if stage_id is None:
                    stage_id = resolve_stage_id_by_title(stages, int(status_code))
                if stage_id is not None:
                    print(f"[DRY-RUN] move {key}#{task_id} -> STAGE={stage_id}")
            continue

        client.call("tasks.task.update", payload)
        if args.sync_kanban and can_move:
            stage_id = resolve_stage_id_for_status(stage_map, int(status_code))
            if stage_id is None:
                stage_id = resolve_stage_id_by_title(stages, int(status_code))
            if stage_id is not None:
                client.call("task.stages.movetask", {"id": int(task_id), "stageId": int(stage_id)})
                print(f"Moved {key}#{task_id} -> STAGE={stage_id}")
            else:
                print(f"[WARN] No kanban stage mapping for status {status_code} on task {key}")
        changed += 1
        print(f"Updated {key}#{task_id} -> STATUS={status_code}")

    print(f"Status sync finished. Updated tasks: {changed}")
    return 0


def sync_metadata_mode(args: argparse.Namespace) -> int:
    source = Path(args.source)
    map_file = Path(args.map_file)

    tasks = load_roadmap(source)
    by_key = {task.key: task for task in tasks}
    task_numbering = build_task_numbering(tasks)
    mapping = json.loads(map_file.read_text(encoding="utf-8"))
    task_ids: dict[str, int] = mapping.get("tasks", {})

    client = BitrixWebhookClient(resolve_webhook_url(args.webhook_url))
    changed = 0

    for key, task_id in task_ids.items():
        if key not in by_key:
            print(f"[WARN] Task key {key} not found in source roadmap, skip")
            continue
        if task_id <= 0:
            print(f"[WARN] Task key {key} has invalid ID in mapping, skip")
            continue

        task = by_key[key]
        fields = {
            "TITLE": render_task_title_for_bitrix(task, task_numbering.get(task.key)),
            "DESCRIPTION": render_task_description(task),
            "TAGS": render_task_tags(task),
        }
        payload = {"taskId": int(task_id), "fields": fields}

        if not args.apply:
            print(f"[DRY-RUN] metadata {key}#{task_id}: {json.dumps(payload, ensure_ascii=False)}")
            continue

        client.call("tasks.task.update", payload)
        changed += 1
        print(f"Updated metadata for {key}#{task_id}")

    print(f"Metadata sync finished. Updated tasks: {changed}")
    return 0


def fetch_stages_mode(args: argparse.Namespace) -> int:
    if not args.entity_id:
        raise ValueError("--entity-id is required")
    client = BitrixWebhookClient(resolve_webhook_url(args.webhook_url))
    stages = get_stages(client, int(args.entity_id))
    output = Path(args.output)
    save_stage_snapshot(output, stages, int(args.entity_id))
    print(f"Fetched {len(stages)} stages for entity {args.entity_id}")
    print(f"Saved stages snapshot to {output}")
    return 0


def _build_done_result_text(task: RoadmapTask, commit_url: str, now_iso: str) -> str:
    epic_value = task.epic or STAGE_EPIC_MAP.get(task.stage, "EPIC-MISC")
    lines = [
        f"Результат задачи {task.key}: {task.title}",
        f"Эпик: {epic_value}",
        f"Сделано: {task.description}",
        f"Дата фиксации: {now_iso}",
        f"Коммит: {commit_url}",
    ]
    return "\n".join(lines)


def sync_task_results_mode(args: argparse.Namespace) -> int:
    source = Path(args.source)
    map_file = Path(args.map_file)
    status_file = Path(args.status_file)
    tasks = load_roadmap(source)
    by_key = {task.key: task for task in tasks}
    mapping = json.loads(map_file.read_text(encoding="utf-8"))
    statuses = json.loads(status_file.read_text(encoding="utf-8"))

    task_ids: dict[str, int] = mapping.get("tasks", {})
    requested_statuses: dict[str, Any] = statuses.get("tasks", {})
    client = BitrixWebhookClient(resolve_webhook_url(args.webhook_url))
    done_code = BITRIX_STATUS_ALIAS["COMPLETED"]
    now_iso = datetime.now(timezone.utc).isoformat()
    changed = 0

    for key, status_value in requested_statuses.items():
        status_code = normalize_status(status_value)
        if status_code != done_code:
            continue
        task_id = int(task_ids.get(key, 0))
        if task_id <= 0:
            print(f"[WARN] Skip result for {key}: task ID missing")
            continue
        if key not in by_key:
            print(f"[WARN] Skip result for {key}: missing in roadmap source")
            continue

        task = by_key[key]
        message = _build_done_result_text(task, args.commit_url, now_iso)
        if not args.apply:
            print(f"[DRY-RUN] result {key}#{task_id}: {message}")
            continue

        # Legacy method is the only stable way to create comment id usable for task result binding.
        comment_res = client.call_form(
            "task.comment.add",
            {
                "TASKID": int(task_id),
                "COMMENTTEXT": message,
            },
        )
        comment_id = int(comment_res.get("result", 0))
        if comment_id <= 0:
            print(f"[WARN] Comment ID missing for {key}#{task_id}; skip result bind")
            continue
        try:
            client.call("tasks.task.result.addFromComment", {"commentId": int(comment_id)})
            print(f"Added task result for {key}#{task_id} via comment {comment_id}")
        except RuntimeError as error:
            print(
                f"[WARN] Failed to bind comment {comment_id} as result for {key}#{task_id}: {error}. "
                "Comment was created and kept."
            )
        changed += 1

    print(f"Result sync finished. Processed completed tasks: {changed}")
    return 0


def _ensure_done_suffix(title: str) -> str:
    if "завершена" in title.lower():
        return title
    return f"{title} (Завершена)"


def sync_epic_completion_mode(args: argparse.Namespace) -> int:
    source = Path(args.source)
    map_file = Path(args.map_file)
    status_file = Path(args.status_file)

    tasks = load_roadmap(source)
    statuses = json.loads(status_file.read_text(encoding="utf-8"))
    mapping = json.loads(map_file.read_text(encoding="utf-8"))
    requested_statuses: dict[str, Any] = statuses.get("tasks", {})
    epic_ids: dict[str, int] = mapping.get("epics", {})

    epic_tasks: dict[str, list[RoadmapTask]] = defaultdict(list)
    for task in tasks:
        epic_value = task.epic or STAGE_EPIC_MAP.get(task.stage, "EPIC-MISC")
        epic_code = _epic_code(epic_value)
        epic_tasks[epic_code].append(task)

    done_code = BITRIX_STATUS_ALIAS["COMPLETED"]
    client = BitrixWebhookClient(resolve_webhook_url(args.webhook_url))
    changed = 0

    for epic_code, task_list in sorted(epic_tasks.items()):
        epic_id = int(epic_ids.get(epic_code, 0))
        if epic_id <= 0:
            print(f"[WARN] Skip epic {epic_code}: epic task ID missing")
            continue

        all_done = True
        for task in task_list:
            status_code = normalize_status(requested_statuses.get(task.key))
            if status_code != done_code:
                all_done = False
                break

        # Enable parent auto-close behavior for all epic roots.
        fields: dict[str, Any] = {
            "AUTOCOMPLETE_SUB_TASKS": "Y",
            "SE_PARAMETER": ["AUTO_COMPLETE"],
        }
        action = "update"

        if all_done:
            epic_get = client.call("tasks.task.get", {"taskId": int(epic_id)}) if args.apply else {"result": {"task": {}}}
            current_title = str(epic_get.get("result", {}).get("task", {}).get("title", ""))
            if current_title:
                fields["TITLE"] = _ensure_done_suffix(current_title)
            fields["STATUS"] = int(done_code)
            action = "complete"

        payload = {"taskId": int(epic_id), "fields": fields}
        if not args.apply:
            print(f"[DRY-RUN] epic {epic_code}#{epic_id} {action}: {json.dumps(payload, ensure_ascii=False)}")
            continue

        client.call("tasks.task.update", payload)
        changed += 1
        print(f"Updated epic {epic_code}#{epic_id}: auto-close=Y, action={action}")

    print(f"Epic completion sync finished. Updated epics: {changed}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bitrix24 roadmap sync utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create roadmap tasks and dependencies")
    create.add_argument("--webhook-url", help="Incoming webhook base URL")
    create.add_argument("--project-id", required=True, help="Bitrix24 project/group ID")
    create.add_argument("--source", default="docs/ROADMAP_TASKS.json", help="Roadmap JSON path")
    create.add_argument(
        "--output",
        default=".agent/context/bitrix-task-map.json",
        help="Where to store roadmap key -> Bitrix task ID map",
    )
    create.add_argument("--default-responsible-id", type=int, help="Fallback RESPONSIBLE_ID")
    create.add_argument("--created-by", type=int, help="Optional CREATED_BY user ID")
    create.add_argument("--apply", action="store_true", help="Apply changes (without this flag runs dry-run)")

    create_missing = subparsers.add_parser("create-missing", help="Create only tasks missing in mapping file")
    create_missing.add_argument("--webhook-url", help="Incoming webhook base URL")
    create_missing.add_argument("--project-id", required=True, help="Bitrix24 project/group ID")
    create_missing.add_argument("--source", default="docs/ROADMAP_TASKS.json", help="Roadmap JSON path")
    create_missing.add_argument(
        "--map-file",
        default=".agent/context/bitrix-task-map.json",
        help="Roadmap key -> task ID mapping file",
    )
    create_missing.add_argument("--default-responsible-id", type=int, help="Fallback RESPONSIBLE_ID")
    create_missing.add_argument("--created-by", type=int, help="Optional CREATED_BY user ID")
    create_missing.add_argument("--apply", action="store_true", help="Apply changes (without this flag runs dry-run)")

    sync_structure = subparsers.add_parser(
        "sync-epic-structure",
        help="Sync epic hierarchy, parent/subtask links, and gantt dependencies",
    )
    sync_structure.add_argument("--webhook-url", help="Incoming webhook base URL")
    sync_structure.add_argument("--project-id", required=True, help="Bitrix24 project/group ID")
    sync_structure.add_argument("--source", default="docs/ROADMAP_TASKS.json", help="Roadmap JSON path")
    sync_structure.add_argument(
        "--map-file",
        default=".agent/context/bitrix-task-map.json",
        help="Roadmap task/epic mapping file",
    )
    sync_structure.add_argument("--default-responsible-id", type=int, help="Fallback RESPONSIBLE_ID")
    sync_structure.add_argument("--apply", action="store_true", help="Apply changes (without this flag runs dry-run)")

    sync_status = subparsers.add_parser("sync-status", help="Update task statuses using key map")
    sync_status.add_argument("--webhook-url", help="Incoming webhook base URL")
    sync_status.add_argument(
        "--map-file",
        default=".agent/context/bitrix-task-map.json",
        help="Roadmap key -> task ID mapping file",
    )
    sync_status.add_argument(
        "--status-file",
        default="docs/ROADMAP_STATUS.example.json",
        help="Status source JSON file",
    )
    sync_status.add_argument("--sync-kanban", action="store_true", help="Move cards across kanban stages")
    sync_status.add_argument("--kanban-entity-id", type=int, help="Kanban entity ID (for group use GROUP_ID)")
    sync_status.add_argument(
        "--kanban-entity-type",
        default="G",
        choices=["G", "U"],
        help="Kanban entity type: G=group, U=user plan",
    )
    sync_status.add_argument(
        "--stage-output",
        default=".agent/context/bitrix-kanban-stages.json",
        help="Where to store fetched kanban stages snapshot",
    )
    sync_status.add_argument("--apply", action="store_true", help="Apply changes (without this flag runs dry-run)")

    sync_meta = subparsers.add_parser("sync-metadata", help="Update titles/descriptions from roadmap source")
    sync_meta.add_argument("--webhook-url", help="Incoming webhook base URL")
    sync_meta.add_argument("--source", default="docs/ROADMAP_TASKS.json", help="Roadmap JSON path")
    sync_meta.add_argument(
        "--map-file",
        default=".agent/context/bitrix-task-map.json",
        help="Roadmap key -> task ID mapping file",
    )
    sync_meta.add_argument("--apply", action="store_true", help="Apply changes (without this flag runs dry-run)")

    fetch_stages = subparsers.add_parser("fetch-stages", help="Fetch kanban stages for group/user plan")
    fetch_stages.add_argument("--webhook-url", help="Incoming webhook base URL")
    fetch_stages.add_argument("--entity-id", type=int, help="Entity ID (group ID or user ID)")
    fetch_stages.add_argument(
        "--output",
        default=".agent/context/bitrix-kanban-stages.json",
        help="Where to save fetched stages",
    )

    sync_results = subparsers.add_parser(
        "sync-task-results",
        help="Write task completion results (comment + task result bind) for completed roadmap tasks",
    )
    sync_results.add_argument("--webhook-url", help="Incoming webhook base URL")
    sync_results.add_argument("--source", default="docs/ROADMAP_TASKS.json", help="Roadmap JSON path")
    sync_results.add_argument(
        "--map-file",
        default=".agent/context/bitrix-task-map.json",
        help="Roadmap key -> task ID mapping file",
    )
    sync_results.add_argument(
        "--status-file",
        default="docs/ROADMAP_EXECUTION_STATUS.json",
        help="Roadmap execution status file",
    )
    sync_results.add_argument(
        "--commit-url",
        required=True,
        help="Commit URL to include into task result text",
    )
    sync_results.add_argument("--apply", action="store_true", help="Apply changes (without this flag runs dry-run)")

    sync_epic_completion = subparsers.add_parser(
        "sync-epic-completion",
        help="Enable epic auto-close and close/rename epics when all subtasks are completed",
    )
    sync_epic_completion.add_argument("--webhook-url", help="Incoming webhook base URL")
    sync_epic_completion.add_argument("--source", default="docs/ROADMAP_TASKS.json", help="Roadmap JSON path")
    sync_epic_completion.add_argument(
        "--map-file",
        default=".agent/context/bitrix-task-map.json",
        help="Roadmap task/epic mapping file",
    )
    sync_epic_completion.add_argument(
        "--status-file",
        default="docs/ROADMAP_EXECUTION_STATUS.json",
        help="Roadmap execution status file",
    )
    sync_epic_completion.add_argument("--apply", action="store_true", help="Apply changes (without this flag runs dry-run)")

    return parser


def main() -> int:
    load_local_env()
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "create":
            return create_mode(args)
        if args.command == "sync-status":
            return sync_status_mode(args)
        if args.command == "sync-metadata":
            return sync_metadata_mode(args)
        if args.command == "fetch-stages":
            return fetch_stages_mode(args)
        if args.command == "create-missing":
            return create_missing_mode(args)
        if args.command == "sync-epic-structure":
            return sync_epic_structure_mode(args)
        if args.command == "sync-task-results":
            return sync_task_results_mode(args)
        if args.command == "sync-epic-completion":
            return sync_epic_completion_mode(args)
        parser.print_help()
        return 1
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
