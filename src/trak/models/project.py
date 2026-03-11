"""Project model for trak."""

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone


_KEY_PATTERN = re.compile(r"^[A-Z]{2,10}$")


@dataclass
class Project:
    id: int
    key: str
    name: str
    description: str | None
    created_at: str
    updated_at: str

    @classmethod
    def _validate_key(cls, key: str) -> None:
        if not _KEY_PATTERN.match(key):
            raise ValueError(
                f"Invalid project key '{key}': must be 2-10 uppercase letters."
            )

    @classmethod
    def create(
        cls,
        conn: sqlite3.Connection,
        key: str,
        name: str,
        description: str | None = None,
    ) -> "Project":
        cls._validate_key(key)
        now = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            "INSERT INTO projects (key, name, description, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (key, name, description, now, now),
        )
        conn.commit()
        return cls(
            id=cursor.lastrowid,
            key=key,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def get_by_key(cls, conn: sqlite3.Connection, key: str) -> "Project | None":
        row = conn.execute(
            "SELECT id, key, name, description, created_at, updated_at "
            "FROM projects WHERE key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        return cls(**dict(row))

    @classmethod
    def list_all(cls, conn: sqlite3.Connection) -> list["Project"]:
        rows = conn.execute(
            "SELECT id, key, name, description, created_at, updated_at "
            "FROM projects ORDER BY created_at DESC"
        ).fetchall()
        return [cls(**dict(r)) for r in rows]

    @classmethod
    def delete(cls, conn: sqlite3.Connection, key: str) -> None:
        cursor = conn.execute("DELETE FROM projects WHERE key = ?", (key,))
        conn.commit()
        if cursor.rowcount == 0:
            raise KeyError(f"Project '{key}' not found.")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
