"""Tests for the email analysis cache."""

import tempfile
from pathlib import Path

import pytest

from gmail_ai_unsub.cache import EmailCache


@pytest.fixture
def temp_cache():
    """Create a temporary cache database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_cache.db"
        yield EmailCache(db_path)


def test_cache_mark_and_check(temp_cache):
    """Test marking an email as analyzed and checking it."""
    cache = temp_cache

    # Initially not analyzed
    assert not cache.is_analyzed("test_email_1")

    # Mark as analyzed
    cache.mark_analyzed(
        email_id="test_email_1",
        is_marketing=True,
        confidence=0.95,
        subject="Test Subject",
        from_address="test@example.com",
    )

    # Now should be analyzed
    assert cache.is_analyzed("test_email_1")


def test_cache_batch_lookup(temp_cache):
    """Test batch lookup of analyzed emails."""
    cache = temp_cache

    # Mark some emails
    cache.mark_analyzed("email_1", is_marketing=True)
    cache.mark_analyzed("email_2", is_marketing=False)

    # Batch lookup
    analyzed = cache.get_analyzed_ids(["email_1", "email_2", "email_3"])
    assert analyzed == {"email_1", "email_2"}


def test_cache_stats(temp_cache):
    """Test cache statistics."""
    cache = temp_cache

    # Initially empty
    stats = cache.get_stats()
    assert stats["total"] == 0
    assert stats["marketing"] == 0
    assert stats["non_marketing"] == 0

    # Add some entries
    cache.mark_analyzed("email_1", is_marketing=True, confidence=0.9)
    cache.mark_analyzed("email_2", is_marketing=True, confidence=0.8)
    cache.mark_analyzed("email_3", is_marketing=False, confidence=0.7)

    stats = cache.get_stats()
    assert stats["total"] == 3
    assert stats["marketing"] == 2
    assert stats["non_marketing"] == 1


def test_cache_clear(temp_cache):
    """Test clearing the cache."""
    cache = temp_cache

    # Add entries
    cache.mark_analyzed("email_1", is_marketing=True)
    cache.mark_analyzed("email_2", is_marketing=False)

    assert cache.get_stats()["total"] == 2

    # Clear
    count = cache.clear()
    assert count == 2
    assert cache.get_stats()["total"] == 0


def test_cache_remove(temp_cache):
    """Test removing a specific email from cache."""
    cache = temp_cache

    cache.mark_analyzed("email_1", is_marketing=True)
    assert cache.is_analyzed("email_1")

    # Remove
    removed = cache.remove("email_1")
    assert removed
    assert not cache.is_analyzed("email_1")

    # Remove non-existent
    removed = cache.remove("email_1")
    assert not removed


def test_cache_update_existing(temp_cache):
    """Test updating an existing cache entry."""
    cache = temp_cache

    # Initial entry
    cache.mark_analyzed("email_1", is_marketing=False, confidence=0.6)

    # Update (re-analyze with different result)
    cache.mark_analyzed("email_1", is_marketing=True, confidence=0.9)

    # Should still be one entry
    assert cache.get_stats()["total"] == 1
    assert cache.get_stats()["marketing"] == 1
