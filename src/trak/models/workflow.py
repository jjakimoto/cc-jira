"""Workflow model for trak."""

import json
import sqlite3
from dataclasses import dataclass, field


@dataclass
class Workflow:
    name: str
    statuses: list[str] = field(default_factory=list)
    transitions: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def get_by_name(cls, conn: sqlite3.Connection, name: str) -> "Workflow | None":
        """Retrieve a workflow by name, including statuses and transitions."""
        rows = conn.execute(
            "SELECT status FROM workflows WHERE name = ? ORDER BY position",
            (name,),
        ).fetchall()
        if not rows:
            return None

        statuses = [r["status"] for r in rows]

        trans_rows = conn.execute(
            "SELECT from_status, to_status FROM workflow_transitions WHERE workflow_name = ?",
            (name,),
        ).fetchall()
        transitions: dict[str, list[str]] = {}
        for r in trans_rows:
            transitions.setdefault(r["from_status"], []).append(r["to_status"])

        return cls(name=name, statuses=statuses, transitions=transitions)

    @classmethod
    def list_all(cls, conn: sqlite3.Connection) -> list["Workflow"]:
        """Return all workflows."""
        names = conn.execute(
            "SELECT DISTINCT name FROM workflows ORDER BY name"
        ).fetchall()
        workflows = []
        for row in names:
            wf = cls.get_by_name(conn, row["name"])
            if wf is not None:
                workflows.append(wf)
        return workflows

    @classmethod
    def create(
        cls,
        conn: sqlite3.Connection,
        name: str,
        statuses: list[str],
        transitions: dict[str, list[str]],
    ) -> "Workflow":
        """Create a custom workflow."""
        status_set = set(statuses)
        # Validate transitions reference valid statuses
        for from_s, to_list in transitions.items():
            if from_s not in status_set:
                raise ValueError(f"Transition references unknown status '{from_s}'.")
            for to_s in to_list:
                if to_s not in status_set:
                    raise ValueError(f"Transition references unknown status '{to_s}'.")

        for i, status in enumerate(statuses):
            is_default = 1 if i == 0 else 0
            conn.execute(
                "INSERT INTO workflows (name, status, position, is_default) VALUES (?, ?, ?, ?)",
                (name, status, i, is_default),
            )

        for from_s, to_list in transitions.items():
            for to_s in to_list:
                conn.execute(
                    "INSERT INTO workflow_transitions (workflow_name, from_status, to_status) "
                    "VALUES (?, ?, ?)",
                    (name, from_s, to_s),
                )

        conn.commit()
        return cls(name=name, statuses=statuses, transitions=transitions)

    @classmethod
    def validate_transition(
        cls,
        conn: sqlite3.Connection,
        from_status: str,
        to_status: str,
        workflow_name: str = "default",
    ) -> bool:
        """Check if a transition is valid. Raises ValueError if not."""
        row = conn.execute(
            "SELECT COUNT(*) FROM workflow_transitions "
            "WHERE workflow_name = ? AND from_status = ? AND to_status = ?",
            (workflow_name, from_status, to_status),
        ).fetchone()
        if row[0] > 0:
            return True

        # Get valid transitions for the error message
        valid_rows = conn.execute(
            "SELECT to_status FROM workflow_transitions "
            "WHERE workflow_name = ? AND from_status = ?",
            (workflow_name, from_status),
        ).fetchall()
        valid_list = [r["to_status"] for r in valid_rows]
        raise ValueError(
            f"Cannot transition from '{from_status}' to '{to_status}'. "
            f"Valid transitions: {', '.join(valid_list) if valid_list else 'none'}"
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "statuses": self.statuses,
            "transitions": self.transitions,
        }
