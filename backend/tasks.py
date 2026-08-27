"""Persistent task/agenda store for the autonomous agent."""
import json
import uuid
from datetime import datetime
from pathlib import Path

AUTOMATION_DIR = Path("automation")
TASKS_FILE = AUTOMATION_DIR / "tasks.json"

VALID_STATUSES = {"todo", "in_progress", "done"}
VALID_PRIORITIES = {"low", "medium", "high"}


def _ensure():
    AUTOMATION_DIR.mkdir(exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]")


def _load() -> list:
    _ensure()
    try:
        return json.loads(TASKS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save(tasks: list):
    _ensure()
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))


def list_tasks(status: str | None = None) -> list:
    tasks = _load()
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    return sorted(tasks, key=lambda t: (t["status"] == "done", t.get("created_at", "")))


def get_task(task_id: str) -> dict | None:
    for t in _load():
        if t["id"] == task_id:
            return t
    return None


def add_task(title: str, description: str = "", priority: str = "medium",
            scheduled: str | None = None) -> dict:
    task = {
        "id": f"tsk_{uuid.uuid4().hex[:8]}",
        "title": title,
        "description": description,
        "status": "todo",
        "priority": priority if priority in VALID_PRIORITIES else "medium",
        "scheduled": scheduled,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "result": "",
    }
    tasks = _load()
    tasks.append(task)
    _save(tasks)
    return task


def update_task(task_id: str, **fields) -> dict | None:
    tasks = _load()
    for t in tasks:
        if t["id"] == task_id:
            if "status" in fields and fields["status"] in VALID_STATUSES:
                t["status"] = fields["status"]
            if "title" in fields:
                t["title"] = fields["title"]
            if "description" in fields:
                t["description"] = fields["description"]
            if "priority" in fields and fields["priority"] in VALID_PRIORITIES:
                t["priority"] = fields["priority"]
            if "scheduled" in fields:
                t["scheduled"] = fields["scheduled"]
            if "result" in fields:
                t["result"] = fields["result"]
            t["updated_at"] = datetime.now().isoformat()
            _save(tasks)
            return t
    return None


def delete_task(task_id: str) -> bool:
    tasks = _load()
    new = [t for t in tasks if t["id"] != task_id]
    if len(new) == len(tasks):
        return False
    _save(new)
    return True


def next_open_task() -> dict | None:
    """Return the next actionable task (scheduled first, then todo by age)."""
    tasks = [t for t in _load() if t["status"] != "done"]
    if not tasks:
        return None
    # Scheduled (with a date) before unscheduled, oldest first
    tasks.sort(key=lambda t: (t.get("scheduled") is None, t.get("scheduled") or "", t.get("created_at", "")))
    return tasks[0]
