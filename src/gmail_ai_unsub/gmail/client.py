"""Gmail API client with rate limiting and error handling."""

import time
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gmail_ai_unsub.gmail.auth import get_credentials
from gmail_ai_unsub.gmail.labels import LabelManager


class GmailClient:
    """Gmail API client with automatic retry and rate limiting."""

    def __init__(
        self,
        credentials_file: str | None,
        token_file: str,
        max_retries: int = 3,
        use_default_credentials: bool = True,
    ) -> None:
        """Initialize Gmail client.

        Args:
            credentials_file: Path to OAuth2 credentials JSON. If None,
                uses embedded default credentials.
            token_file: Path to OAuth2 token cache
            max_retries: Maximum number of retries for rate-limited requests
            use_default_credentials: If True and credentials_file doesn't exist,
                use embedded default credentials.
        """
        creds = get_credentials(credentials_file, token_file, use_default_credentials)
        self.service = build("gmail", "v1", credentials=creds)
        self.labels = LabelManager(self.service)
        self.max_retries = max_retries

    def _execute_with_retry(self, request: Any, operation_name: str = "API call") -> Any:
        """Execute API request with exponential backoff retry.

        Args:
            request: Google API request object
            operation_name: Name of operation for error messages

        Returns:
            API response

        Raises:
            HttpError: If request fails after max retries
        """
        for attempt in range(self.max_retries):
            try:
                return request.execute()
            except HttpError as error:
                if error.resp.status == 429:  # Rate limit exceeded
                    if attempt < self.max_retries - 1:
                        # Exponential backoff: 2^attempt seconds
                        wait_time = 2**attempt
                        print(
                            f"Rate limit hit. Waiting {wait_time}s before retry "
                            f"{attempt + 1}/{self.max_retries}..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise RuntimeError(
                            f"{operation_name} failed after {self.max_retries} retries "
                            f"due to rate limiting. Please try again later."
                        ) from error
                else:
                    # Non-rate-limit error, don't retry
                    raise

        raise RuntimeError(f"{operation_name} failed unexpectedly")

    def list_messages(
        self,
        query: str = "",
        max_results: int = 100,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List messages matching a query.

        Args:
            query: Gmail search query (e.g., "is:unread", "from:example.com")
            max_results: Maximum number of results per page
            page_token: Token for pagination

        Returns:
            Dict with 'messages' list and 'nextPageToken' if more results available
        """
        request = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results, pageToken=page_token)
        )
        return self._execute_with_retry(request, "List messages")

    def get_message(self, message_id: str, format: str = "full") -> dict[str, Any]:  # noqa: A002
        """Get a message by ID.

        Args:
            message_id: Gmail message ID
            format: Message format: 'full', 'metadata', 'minimal', or 'raw'

        Returns:
            Message dict
        """
        request = self.service.users().messages().get(userId="me", id=message_id, format=format)
        return self._execute_with_retry(request, f"Get message {message_id}")

    def get_message_metadata(self, message_id: str) -> dict[str, Any]:
        """Get message metadata (headers only, quota-efficient).

        Args:
            message_id: Gmail message ID

        Returns:
            Message dict with metadata format
        """
        return self.get_message(message_id, format="metadata")

    def send_message(self, raw_message: str | bytes) -> dict[str, Any]:
        """Send an email message.

        Args:
            raw_message: Raw RFC 2822 formatted message (string or bytes)

        Returns:
            Sent message dict
        """
        import base64

        if isinstance(raw_message, bytes):
            raw_message_str = raw_message.decode("utf-8")
        else:
            raw_message_str = raw_message

        # Gmail API expects base64url encoded string
        message_bytes = raw_message_str.encode("utf-8")
        encoded = base64.urlsafe_b64encode(message_bytes).decode("utf-8")

        request = self.service.users().messages().send(userId="me", body={"raw": encoded})
        return self._execute_with_retry(request, "Send message")
