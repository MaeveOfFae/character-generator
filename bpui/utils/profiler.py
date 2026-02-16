"""Performance profiling utilities."""

import time
import logging
from contextlib import contextmanager
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class ProfileEntry:
    """A single profiling measurement."""
    name: str
    duration: float
    timestamp: float
    metadata: Dict = field(default_factory=dict)


class Profiler:
    """Simple profiler for tracking operation timings."""
    
    def __init__(self, enabled: bool = True):
        """Initialize profiler.
        
        Args:
            enabled: Whether profiling is enabled
        """
        self.enabled = enabled
        self.entries: List[ProfileEntry] = []
        self._start_time = time.time()
    
    @contextmanager
    def profile(self, name: str, **metadata):
        """Context manager for profiling a code block.
        
        Args:
            name: Name of the operation
            **metadata: Additional metadata to store
        
        Example:
            with profiler.profile("load_blueprint", asset="system_prompt"):
                result = load_blueprint("system_prompt")
        """
        if not self.enabled:
            yield
            return
        
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.entries.append(ProfileEntry(
                name=name,
                duration=duration,
                timestamp=start - self._start_time,
                metadata=metadata
            ))
            logger.debug(f"[PROFILE] {name}: {duration*1000:.2f}ms {metadata}")
    
    def profile_decorator(self, name: Optional[str] = None, **metadata):
        """Decorator for profiling a function.
        
        Args:
            name: Name of the operation (defaults to function name)
            **metadata: Additional metadata to store
        
        Example:
            @profiler.profile_decorator("parse_output")
            def parse_blueprint_output(text):
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                op_name = name or func.__name__
                with self.profile(op_name, **metadata):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_summary(self) -> Dict:
        """Get profiling summary.
        
        Returns:
            Dict with total time, operation counts, and timing breakdown
        """
        if not self.entries:
            return {
                "total_time": 0.0,
                "operation_count": 0,
                "operations": {}
            }
        
        # Group by operation name
        operations: Dict[str, List[float]] = {}
        for entry in self.entries:
            if entry.name not in operations:
                operations[entry.name] = []
            operations[entry.name].append(entry.duration)
        
        # Calculate stats for each operation
        operation_stats = {}
        for name, durations in operations.items():
            operation_stats[name] = {
                "count": len(durations),
                "total": sum(durations),
                "mean": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations)
            }
        
        return {
            "total_time": sum(e.duration for e in self.entries),
            "operation_count": len(self.entries),
            "operations": operation_stats
        }
    
    def print_report(self):
        """Print a formatted profiling report."""
        if not self.enabled:
            logger.info("Profiling was not enabled")
            return
        
        if not self.entries:
            logger.info("No profiling data collected")
            return
        
        summary = self.get_summary()
        
        print("\n" + "=" * 70)
        print("PERFORMANCE PROFILE")
        print("=" * 70)
        print(f"Total time: {summary['total_time']:.3f}s")
        print(f"Operations: {summary['operation_count']}")
        print("\nBreakdown by operation:")
        print("-" * 70)
        print(f"{'Operation':<30} {'Count':>8} {'Total':>10} {'Mean':>10} {'Min':>8} {'Max':>8}")
        print("-" * 70)
        
        # Sort by total time (descending)
        sorted_ops = sorted(
            summary['operations'].items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )
        
        for name, stats in sorted_ops:
            print(f"{name:<30} {stats['count']:>8} "
                  f"{stats['total']:>9.3f}s {stats['mean']:>9.3f}s "
                  f"{stats['min']:>7.3f}s {stats['max']:>7.3f}s")
        
        print("=" * 70 + "\n")
    
    def get_timeline(self) -> List[Dict]:
        """Get timeline of operations.
        
        Returns:
            List of operations with timestamps
        """
        return [
            {
                "name": entry.name,
                "timestamp": entry.timestamp,
                "duration": entry.duration,
                "metadata": entry.metadata
            }
            for entry in self.entries
        ]
    
    def reset(self):
        """Reset profiler state."""
        self.entries.clear()
        self._start_time = time.time()


# Global profiler instance
_global_profiler: Optional[Profiler] = None


def get_profiler() -> Profiler:
    """Get the global profiler instance."""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = Profiler(enabled=False)
    return _global_profiler


def set_profiler(profiler: Profiler):
    """Set the global profiler instance."""
    global _global_profiler
    _global_profiler = profiler


def enable_profiling():
    """Enable global profiling."""
    profiler = get_profiler()
    profiler.enabled = True


def disable_profiling():
    """Disable global profiling."""
    profiler = get_profiler()
    profiler.enabled = False


@contextmanager
def profile(name: str, **metadata):
    """Context manager for profiling using global profiler.
    
    Args:
        name: Name of the operation
        **metadata: Additional metadata
    
    Example:
        from bpui.profiler import profile
        
        with profile("load_config"):
            config = load_config()
    """
    profiler = get_profiler()
    with profiler.profile(name, **metadata):
        yield


def profile_decorator(name: Optional[str] = None, **metadata):
    """Decorator for profiling using global profiler.
    
    Args:
        name: Name of the operation (defaults to function name)
        **metadata: Additional metadata
    
    Example:
        from bpui.profiler import profile_decorator
        
        @profile_decorator()
        def expensive_operation():
            ...
    """
    profiler = get_profiler()
    return profiler.profile_decorator(name, **metadata)
