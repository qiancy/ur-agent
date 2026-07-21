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
    action: str,
    person_name: str,
    task: str,
    oid: int,
    due_date: Optional[str] = None,
) -> str:
    """
    Manage health reminders for a person.

    Args:
        action: Action type — 'add', 'update', or 'delete'.
        person_name: Name of the person.
        task: Task/reminder description.
        oid: Organization identifier.
        due_date: Due date for the task (optional).

    Returns:
        Operation confirmation or error message.
    """
    try:
        action = action.lower().strip()

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
def check_wellness(person_name: str, oid: int) -> str:
    """
    Check wellness / health information for a person.

    Args:
        person_name: Name of the person.
        oid: Organization identifier.

    Returns:
        Person information with health data, or error message.
    """
    try:
        people = query_person(oid, person_name)
        if people:
            return json.dumps(people[0], default=str, ensure_ascii=False)
        return f"Person '{person_name}' not found in org {oid}"
    except Exception as e:
        return f"Error checking wellness: {e}"
