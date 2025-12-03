"""Gmail label management."""

from typing import Any

from googleapiclient.errors import HttpError


class LabelManager:
    """Manages Gmail labels for organizing emails."""

    def __init__(self, service: Any) -> None:
        """Initialize label manager.

        Args:
            service: Gmail API service object
        """
        self.service = service
        self._label_cache: dict[str, str] | None = None

    def _get_all_labels(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Get all labels, with caching.

        Args:
            force_refresh: Force refresh of the cache

        Returns:
            List of label dicts
        """
        if self._label_cache is None or force_refresh:
            results = self.service.users().labels().list(userId="me").execute()
            return results.get("labels", [])
        return []

    def get_or_create_label(self, label_name: str) -> str:
        """Get existing label ID or create a new label.

        Args:
            label_name: Name of the label (can be hierarchical like "Parent/Child")

        Returns:
            Label ID
        """
        # Check if label already exists
        existing = self._find_label(label_name)
        if existing:
            return existing["id"]

        # Try to create the label, handling 409 conflicts gracefully
        try:
            return self._create_label(label_name)
        except HttpError as e:
            if e.resp.status == 409:
                # Label was created by another process or exists with different case
                # Refresh cache and try to find it again
                existing = self._find_label(label_name, force_refresh=True)
                if existing:
                    return existing["id"]
                # If still not found, the conflict might be due to case sensitivity
                # Try a case-insensitive search
                existing = self._find_label_case_insensitive(label_name)
                if existing:
                    return existing["id"]
                raise RuntimeError(
                    f"Label '{label_name}' conflicts with an existing label but could not be found. "
                    "This may be due to a label with different capitalization."
                ) from e
            raise

    def _create_label(self, label_name: str) -> str:
        """Create a new label.

        Args:
            label_name: Full label name

        Returns:
            Label ID
        """
        # For simple labels (no hierarchy), create directly with full name
        # Gmail API accepts the full path as the name
        label_obj = {
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        }

        created = self.service.users().labels().create(userId="me", body=label_obj).execute()
        return created["id"]

    def _find_label(self, label_name: str, force_refresh: bool = False) -> dict[str, Any] | None:
        """Find a label by name.

        Gmail stores hierarchical labels with the full path as the name,
        e.g., "Parent/Child" is stored as name="Parent/Child".

        Args:
            label_name: Label name (can include "/" for hierarchy)
            force_refresh: Force refresh of label list

        Returns:
            Label dict or None if not found
        """
        results = self.service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        # Gmail stores the full path as the label name
        for label in labels:
            if label.get("name") == label_name:
                return label

        return None

    def _find_label_case_insensitive(self, label_name: str) -> dict[str, Any] | None:
        """Find a label by name, case-insensitive.

        Args:
            label_name: Label name to search for

        Returns:
            Label dict or None if not found
        """
        results = self.service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        label_name_lower = label_name.lower()
        for label in labels:
            if label.get("name", "").lower() == label_name_lower:
                return label

        return None

    def _find_label_fuzzy(self, label_name: str) -> dict[str, Any] | None:
        """Find a label by name with fuzzy matching.

        Handles common variations like hyphens vs spaces, case differences.

        Args:
            label_name: Label name to search for

        Returns:
            Label dict or None if not found
        """
        results = self.service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        # Normalize: lowercase, replace hyphens/underscores with spaces
        def normalize(s: str) -> str:
            return s.lower().replace("-", " ").replace("_", " ")

        target = normalize(label_name)
        for label in labels:
            if normalize(label.get("name", "")) == target:
                return label

        return None

    def get_label_id(self, label_name: str) -> str | None:
        """Get label ID by name, with fuzzy matching fallback.

        Unlike get_or_create_label, this does NOT create the label if missing.

        Args:
            label_name: Label name to find

        Returns:
            Label ID or None if not found
        """
        # Try exact match first
        label = self._find_label(label_name)
        if label:
            return label["id"]

        # Try case-insensitive
        label = self._find_label_case_insensitive(label_name)
        if label:
            return label["id"]

        # Try fuzzy match
        label = self._find_label_fuzzy(label_name)
        if label:
            return label["id"]

        return None

    def apply_label(self, message_id: str, label_id: str) -> None:
        """Apply a label to a message.

        Args:
            message_id: Gmail message ID
            label_id: Label ID to apply
        """
        self.service.users().messages().modify(
            userId="me", id=message_id, body={"addLabelIds": [label_id]}
        ).execute()

    def remove_label(self, message_id: str, label_id: str) -> None:
        """Remove a label from a message.

        Args:
            message_id: Gmail message ID
            label_id: Label ID to remove
        """
        self.service.users().messages().modify(
            userId="me", id=message_id, body={"removeLabelIds": [label_id]}
        ).execute()

    def apply_labels(
        self,
        message_id: str,
        add_label_ids: list[str] | None = None,
        remove_label_ids: list[str] | None = None,
    ) -> None:
        """Apply and/or remove multiple labels at once.

        Args:
            message_id: Gmail message ID
            add_label_ids: List of label IDs to add
            remove_label_ids: List of label IDs to remove
        """
        body: dict[str, list[str]] = {}
        if add_label_ids:
            body["addLabelIds"] = add_label_ids
        if remove_label_ids:
            body["removeLabelIds"] = remove_label_ids

        if body:
            self.service.users().messages().modify(userId="me", id=message_id, body=body).execute()
