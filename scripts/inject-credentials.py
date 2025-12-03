#!/usr/bin/env python3
"""Inject OAuth credentials into source code before building wheels.

This script replaces placeholder credentials in auth.py with real credentials
from environment variables before building PyPI wheels.

Usage:
    BUILD_GMAIL_CLIENT_ID=... BUILD_GMAIL_CLIENT_SECRET=... python scripts/inject-credentials.py
"""

import os
import re
import sys
from pathlib import Path

# Path to auth.py
AUTH_FILE = Path(__file__).parent.parent / "src" / "gmail_ai_unsub" / "gmail" / "auth.py"


def inject_credentials() -> None:
    """Inject credentials from environment into auth.py."""
    client_id = os.getenv("BUILD_GMAIL_CLIENT_ID")
    client_secret = os.getenv("BUILD_GMAIL_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(
            "Error: BUILD_GMAIL_CLIENT_ID and BUILD_GMAIL_CLIENT_SECRET must be set",
            file=sys.stderr,
        )
        sys.exit(1)

    # Read the file
    content = AUTH_FILE.read_text(encoding="utf-8")

    # Replace the client ID (look for the pattern)
    content = re.sub(
        r'_BUILD_CLIENT_ID = "[^"]*"',
        f'_BUILD_CLIENT_ID = "{client_id}"',
        content,
    )

    # Replace the client secret
    content = re.sub(
        r'_BUILD_CLIENT_SECRET = "[^"]*"',
        f'_BUILD_CLIENT_SECRET = "{client_secret}"',
        content,
    )

    # Write back
    AUTH_FILE.write_text(content, encoding="utf-8")
    print(f"✓ Injected credentials into {AUTH_FILE}")


if __name__ == "__main__":
    inject_credentials()
