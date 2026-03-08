#!/usr/bin/env python3
"""Sync local roadmap tasks with Bitrix24 project tasks via incoming webhook.

Usage examples:
  python3 scripts/bitrix24/roadmap_sync.py create \
    --webhook-url "https://portal.bitrix24.ru/rest/1/your_webhook/" \
    --project-id 42 \
    --source docs/ROADMAP_TASKS.json \
    --output .agent/context/bitrix-task-map.json \
    --default-responsible-id 1 \
    --apply

  python3 scripts/bitrix24/roadmap_sync.py sync-status \
    --webhook-url "https://portal.bitrix24.ru/rest/1/your_webhook/" \
    --map-file .agent/context/bitrix-task-map.json \
    --status-file docs/ROADMAP_STATUS.example.json \
    --apply
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
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


def load_roadmap(path: Path) -> list[RoadmapTask]:
    raw = json.loads(path.read_text(encoding="utf-8"))
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


def normalize_status(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if str(value).isdigit():
        return int(value)
    return BITRIX_STATUS_ALIAS.get(str(value).strip().upper())


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

    print(f"Loaded {len(ordered)} roadmap tasks from {source}")

    client = BitrixWebhookClient(args.webhook_url)
    task_id_map: dict[str, int] = {}

    for task in ordered:
        parent_id = task_id_map.get(task.parent) if task.parent else None
        responsible_id = task.responsible_id or args.default_responsible_id

        fields: dict[str, Any] = {
            "TITLE": f"[{task.key}] {task.title}",
            "DESCRIPTION": f"{task.description}\n\nStage: {task.stage}\nRoadmap key: {task.key}",
            "GROUP_ID": int(args.project_id),
            "TAGS": task.tags + ["pmo-roadmap", task.stage],
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


def sync_status_mode(args: argparse.Namespace) -> int:
    map_file = Path(args.map_file)
    status_file = Path(args.status_file)

    mapping = json.loads(map_file.read_text(encoding="utf-8"))
    statuses = json.loads(status_file.read_text(encoding="utf-8"))

    task_ids: dict[str, int] = mapping.get("tasks", {})
    requested_statuses: dict[str, Any] = statuses.get("tasks", {})

    client = BitrixWebhookClient(args.webhook_url)

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
            continue

        client.call("tasks.task.update", payload)
        changed += 1
        print(f"Updated {key}#{task_id} -> STATUS={status_code}")

    print(f"Status sync finished. Updated tasks: {changed}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bitrix24 roadmap sync utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create roadmap tasks and dependencies")
    create.add_argument("--webhook-url", required=True, help="Incoming webhook base URL")
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

    sync_status = subparsers.add_parser("sync-status", help="Update task statuses using key map")
    sync_status.add_argument("--webhook-url", required=True, help="Incoming webhook base URL")
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
    sync_status.add_argument("--apply", action="store_true", help="Apply changes (without this flag runs dry-run)")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "create":
            return create_mode(args)
        if args.command == "sync-status":
            return sync_status_mode(args)
        parser.print_help()
        return 1
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
