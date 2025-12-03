"""Timing instrumentation for performance analysis."""

import time
from collections import defaultdict
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class TimingStats:
    """Statistics for a timing category."""

    total_time: float = 0.0
    count: int = 0
    min_time: float = float("inf")
    max_time: float = 0.0
    times: list[float] = field(default_factory=list)

    def add(self, duration: float) -> None:
        """Add a timing measurement."""
        self.total_time += duration
        self.count += 1
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.times.append(duration)

    @property
    def avg_time(self) -> float:
        """Average time for this category."""
        return self.total_time / self.count if self.count > 0 else 0.0

    @property
    def p50(self) -> float:
        """50th percentile (median)."""
        if not self.times:
            return 0.0
        sorted_times = sorted(self.times)
        mid = len(sorted_times) // 2
        if len(sorted_times) % 2 == 0:
            return (sorted_times[mid - 1] + sorted_times[mid]) / 2
        return sorted_times[mid]

    @property
    def p95(self) -> float:
        """95th percentile."""
        if not self.times:
            return 0.0
        sorted_times = sorted(self.times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[min(index, len(sorted_times) - 1)]

    @property
    def p99(self) -> float:
        """99th percentile."""
        if not self.times:
            return 0.0
        sorted_times = sorted(self.times)
        index = int(len(sorted_times) * 0.99)
        return sorted_times[min(index, len(sorted_times) - 1)]


class Timer:
    """Global timer for tracking performance metrics."""

    def __init__(self, enabled: bool = False) -> None:
        """Initialize timer.

        Args:
            enabled: Whether timing is enabled
        """
        self.enabled = enabled
        self.stats: dict[str, TimingStats] = defaultdict(TimingStats)
        self.current_timings: dict[str, float] = {}

    @contextmanager
    def time(self, category: str) -> Generator[None]:
        """Context manager to time an operation.

        Args:
            category: Category name for this timing (e.g., "llm_call", "gmail_api")

        Yields:
            None
        """
        if not self.enabled:
            yield
            return

        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.stats[category].add(duration)

    def time_sync(self, category: str, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Time a synchronous function call.

        Args:
            category: Category name for this timing
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function return value
        """
        if not self.enabled:
            return func(*args, **kwargs)

        with self.time(category):
            return func(*args, **kwargs)

    async def time_async(self, category: str, coro: Any) -> Any:
        """Time an async function call.

        Args:
            category: Category name for this timing
            coro: Coroutine to await

        Returns:
            Coroutine return value
        """
        if not self.enabled:
            return await coro

        start = time.perf_counter()
        try:
            result = await coro
        finally:
            duration = time.perf_counter() - start
            self.stats[category].add(duration)
        return result

    def get_stats(self) -> dict[str, TimingStats]:
        """Get all timing statistics."""
        return dict(self.stats)

    def reset(self) -> None:
        """Reset all timing statistics."""
        self.stats.clear()
        self.current_timings.clear()

    def format_summary(self) -> str:
        """Format timing statistics as a summary string."""
        if not self.enabled or not self.stats:
            return ""

        lines = ["\n[bold]Performance Summary:[/bold]\n"]
        lines.append(
            f"{'Category':<25} {'Count':<8} {'Total':<10} {'Avg':<10} {'Min':<10} {'Max':<10} {'P50':<10} {'P95':<10}"
        )
        lines.append("-" * 100)

        # Sort by total time descending
        sorted_stats = sorted(self.stats.items(), key=lambda x: x[1].total_time, reverse=True)

        for category, stats in sorted_stats:
            lines.append(
                f"{category:<25} {stats.count:<8} {stats.total_time:<10.3f} "
                f"{stats.avg_time:<10.3f} {stats.min_time:<10.3f} {stats.max_time:<10.3f} "
                f"{stats.p50:<10.3f} {stats.p95:<10.3f}"
            )

        total_time = sum(s.total_time for s in self.stats.values())
        lines.append("-" * 100)
        lines.append(f"{'TOTAL':<25} {'':<8} {total_time:<10.3f}")

        return "\n".join(lines)


# Global timer instance
_global_timer = Timer(enabled=False)


def get_timer() -> Timer:
    """Get the global timer instance."""
    return _global_timer


def enable_timing() -> None:
    """Enable global timing."""
    _global_timer.enabled = True


def disable_timing() -> None:
    """Disable global timing."""
    _global_timer.enabled = False


def reset_timing() -> None:
    """Reset global timing statistics."""
    _global_timer.reset()
