"""State storage for unsubscribe links and processing status."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def expand_path(path: str) -> str:
    """Expand ~ and environment variables in path."""
    return str(Path(path).expanduser())


class UnsubscribeLink(BaseModel):
    """Stored unsubscribe link information."""

    email_id: str = Field(..., description="Gmail message ID")
    link_url: str | None = Field(None, description="Unsubscribe URL if found")
    mailto_address: str | None = Field(None, description="Mailto address if found")
    list_unsubscribe_header: str | None = Field(
        None, description="Raw List-Unsubscribe header value"
    )
    source: str = Field(..., description="Source: 'header', 'body', or 'manual'")
    status: str = Field(default="pending", description="Status: 'pending', 'success', 'failed'")
    error: str | None = Field(None, description="Error message if failed")


class StateStorage:
    """JSON-based state storage for unsubscribe links."""

    def __init__(self, state_file: str) -> None:
        """Initialize state storage.

        Args:
            state_file: Path to JSON state file
        """
        self.state_file = Path(expand_path(state_file))
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        """Load state from JSON file."""
        if not self.state_file.exists():
            return {"unsubscribe_links": {}, "unsubscribed_senders": {}}

        try:
            with open(self.state_file, encoding="utf-8") as f:
                state = json.load(f)
                # Ensure unsubscribed_senders exists for backward compatibility
                if "unsubscribed_senders" not in state:
                    state["unsubscribed_senders"] = {}
                return state
        except (OSError, json.JSONDecodeError):
            return {"unsubscribe_links": {}, "unsubscribed_senders": {}}

    def _save(self) -> None:
        """Save state to JSON file."""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2, ensure_ascii=False)

    def add_unsubscribe_link(self, link: UnsubscribeLink) -> None:
        """Add or update an unsubscribe link."""
        if "unsubscribe_links" not in self._state:
            self._state["unsubscribe_links"] = {}

        self._state["unsubscribe_links"][link.email_id] = link.model_dump()
        self._save()

    def get_unsubscribe_link(self, email_id: str) -> UnsubscribeLink | None:
        """Get unsubscribe link for an email ID."""
        links = self._state.get("unsubscribe_links", {})
        link_data = links.get(email_id)
        if link_data:
            return UnsubscribeLink(**link_data)
        return None

    def get_pending_links(self) -> list[UnsubscribeLink]:
        """Get all pending unsubscribe links."""
        links = self._state.get("unsubscribe_links", {})
        return [
            UnsubscribeLink(**link_data)
            for link_data in links.values()
            if link_data.get("status") == "pending"
        ]

    def update_link_status(self, email_id: str, status: str, error: str | None = None) -> None:
        """Update the status of an unsubscribe link."""
        links = self._state.get("unsubscribe_links", {})
        if email_id in links:
            links[email_id]["status"] = status
            if error:
                links[email_id]["error"] = error
            else:
                links[email_id].pop("error", None)
            self._save()

    def get_all_links(self) -> list[UnsubscribeLink]:
        """Get all stored unsubscribe links."""
        links = self._state.get("unsubscribe_links", {})
        return [UnsubscribeLink(**link_data) for link_data in links.values()]

    def _normalize_sender(self, sender: str) -> str:
        """Normalize sender email address.

        Extracts email from "Name <email@domain.com>" format and lowercases it.

        Args:
            sender: Sender address (can be just email or "Name <email>")

        Returns:
            Normalized email address
        """
        import re

        # Extract email from "Name <email@domain.com>" format
        email_match = re.search(r"<([^>]+)>", sender)
        if email_match:
            return email_match.group(1).lower().strip()

        # If no angle brackets, use the whole string
        return sender.lower().strip()

    def record_unsubscribed_sender(self, sender: str, email_date: datetime) -> None:
        """Record a successful unsubscribe for a sender.

        Args:
            sender: Sender email address
            email_date: Date of the email that was unsubscribed from
        """
        if "unsubscribed_senders" not in self._state:
            self._state["unsubscribed_senders"] = {}

        normalized_sender = self._normalize_sender(sender)
        self._state["unsubscribed_senders"][normalized_sender] = {
            "last_unsubscribed_date": email_date.isoformat(),
        }
        self._save()

    def should_unsubscribe_from_sender(self, sender: str, email_date: datetime) -> bool:
        """Check if we should unsubscribe from a sender.

        Returns False if we've already unsubscribed from this sender
        and the email date is before or equal to the last unsubscribed date.
        Returns True if we haven't unsubscribed before, or if this email
        is newer than the last unsubscribed date (they may have resubscribed).

        Args:
            sender: Sender email address
            email_date: Date of the email to check

        Returns:
            True if we should attempt unsubscribe, False if we've already done it
        """
        if "unsubscribed_senders" not in self._state:
            return True

        normalized_sender = self._normalize_sender(sender)
        sender_data = self._state["unsubscribed_senders"].get(normalized_sender)

        if not sender_data:
            # Never unsubscribed from this sender
            return True

        # Check if email is newer than last unsubscribed date
        last_unsub_date_str = sender_data.get("last_unsubscribed_date")
        if not last_unsub_date_str:
            return True

        try:
            last_unsub_date = datetime.fromisoformat(last_unsub_date_str)
            # If email is newer than last unsub, they may have resubscribed
            return email_date > last_unsub_date
        except (ValueError, TypeError):
            # If date parsing fails, assume we should unsubscribe
            return True

    def get_last_unsubscribed_date(self, sender: str) -> datetime | None:
        """Get the last date we unsubscribed from a sender.

        Args:
            sender: Sender email address

        Returns:
            Last unsubscribed date, or None if never unsubscribed
        """
        if "unsubscribed_senders" not in self._state:
            return None

        normalized_sender = self._normalize_sender(sender)
        sender_data = self._state["unsubscribed_senders"].get(normalized_sender)

        if not sender_data:
            return None

        last_unsub_date_str = sender_data.get("last_unsubscribed_date")
        if not last_unsub_date_str:
            return None

        try:
            return datetime.fromisoformat(last_unsub_date_str)
        except (ValueError, TypeError):
            return None
