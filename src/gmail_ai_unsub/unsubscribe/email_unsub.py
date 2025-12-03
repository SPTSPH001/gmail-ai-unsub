"""Handle List-Unsubscribe header automation (mailto and HTTP POST)."""

from email.message import EmailMessage
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests

from gmail_ai_unsub.gmail.client import GmailClient
from gmail_ai_unsub.storage import UnsubscribeLink


def send_mailto_unsubscribe(
    client: GmailClient,
    mailto_address: str,
    original_message: dict[str, Any],
) -> bool:
    """Send unsubscribe email via mailto: link.

    Args:
        client: Gmail API client
        mailto_address: Email address from mailto: link
        original_message: Original Gmail message dict

    Returns:
        True if successful, False otherwise
    """
    try:
        # Parse mailto address (may contain subject/body params)
        parsed = urlparse(f"mailto:{mailto_address}")
        to_address = parsed.path
        params = parse_qs(parsed.query)

        # Get original message headers
        headers = original_message.get("payload", {}).get("headers", [])
        subject_prefix = "Unsubscribe"

        for header in headers:
            name = header.get("name", "").lower()
            if name == "from":
                break

        # Create unsubscribe email
        msg = EmailMessage()
        msg["To"] = to_address
        msg["Subject"] = params.get("subject", [f"Unsubscribe: {subject_prefix}"])[0]

        # Add unsubscribe body if specified in mailto params
        body = params.get("body", ["Please unsubscribe me from this mailing list."])[0]
        msg.set_content(body)

        # Convert to RFC 2822 format
        raw_message = msg.as_string()

        # Send via Gmail API
        client.send_message(raw_message)
        return True

    except Exception as e:
        print(f"Failed to send mailto unsubscribe: {e}")
        return False


def send_http_post_unsubscribe(url: str, original_message: dict[str, Any] | None = None) -> bool:
    """Send HTTP POST for one-click unsubscribe (RFC 8058).

    Args:
        url: Unsubscribe URL
        original_message: Original Gmail message (for context, not always needed)

    Returns:
        True if successful, False otherwise
    """
    try:
        # RFC 8058 one-click unsubscribe uses POST with List-Unsubscribe header value
        # Some services expect specific form data
        response = requests.post(
            url,
            data={"List-Unsubscribe": "One-Click"},
            headers={"User-Agent": "gmail-ai-unsub/0.1.0"},
            timeout=30,
            allow_redirects=True,
        )

        # Consider 2xx and 3xx as success
        return 200 <= response.status_code < 400

    except Exception as e:
        print(f"Failed to send HTTP POST unsubscribe: {e}")
        return False


def handle_list_unsubscribe(
    client: GmailClient,
    unsubscribe_link: UnsubscribeLink,
    original_message: dict[str, Any],
    enable_mailto: bool = True,
) -> bool:
    """Handle List-Unsubscribe header automation.

    Args:
        client: Gmail API client
        unsubscribe_link: UnsubscribeLink with header information
        original_message: Original Gmail message dict
        enable_mailto: Whether to attempt mailto: unsubscribe

    Returns:
        True if unsubscribe was successful, False otherwise
    """
    # Check for one-click HTTP POST
    if unsubscribe_link.link_url:
        # Check if it supports one-click (List-Unsubscribe-Post header)
        headers = original_message.get("payload", {}).get("headers", [])
        has_one_click = False
        for header in headers:
            if header.get(
                "name", ""
            ).lower() == "list-unsubscribe-post" and "List-Unsubscribe=One-Click" in header.get(
                "value", ""
            ):
                has_one_click = True
                break

        if has_one_click:
            return send_http_post_unsubscribe(unsubscribe_link.link_url, original_message)
        else:
            # Regular HTTP link - will need browser automation
            # Return False to indicate it needs browser handling
            return False

    # Handle mailto: unsubscribe
    if unsubscribe_link.mailto_address and enable_mailto:
        return send_mailto_unsubscribe(client, unsubscribe_link.mailto_address, original_message)

    return False
