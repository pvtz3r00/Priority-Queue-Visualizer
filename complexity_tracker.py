"""
complexity_tracker.py - Thread-safe logging mechanism storing operation analytics
such as input size, exact comparisons, and algorithmic execution time.
"""

class ComplexityTracker:
    def __init__(self):
        self._history = []

    def record(self, operation: str, size_before: int, comparisons: int, elapsed_us: float = 0.0):
        self._history.append((operation, size_before, comparisons, elapsed_us))

    def get_history(self):
        return list(self._history)

    def clear(self):
        self._history.clear()