"""Comment model for trak."""

import getpass
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Comment:
    id: int
    issue_id: int
    author: str
    body: str
    created_at: str

    @classmethod
    def add(
        cls,
        conn: sqlite3.Connection,
        issue_id: int,
        body: str,
        author: str | None = None,
    ) -> "Comment":
        if author is None:
            author = getpass.getuser()
        now = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            "INSERT INTO comments (issue_id, author, body, created_at) VALUES (?, ?, ?, ?)",
            (issue_id, author, body, now),
        )
        conn.commit()
        return cls(
            id=cursor.lastrowid,
            issue_id=issue_id,
            author=author,
            body=body,
            created_at=now,
        )

    @classmethod
    def list_for_issue(cls, conn: sqlite3.Connection, issue_id: int) -> list["Comment"]:
        rows = conn.execute(
            "SELECT id, issue_id, author, body, created_at "
            "FROM comments WHERE issue_id = ? ORDER BY created_at ASC",
            (issue_id,),
        ).fetchall()
        return [cls(**dict(r)) for r in rows]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "issue_id": self.issue_id,
            "author": self.author,
            "body": self.body,
            "created_at": self.created_at,
        }
