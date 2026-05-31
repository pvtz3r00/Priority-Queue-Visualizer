"""
core/priority_queue.py - Heap core backed by decoupled, animation-aware step logging.
Enables mixed-type comparative checking to support letters without raising exceptions.
"""
import time
from heap_strategy import MinHeapStrategy, MaxHeapStrategy
from visual_constants import COL_ACTIVE, COL_COMPARE, COL_SWAP, COL_NEW, COL_REMOVE

class PriorityQueue:
    def __init__(self, is_max_priority=False, tracker=None):
        self._heap = []
        self._tracker = tracker
        self._cmps = 0
        self.set_strategy(is_max_priority)

    def set_tracker(self, tracker):
        self._tracker = tracker

    def set_strategy(self, is_max_priority: bool):
        self._is_max = is_max_priority
        self._strategy = MaxHeapStrategy() if is_max_priority else MinHeapStrategy()

    @property
    def is_max(self) -> bool:
        return self._is_max

    @property
    def strategy_color(self) -> str:
        return self._strategy.default_color

    def get_data(self):
        return self._heap

    def clear(self):
        self._heap.clear()
        self._cmps = 0

    @staticmethod
    def _parent(i): return (i - 1) // 2
    @staticmethod
    def _left(i):   return 2 * i + 1
    @staticmethod
    def _right(i):  return 2 * i + 2

    def _safe_compare_vals(self, val1, val2):
        """Compares elements. If structural types differ, casts both to string keys to prevent crashes."""
        if type(val1) != type(val2):
            return self._strategy.compare(str(val1), str(val2))
        return self._strategy.compare(val1, val2)

    def _cmp(self, ci, pi):
        self._cmps += 1
        return self._safe_compare_vals(self._heap[ci][0], self._heap[pi][0])

    def push(self, priority, value):
        self._cmps = 0
        t0 = time.perf_counter()
        size_before = len(self._heap)
        self._heap.append((priority, value))
        self._sift_up(len(self._heap) - 1)
        if self._tracker:
            self._tracker.record("PUSH", size_before, self._cmps, (time.perf_counter() - t0) * 1e6)

    def pop(self):
        if not self._heap:
            return None
        self._cmps = 0
        t0 = time.perf_counter()
        size_before = len(self._heap)
        root = self._heap[0]
        last = self._heap.pop()
        if self._heap:
            self._heap[0] = last
            self._sift_down(0)
        if self._tracker:
            self._tracker.record("POP", size_before, self._cmps, (time.perf_counter() - t0) * 1e6)
        return root

    def _sift_up(self, i):
        p = self._parent(i)
        if i > 0 and self._cmp(i, p):
            self._heap[i], self._heap[p] = self._heap[p], self._heap[i]
            self._sift_up(p)

    def _sift_down(self, i):
        t = i
        l, r = self._left(i), self._right(i)
        if l < len(self._heap) and self._cmp(l, t):
            t = l
        if r < len(self._heap) and self._cmp(r, t):
            t = r
        if t != i:
            self._heap[i], self._heap[t] = self._heap[t], self._heap[i]
            self._sift_down(t)

    _pos_fn = None

    def _get_pos(self, n):
        if callable(self._pos_fn):
            return self._pos_fn(n)
        return {}

    def push_animated(self, priority, value):
        self._cmps = 0
        t0 = time.perf_counter()
        size_before = len(self._heap)
        steps = []

        heap_before = list(self._heap)
        self._heap.append((priority, value))
        new_idx = len(self._heap) - 1
        pos_after = self._get_pos(len(self._heap))

        tx, ty = pos_after.get(new_idx, (0, 0))
        moving = {new_idx: (tx, ty + 120, tx, ty)}

        steps.append({
            'heap_before': heap_before,
            'heap': list(self._heap),
            'moving': moving,
            'highlight': {new_idx: COL_NEW},
            'label': f"Insert P={priority} → index {new_idx}",
        })

        idx = new_idx
        while idx > 0:
            parent = self._parent(idx)
            self._cmps += 1
            cond = self._safe_compare_vals(self._heap[idx][0], self._heap[parent][0])

            steps.append({
                'heap_before': list(self._heap),
                'heap': list(self._heap),
                'moving': {},
                'highlight': {idx: COL_ACTIVE, parent: COL_COMPARE},
                'label': f"Compare P={self._heap[idx][0]} vs P={self._heap[parent][0]}" + (" → swap" if cond else " → heap OK"),
            })

            if cond:
                pos_now = self._get_pos(len(self._heap))
                ix, iy = pos_now.get(idx, (0, 0))
                px, py = pos_now.get(parent, (0, 0))
                heap_before_swap = list(self._heap)
                self._heap[idx], self._heap[parent] = self._heap[parent], self._heap[idx]
                steps.append({
                    'heap_before': heap_before_swap,
                    'heap': list(self._heap),
                    'moving': {idx: (ix, iy, px, py), parent: (px, py, ix, iy)},
                    'highlight': {idx: COL_SWAP, parent: COL_SWAP},
                    'label': f"Swap P={self._heap[parent][0]} ↑ to index {parent}",
                })
                idx = parent
            else:
                break

        steps.append({
            'heap_before': list(self._heap),
            'heap': list(self._heap),
            'moving': {},
            'highlight': {idx: COL_ACTIVE},
            'label': f"Push done — {self._cmps} comparison(s)",
        })

        if self._tracker:
            self._tracker.record("PUSH", size_before, self._cmps, (time.perf_counter() - t0) * 1e6)
        return steps

    def pop_animated(self):
        if not self._heap:
            return None, []
        self._cmps = 0
        t0 = time.perf_counter()
        size_before = len(self._heap)
        steps = []
        root = self._heap[0]

        steps.append({
            'heap_before': list(self._heap),
            'heap': list(self._heap),
            'moving': {},
            'highlight': {0: COL_REMOVE},
            'label': f"Remove root P={root[0]} V='{root[1]}'",
        })

        last = self._heap.pop()
        pos_full = self._get_pos(size_before)

        last_old_idx = size_before - 1
        rx, ry = pos_full.get(0, (0, 0))
        lx, ly = pos_full.get(last_old_idx, (0, 0))

        if self._heap:
            self._heap[0] = last
            steps.append({
                'heap_before': list(self._heap),
                'heap': list(self._heap),
                'moving': {0: (lx, ly, rx, ry)},
                'highlight': {0: COL_NEW},
                'label': f"Move last node P={last[0]} → root",
            })

            idx = 0
            while True:
                target = idx
                l_idx = self._left(idx)
                r_idx = self._right(idx)

                if l_idx < len(self._heap):
                    self._cmps += 1
                    if self._safe_compare_vals(self._heap[l_idx][0], self._heap[target][0]):
                        target = l_idx
                if r_idx < len(self._heap):
                    self._cmps += 1
                    if self._safe_compare_vals(self._heap[r_idx][0], self._heap[target][0]):
                        target = r_idx

                hl = {idx: COL_ACTIVE}
                if l_idx < len(self._heap):
                    hl[l_idx] = COL_COMPARE
                if r_idx < len(self._heap):
                    hl[r_idx] = COL_COMPARE

                steps.append({
                    'heap_before': list(self._heap),
                    'heap': list(self._heap),
                    'moving': {},
                    'highlight': hl,
                    'label': f"Compare P={self._heap[idx][0]} with children" + (" → swap" if target != idx else " → heap OK"),
                })

                if target != idx:
                    pos_now = self._get_pos(len(self._heap))
                    ix, iy = pos_now.get(idx, (0, 0))
                    tx2, ty2 = pos_now.get(target, (0, 0))
                    hb2 = list(self._heap)
                    self._heap[idx], self._heap[target] = self._heap[target], self._heap[idx]
                    steps.append({
                        'heap_before': hb2,
                        'heap': list(self._heap),
                        'moving': {idx: (ix, iy, tx2, ty2), target: (tx2, ty2, ix, iy)},
                        'highlight': {idx: COL_SWAP, target: COL_SWAP},
                        'label': f"Swap P={self._heap[target][0]} sifts down",
                    })
                    idx = target
                else:
                    break
        else:
            steps.append({
                'heap_before': [],
                'heap': [],
                'moving': {},
                'highlight': {},
                'label': "Heap is now empty",
            })

        steps.append({
            'heap_before': list(self._heap),
            'heap': list(self._heap),
            'moving': {},
            'highlight': {},
            'label': f"Pop done — {self._cmps} comparison(s)",
        })

        if self._tracker:
            self._tracker.record("POP", size_before, self._cmps, (time.perf_counter() - t0) * 1e6)
        return root, steps