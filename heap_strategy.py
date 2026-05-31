"""
heap_strategy.py - Implements the Strategy Pattern to decouple Min and Max Heap behaviors.
Eliminates branching checks throughout the priority queue sorting process.
"""

from abc import ABC, abstractmethod
from visual_constants import COL_DEFAULT, COL_DEFAULT_MAX

class HeapStrategy(ABC):
    """Abstract Base Strategy governing binary heap relations and visual traits."""

    @abstractmethod
    def compare(self, child_priority: int, parent_priority: int) -> bool:
        """Determines if the child node should rise above the parent node."""
        pass

    @property
    @abstractmethod
    def default_color(self) -> str:
        """The theme base color representing the heap strategy."""
        pass

    @property
    @abstractmethod
    def label(self) -> str:
        """Readable name representing the operational strategy."""
        pass


class MinHeapStrategy(HeapStrategy):
    """Min-Heap rules: Lower values rise to root (Minimum Priority Queue)."""

    def compare(self, child_priority: int, parent_priority: int) -> bool:
        return child_priority < parent_priority

    @property
    def default_color(self) -> str:
        return COL_DEFAULT

    @property
    def label(self) -> str:
        return "Min-Heap"


class MaxHeapStrategy(HeapStrategy):
    """Max-Heap rules: Higher values rise to root (Maximum Priority Queue)."""

    def compare(self, child_priority: int, parent_priority: int) -> bool:
        return child_priority > parent_priority

    @property
    def default_color(self) -> str:
        return COL_DEFAULT_MAX

    @property
    def label(self) -> str:
        return "Max-Heap"