"""Issue model for trak."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from trak.models.workflow import Workflow


@dataclass
class Issue:
    id: int
    project_id: int
    number: int
    type: str
    summary: str
    description: str | None
    status: str
    priority: str
    assignee: str | None
    labels: str | None
    created_at: str
    updated_at: str

    @property
    def key(self) -> str:
        """Return the issue key (e.g. MP-1). Requires project_key to be set."""
        return f"{self._project_key}-{self.number}" if hasattr(self, "_project_key") else f"?-{self.number}"

    def _set_project_key(self, project_key: str) -> None:
        object.__setattr__(self, "_project_key", project_key)

    @classmethod
    def create(
        cls,
        conn: sqlite3.Connection,
        project_id: int,
        summary: str,
        type: str = "task",
        description: str | None = None,
        priority: str = "p2",
        assignee: str | None = None,
        labels: str | None = None,
    ) -> "Issue":
        now = datetime.now(timezone.utc).isoformat()
        # Auto-increment number per project
        row = conn.execute(
            "SELECT COALESCE(MAX(number), 0) FROM issues WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        next_number = row[0] + 1

        cursor = conn.execute(
            "INSERT INTO issues (project_id, number, type, summary, description, "
            "status, priority, assignee, labels, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'todo', ?, ?, ?, ?, ?)",
            (project_id, next_number, type, summary, description, priority, assignee, labels, now, now),
        )
        conn.commit()
        return cls(
            id=cursor.lastrowid,
            project_id=project_id,
            number=next_number,
            type=type,
            summary=summary,
            description=description,
            status="todo",
            priority=priority,
            assignee=assignee,
            labels=labels,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def get_by_key(cls, conn: sqlite3.Connection, key: str) -> "Issue | None":
        """Retrieve an issue by its key (e.g. 'MP-1')."""
        parts = key.rsplit("-", 1)
        if len(parts) != 2:
            return None
        project_key, num_str = parts
        try:
            number = int(num_str)
        except ValueError:
            return None

        row = conn.execute(
            "SELECT i.id, i.project_id, i.number, i.type, i.summary, i.description, "
            "i.status, i.priority, i.assignee, i.labels, i.created_at, i.updated_at, "
            "p.key AS project_key "
            "FROM issues i JOIN projects p ON i.project_id = p.id "
            "WHERE p.key = ? AND i.number = ?",
            (project_key, number),
        ).fetchone()
        if row is None:
            return None
        d = dict(row)
        pkey = d.pop("project_key")
        issue = cls(**d)
        issue._set_project_key(pkey)
        return issue

    @classmethod
    def list_all(
        cls,
        conn: sqlite3.Connection,
        project_key: str | None = None,
        status: str | None = None,
        assignee: str | None = None,
        label: str | None = None,
        priority: str | None = None,
    ) -> list["Issue"]:
        query = (
            "SELECT i.id, i.project_id, i.number, i.type, i.summary, i.description, "
            "i.status, i.priority, i.assignee, i.labels, i.created_at, i.updated_at, "
            "p.key AS project_key "
            "FROM issues i JOIN projects p ON i.project_id = p.id"
        )
        conditions: list[str] = []
        params: list[str] = []
        if project_key is not None:
            conditions.append("p.key = ?")
            params.append(project_key)
        if status is not None:
            conditions.append("i.status = ?")
            params.append(status)
        if assignee is not None:
            conditions.append("i.assignee = ?")
            params.append(assignee)
        if priority is not None:
            conditions.append("i.priority = ?")
            params.append(priority)
        if label is not None:
            conditions.append("i.labels LIKE ?")
            params.append(f"%{label}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY i.created_at DESC"

        rows = conn.execute(query, params).fetchall()
        issues = []
        for r in rows:
            d = dict(r)
            pkey = d.pop("project_key")
            issue = cls(**d)
            issue._set_project_key(pkey)
            issues.append(issue)
        return issues

    @classmethod
    def update(
        cls,
        conn: sqlite3.Connection,
        key: str,
        status: str | None = None,
        assignee: str | None = None,
        priority: str | None = None,
        summary: str | None = None,
        type: str | None = None,
        labels: str | None = None,
    ) -> "Issue":
        issue = cls.get_by_key(conn, key)
        if issue is None:
            raise KeyError(f"Issue '{key}' not found.")

        updates: list[str] = []
        params: list = []
        if status is not None:
            Workflow.validate_transition(conn, issue.status, status)
            updates.append("status = ?")
            params.append(status)
        if assignee is not None:
            updates.append("assignee = ?")
            params.append(assignee)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        if summary is not None:
            updates.append("summary = ?")
            params.append(summary)
        if type is not None:
            updates.append("type = ?")
            params.append(type)
        if labels is not None:
            updates.append("labels = ?")
            params.append(labels)

        if not updates:
            return issue

        now = datetime.now(timezone.utc).isoformat()
        updates.append("updated_at = ?")
        params.append(now)
        params.append(issue.id)

        conn.execute(
            f"UPDATE issues SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()
        return cls.get_by_key(conn, key)

    @classmethod
    def delete(cls, conn: sqlite3.Connection, key: str) -> None:
        issue = cls.get_by_key(conn, key)
        if issue is None:
            raise KeyError(f"Issue '{key}' not found.")
        conn.execute("DELETE FROM issues WHERE id = ?", (issue.id,))
        conn.commit()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "project_id": self.project_id,
            "number": self.number,
            "type": self.type,
            "summary": self.summary,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "assignee": self.assignee,
            "labels": self.labels,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
