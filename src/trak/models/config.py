"""Config model for trak."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Config:
    key: str
    value: str
    updated_at: str

    @classmethod
    def get(cls, conn: sqlite3.Connection, key: str) -> "Config | None":
        """Retrieve a config value by key."""
        row = conn.execute(
            "SELECT key, value, updated_at FROM config WHERE key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        return cls(**dict(row))

    @classmethod
    def set_value(cls, conn: sqlite3.Connection, key: str, value: str) -> "Config":
        """Set a config value (insert or replace)."""
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, now),
        )
        conn.commit()
        return cls(key=key, value=value, updated_at=now)

    @classmethod
    def list_all(cls, conn: sqlite3.Connection) -> list["Config"]:
        """Return all config entries ordered by key."""
        rows = conn.execute(
            "SELECT key, value, updated_at FROM config ORDER BY key"
        ).fetchall()
        return [cls(**dict(r)) for r in rows]

    @classmethod
    def delete(cls, conn: sqlite3.Connection, key: str) -> None:
        """Delete a config entry by key."""
        cfg = cls.get(conn, key)
        if cfg is None:
            raise KeyError(f"Config key '{key}' not found.")
        conn.execute("DELETE FROM config WHERE key = ?", (key,))
        conn.commit()

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at,
        }
