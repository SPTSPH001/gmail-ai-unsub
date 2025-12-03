"""Tests for storage module."""

from pathlib import Path

from gmail_ai_unsub.storage import StateStorage, UnsubscribeLink


def test_storage_add_and_get(tmp_path: Path) -> None:
    """Test adding and retrieving unsubscribe links."""
    state_file = tmp_path / "state.json"
    storage = StateStorage(str(state_file))

    link = UnsubscribeLink(
        email_id="test123",
        link_url="https://example.com/unsub",
        source="header",
    )

    storage.add_unsubscribe_link(link)

    retrieved = storage.get_unsubscribe_link("test123")
    assert retrieved is not None
    assert retrieved.email_id == "test123"
    assert retrieved.link_url == "https://example.com/unsub"


def test_storage_pending_links(tmp_path: Path) -> None:
    """Test getting pending unsubscribe links."""
    state_file = tmp_path / "state.json"
    storage = StateStorage(str(state_file))

    link1 = UnsubscribeLink(
        email_id="test1",
        link_url="https://example.com/unsub1",
        source="header",
        status="pending",
    )
    link2 = UnsubscribeLink(
        email_id="test2",
        link_url="https://example.com/unsub2",
        source="header",
        status="success",
    )

    storage.add_unsubscribe_link(link1)
    storage.add_unsubscribe_link(link2)

    pending = storage.get_pending_links()
    assert len(pending) == 1
    assert pending[0].email_id == "test1"


def test_storage_update_status(tmp_path: Path) -> None:
    """Test updating link status."""
    state_file = tmp_path / "state.json"
    storage = StateStorage(str(state_file))

    link = UnsubscribeLink(
        email_id="test123",
        link_url="https://example.com/unsub",
        source="header",
        status="pending",
    )

    storage.add_unsubscribe_link(link)
    storage.update_link_status("test123", "success")

    updated = storage.get_unsubscribe_link("test123")
    assert updated is not None
    assert updated.status == "success"
