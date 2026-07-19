from typing import Optional
from langchain_core.tools import tool
import psycopg2
from psycopg2.extras import RealDictCursor
import json

from src.db.database import get_db_connection

@tool
def manage_reminder(action: str, person_name: str, task: str, due_date: Optional[str] = None) -> str:
    """
    Manage personnel reminders and tasks.
    
    Args:
        action (str): Action type (add, update, delete)
        person_name (str): Name of the person
        task (str): Task description
        due_date (Optional[str]): Due date for the task (optional)
        
    Returns:
        str: Operation confirmation or error message
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Normalize action to lowercase
        action = action.lower().strip()
        
        if action == "add":
            # Insert new reminder
            cur.execute("""
                INSERT INTO personnel (name, role, health_reminders)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (person_name, "reminder", json.dumps({"task": task, "due_date": due_date})))
            
            person_id = cur.fetchone()[0]
            conn.commit()
            return f"Successfully added reminder for {person_name}: {task}"
            
        elif action == "update":
            # Update existing reminder
            cur.execute("""
                UPDATE personnel 
                SET health_reminders = %s
                WHERE name = %s AND role = 'reminder'
            """, (json.dumps({"task": task, "due_date": due_date}), person_name))
            
            if cur.rowcount > 0:
                conn.commit()
                return f"Successfully updated reminder for {person_name}: {task}"
            else:
                return f"No reminder found for {person_name}"
                
        elif action == "delete":
            # Delete reminder
            cur.execute("""
                DELETE FROM personnel 
                WHERE name = %s AND role = 'reminder'
            """, (person_name,))
            
            if cur.rowcount > 0:
                conn.commit()
                return f"Successfully deleted reminder for {person_name}"
            else:
                return f"No reminder found for {person_name}"
        else:
            return f"Invalid action: {action}. Use 'add', 'update', or 'delete'"
            
    except Exception as e:
        return f"Error managing reminder: {str(e)}"
    finally:
        if conn:
            conn.close()

@tool
def check_wellness(person_name: str, context_id: int) -> str:
    """
    Check wellness information for a person in a specific context.
    
    Args:
        person_name (str): Name of the person
        context_id (int): Context identifier for multi-tenant isolation
        
    Returns:
        str: Wellness information or error message
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query wellness information
        cur.execute("""
            SELECT * FROM personnel 
            WHERE context_id = %s AND name = %s
        """, (context_id, person_name))
        
        person = cur.fetchone()
        
        if person:
            # Convert to regular dict for JSON serialization
            person_data = dict(person)
            return json.dumps(person_data, default=str)
        else:
            return f"No person found with name '{person_name}' in context {context_id}"
            
    except Exception as e:
        return f"Error checking wellness: {str(e)}"
    finally:
        if conn:
            conn.close()
