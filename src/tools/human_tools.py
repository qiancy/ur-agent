"""Human tools: manage_reminder, check_wellness."""
from typing import Optional
from langchain_core.tools import tool
import json

from src.db.database import (
    query_person,
    query_person_by_name,
    _execute,
)


@tool
def manage_reminder(
    action: Optional[str] = None,
    person_name: Optional[str] = None,
    task: Optional[str] = None,
    oid: int = 1,
    due_date: Optional[str] = None,
) -> str:
    """
    Manage health reminders for a person.

    Args:
        action: Action type — 'add', 'update', or 'delete'.
        person_name: Name of the person.
        task: Task/reminder description.
        oid: Organization identifier. Default: 1 (蜀国).
        due_date: Due date for the task (optional).

    Returns:
        Operation confirmation or error message.
    """
    try:
        if not action:
            return "Error: action is required"
        action = action.lower().strip()

        if not person_name:
            return "Error: person_name is required"
        if not task and action in ("add", "update"):
            return "Error: task is required for add/update actions"

        if not isinstance(oid, int):
            try:
                oid = int(oid)
            except (ValueError, TypeError):
                return "Error: oid must be an integer"

        people = query_person(oid, person_name)
        if not people:
            return f"Person '{person_name}' not found in org {oid}"
        person = people[0]

        current = person.get("health_reminders") or {}
        if isinstance(current, str):
            current = json.loads(current)

        if action == "add":
            tasks = current.get("tasks", [])
            tasks.append({"task": task, "due_date": due_date})
            current["tasks"] = tasks
        elif action == "update":
            tasks = current.get("tasks", [])
            updated = False
            for t in tasks:
                if t["task"] == task:
                    t["due_date"] = due_date
                    updated = True
            if not updated:
                tasks.append({"task": task, "due_date": due_date})
            current["tasks"] = tasks
        elif action == "delete":
            if not task:
                return "Error: task is required for delete action"
            current["tasks"] = [t for t in current.get("tasks", []) if t["task"] != task]
        else:
            return f"Invalid action: {action}. Use 'add', 'update', or 'delete'"

        _execute(
            "UPDATE person SET health_reminders = %s WHERE id = %s",
            (json.dumps(current, ensure_ascii=False), person["id"]),
        )
        return f"Reminder {action}d for {person_name}: {task}"
    except Exception as e:
        return f"Error managing reminder: {e}"


@tool
def check_wellness(person_name: str, oid: int = 1) -> str:
    """
    Check wellness / health information for a person.

    Args:
        person_name: Name of the person.
        oid: Organization identifier. Default: 1 (蜀国).

    Returns:
        Person information with health data, or error message.
    """
    try:
        if not isinstance(oid, int):
            try:
                oid = int(oid)
            except (ValueError, TypeError):
                return "Error: oid must be an integer"
        
        people = query_person(oid, person_name)
        if people:
            result = people[0]
            result["oid"] = oid
            return json.dumps(result, default=str, ensure_ascii=False)
        return f"Person '{person_name}' not found in org {oid}"
    except Exception as e:
        return f"Error checking wellness: {e}"
