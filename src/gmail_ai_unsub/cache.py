"""Email analysis cache using SQLite.

Stores which emails have been analyzed to avoid re-processing and burning tokens.
Uses SQLite for durability (survives Ctrl+C) and fast lookups.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from gmail_ai_unsub.paths import get_cache_dir


def get_cache_db_path() -> Path:
    """Get the path to the cache database."""
    return get_cache_dir(ensure_exists=True) / "analyzed_emails.db"


class EmailCache:
    """Cache for tracking analyzed emails.

    Uses SQLite for:
    - Durability: Commits after each insert, survives Ctrl+C
    - Fast lookups: Indexed by email_id
    - Low memory: Only loads what's needed
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        """Initialize the email cache.

        Args:
            db_path: Path to SQLite database. If None, uses default cache location.
        """
        if db_path is None:
            db_path = get_cache_db_path()
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analyzed_emails (
                    email_id TEXT PRIMARY KEY,
                    analyzed_at TEXT NOT NULL,
                    is_marketing INTEGER NOT NULL,
                    confidence REAL,
                    subject TEXT,
                    from_address TEXT
                )
            """)
            # Index for fast date-based queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_analyzed_at
                ON analyzed_emails(analyzed_at)
            """)
            conn.commit()

    def is_analyzed(self, email_id: str) -> bool:
        """Check if an email has already been analyzed.

        Args:
            email_id: Gmail message ID

        Returns:
            True if email was previously analyzed
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM analyzed_emails WHERE email_id = ?",
                (email_id,),
            )
            return cursor.fetchone() is not None

    def get_analyzed_ids(self, email_ids: list[str]) -> set[str]:
        """Get which of the given email IDs have been analyzed.

        More efficient than calling is_analyzed() for each ID.

        Args:
            email_ids: List of Gmail message IDs to check

        Returns:
            Set of email IDs that have been analyzed
        """
        if not email_ids:
            return set()

        with sqlite3.connect(self.db_path) as conn:
            # Use parameterized query with placeholders
            placeholders = ",".join("?" * len(email_ids))
            cursor = conn.execute(
                f"SELECT email_id FROM analyzed_emails WHERE email_id IN ({placeholders})",
                email_ids,
            )
            return {row[0] for row in cursor.fetchall()}

    def mark_analyzed(
        self,
        email_id: str,
        is_marketing: bool,
        confidence: float | None = None,
        subject: str | None = None,
        from_address: str | None = None,
    ) -> None:
        """Mark an email as analyzed.

        Commits immediately to survive Ctrl+C.

        Args:
            email_id: Gmail message ID
            is_marketing: Whether the email was classified as marketing
            confidence: Classification confidence score
            subject: Email subject (for debugging/auditing)
            from_address: Sender address (for debugging/auditing)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO analyzed_emails
                (email_id, analyzed_at, is_marketing, confidence, subject, from_address)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    email_id,
                    datetime.now().isoformat(),
                    1 if is_marketing else 0,
                    confidence,
                    subject,
                    from_address,
                ),
            )
            conn.commit()

    def remove(self, email_id: str) -> bool:
        """Remove an email from the cache.

        Useful when user manually changes labels and wants to re-analyze.

        Args:
            email_id: Gmail message ID

        Returns:
            True if email was in cache and removed
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM analyzed_emails WHERE email_id = ?",
                (email_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def clear(self) -> int:
        """Clear all cached email analysis results.

        Returns:
            Number of entries cleared
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM analyzed_emails")
            count = cursor.fetchone()[0]
            conn.execute("DELETE FROM analyzed_emails")
            conn.commit()
            return count

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dict with total, marketing, and non_marketing counts
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN is_marketing = 1 THEN 1 ELSE 0 END) as marketing,
                    SUM(CASE WHEN is_marketing = 0 THEN 1 ELSE 0 END) as non_marketing
                FROM analyzed_emails
            """)
            row = cursor.fetchone()
            return {
                "total": row[0] or 0,
                "marketing": row[1] or 0,
                "non_marketing": row[2] or 0,
            }

    def vacuum(self) -> None:
        """Optimize the database file size."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("VACUUM")
