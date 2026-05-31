"""
ui/visualizer_tab.py - Visual tree calculations, mouse events, and animation scheduler.
"""
import tkinter as tk
from tkinter import messagebox, ttk
import random
import string
from visual_constants import (
    BG_COLOR, CANVAS_COLOR, TEXT_COLOR, COL_ACTIVE, COL_COMPARE, COL_SWAP,
    COL_GHOST, COL_NEW, COL_REMOVE, LEVEL_GAP, NODE_RADIUS, TWEEN_MS, TWEEN_STEPS
)
from priority_queue import PriorityQueue
from complexity_tracker import ComplexityTracker
from complexity_graph import ComplexityGraphPanel
from sidebar_widgets import SidebarPanel
from control_panel import ControlPanel


def _ease(t: float) -> float:
    return t * t * (3 - 2 * t)


class VisualizerTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_COLOR)
        self._tracker = ComplexityTracker()
        self.pq = PriorityQueue(is_max_priority=False, tracker=self._tracker)

        self._fill_job = None
        self._fill_queue = []

        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._drag_start = None

        # Animation states
        self._steps = []
        self._step_idx = 0
        self._tween_idx = 0
        self._anim_job = None
        self._anim_running = False
        self._autopop_running = False

        self._setup_ui()
        self.pq._pos_fn = self._compute_positions

    def _setup_ui(self):
        # 1. Top Control bar
        self.control_bar = ControlPanel(
            self,
            on_push=self._handle_push,
            on_pop=self._handle_pop,
            on_autopop=self._handle_autopop,
            on_clear=self._handle_clear,
            on_toggle=self._handle_toggle,
            on_fill=self._start_random_fill
        )
        self.control_bar.pack(fill="x", pady=5, padx=8)

        # 2. Outer container
        nb_frame = tk.Frame(self, bg=BG_COLOR)
        nb_frame.pack(fill="both", expand=True)

        # Tabs Setup
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.TNotebook", background=BG_COLOR, borderwidth=0)
        style.configure("Dark.TNotebook.Tab", background="#333333", foreground=TEXT_COLOR, padding=[12, 4], font=("Arial", 11, "bold"))
        style.map("Dark.TNotebook.Tab", background=[("selected", "#00CED1")], foreground=[("selected", "black")])

        self.notebook = ttk.Notebook(nb_frame, style="Dark.TNotebook")
        self.notebook.pack(side="left", fill="both", expand=True)

        # Tab 1: Heap tree view
        heap_outer = tk.Frame(self.notebook, bg=BG_COLOR)
        self.notebook.add(heap_outer, text="  Heap View  ")

        zoom_bar = tk.Frame(heap_outer, bg=BG_COLOR)
        zoom_bar.pack(fill="x", padx=8, pady=(4, 0))

        tk.Label(zoom_bar, text="Zoom:", fg=TEXT_COLOR, bg=BG_COLOR, font=("Arial", 10)).pack(side="left")
        for lbl, cmd in ((" + ", self._zoom_in), (" − ", self._zoom_out)):
            tk.Button(
                zoom_bar, text=lbl, command=cmd,
                bg="#333333", fg=TEXT_COLOR, relief="flat",
                cursor="hand2", font=("Arial", 11, "bold"), padx=4
            ).pack(side="left", padx=2)

        self._zoom_label = tk.Label(zoom_bar, text="100%", fg="#AAAAAA", bg=BG_COLOR, font=("Arial", 10), width=5)
        self._zoom_label.pack(side="left", padx=4)

        tk.Button(
            zoom_bar, text="Reset View", command=self._zoom_reset,
            bg="#333333", fg=TEXT_COLOR, relief="flat", cursor="hand2", font=("Arial", 10)
        ).pack(side="left", padx=6)

        # Docked stepping and stop buttons locked to the far right
        self._skip_btn = tk.Button(
            zoom_bar, text="⏩ Skip", command=self._skip_all,
            bg="#444444", fg=TEXT_COLOR, relief="flat", cursor="hand2", font=("Arial", 10), state="disabled"
        )
        self._skip_btn.pack(side="right", padx=4)

        self._step_btn = tk.Button(
            zoom_bar, text="⏭ Step", command=self._manual_step,
            bg="#444444", fg=TEXT_COLOR, relief="flat", cursor="hand2", font=("Arial", 10), state="disabled"
        )
        self._step_btn.pack(side="right", padx=4)

        tk.Label(zoom_bar, text="  scroll=zoom · drag=pan", fg="#555555", bg=BG_COLOR, font=("Arial", 9)).pack(side="right", padx=10)

        # Description status tag
        self._anim_label = tk.Label(zoom_bar, text="", fg=COL_ACTIVE, bg=BG_COLOR, font=("Arial", 10, "italic"), anchor="w")
        self._anim_label.pack(side="left", padx=8, fill="x", expand=True)

        self.canvas = tk.Canvas(heap_outer, bg=CANVAS_COLOR, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", lambda _: self._zoom_in())
        self.canvas.bind("<Button-5>", lambda _: self._zoom_out())
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)

        # Tab 2: Complexity Graphs Panel
        self.graph_panel = ComplexityGraphPanel(self.notebook, self._tracker)
        self.notebook.add(self.graph_panel, text="  Complexity Graph  ")

        # 3. Sidebar Widget
        self.sidebar = SidebarPanel(nb_frame)
        self.sidebar.pack(side="right", fill="y")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        self.sidebar.log("App started — Min-Heap mode")

    def _handle_toggle(self, is_max: bool):
        self._cancel_animation()
        self._cancel_active_fill()
        self._tracker.clear()

        self.pq.set_strategy(is_max)
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._update_zoom_label()

        mode = "Max-Heap" if is_max else "Min-Heap"
        self.sidebar.log(f"Switched to {mode} — heap cleared")
        self._static_redraw()
        self.graph_panel.refresh_graph()
        self.sidebar.refresh(self.pq.get_data(), self.pq.is_max)

    def _handle_push(self):
        if self._anim_running:
            return

        pri_str = self.control_bar.pri_entry.get().strip()
        if not pri_str:
            messagebox.showerror("Input Error", "Priority cannot be empty.")
            return

        # STRICTLY ALLOWS NUMERIC INTEGERS ONLY (Alphanumeric values will raise an error)
        if pri_str.isdigit() or (pri_str.startswith('-') and pri_str[1:].isdigit()):
            priority = int(pri_str)
        else:
            messagebox.showerror("Input Error", "Priority must be an integer (e.g., -5, 12, 100). No letters/spaces/symbols.")
            return

        value = self.control_bar.val_entry.get().strip()
        if not value:
            messagebox.showerror("Input Error", "Value cannot be empty.")
            return

        self.control_bar.val_entry.delete(0, tk.END)
        self.control_bar.pri_entry.delete(0, tk.END)

        steps = self.pq.push_animated(priority, value)
        self.sidebar.log(f"PUSH  P={priority}  V='{value}'")
        self._begin_animation(steps)

    def _handle_pop(self):
        if self._anim_running:
            return
        result, steps = self.pq.pop_animated()
        if result is not None:
            self.sidebar.log(f"POP   P={result[0]}  V='{result[1]}'")
            self._begin_animation(steps)
        else:
            messagebox.showwarning("Empty", "The Priority Queue is empty.")
            self.sidebar.log("POP   — queue empty")

    def _handle_autopop(self):
        if self._anim_running:
            return
        if not self.pq.get_data():
            messagebox.showwarning("Empty", "The Priority Queue is already empty.")
            self.sidebar.log("AUTO-POP — queue empty")
            return

        self._autopop_running = True
        self._trigger_next_autopop_step()

    def _trigger_next_autopop_step(self):
        if not self._autopop_running:
            return

        result, steps = self.pq.pop_animated()
        if result is not None:
            self.sidebar.log(f"AUTO-POP  P={result[0]}  V='{result[1]}'")
            self._begin_animation(steps)
        else:
            self._autopop_running = False
            self.sidebar.log("AUTO-POP — queue completely empty")
            self.control_bar.set_controls_state("normal")

    def _handle_clear(self):
        self._cancel_animation()
        self._cancel_active_fill()
        self.pq.clear()
        self._tracker.clear()

        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._update_zoom_label()

        self.sidebar.log("CLEAR — queue emptied")
        self._static_redraw()
        self.graph_panel.refresh_graph()
        self.sidebar.refresh(self.pq.get_data(), self.pq.is_max)

    def _compute_positions(self, n):
        if n == 0:
            return {}
        self.update_idletasks()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return {}

        z = self._zoom
        r = NODE_RADIUS * z
        lg = LEVEL_GAP * z
        rx = cw // 2 + self._pan_x
        ry = r + 10 + self._pan_y
        xo = (cw // 4) * z
        pos = {}
        self._fill_positions(pos, 0, rx, ry, xo, lg, n)
        return pos

    def _fill_positions(self, pos, idx, x, y, xo, lg, n):
        if idx >= n:
            return
        pos[idx] = (x, y)
        l, r = 2 * idx + 1, 2 * idx + 2
        if l < n:
            self._fill_positions(pos, l, x - xo, y + lg, xo // 2, lg, n)
        if r < n:
            self._fill_positions(pos, r, x + xo, y + lg, xo // 2, lg, n)

    def _static_redraw(self):
        data = self.pq.get_data()
        pos = self._compute_positions(len(data))
        self._paint_heap(data, pos, {})

    def _paint_heap(self, data, pos, color_overrides, label_map=None):
        c = self.canvas
        c.delete("all")
        if not data or not pos:
            return

        n = len(data)
        z = self._zoom
        r = NODE_RADIUS * z

        # Edges
        for idx in range(n):
            if idx not in pos:
                continue
            x, y = pos[idx]
            for child in (2 * idx + 1, 2 * idx + 2):
                if child < n and child in pos:
                    cx, cy = pos[child]
                    edge_col = "#555555"
                    if color_overrides.get(idx) in (COL_SWAP, COL_ACTIVE, COL_COMPARE) or \
                       color_overrides.get(child) in (COL_SWAP, COL_ACTIVE, COL_COMPARE):
                        edge_col = "#888888"
                    c.create_line(x, y, cx, cy, fill=edge_col, width=max(1, int(r * 0.06)))

        # Nodes
        base_col = self.pq.strategy_color
        moving_idxs = set(label_map.keys() if label_map else [])
        draw_order = [i for i in pos if i not in moving_idxs] + [i for i in pos if i in moving_idxs]

        for idx in draw_order:
            if idx not in pos:
                continue
            px, py = pos[idx]
            col = color_overrides.get(idx, base_col)
            ow = max(2, int(r * 0.10))

            if col in (COL_ACTIVE, COL_COMPARE, COL_SWAP, COL_NEW, COL_REMOVE):
                c.create_oval(px - r - 6, py - r - 6, px + r + 6, py + r + 6, outline=col, width=3)

            c.create_oval(px - r, py - r, px + r, py + r, fill=col, outline="white", width=ow)

            if r >= 14:
                node_data = (label_map[idx] if label_map and idx in label_map else (data[idx] if idx < len(data) else None))
                if node_data:
                    pri, val = node_data
                    txt = f"P:{pri}\n{val}" if r >= 20 else str(pri)
                    fsz = max(6, min(16, int(r * 0.38)))
                    tcol = "black" if col not in (COL_GHOST,) else "#777777"
                    c.create_text(px, py, text=txt, fill=tcol, font=("Arial", fsz, "bold"), justify="center")

    def _begin_animation(self, steps):
        if not steps:
            self._static_redraw()
            self.graph_panel.refresh_graph()
            self.sidebar.refresh(self.pq.get_data(), self.pq.is_max)
            return

        self._cancel_animation()
        self._steps = steps
        self._step_idx = 0
        self._anim_running = True
        self.control_bar.set_controls_state("disabled")
        self._step_btn.config(state="normal")
        self._skip_btn.config(state="normal")
        self._run_next_step()

    def _run_next_step(self):
        if self._step_idx >= len(self._steps):
            self._finish_animation()
            return

        step = self._steps[self._step_idx]
        self._anim_label.config(text=f"▶ {step.get('label', '')}")

        self._tween_idx = 0
        self._tw_heap_before = step.get('heap_before', [])
        self._tw_heap_after = step.get('heap', [])
        self._tw_moving = step.get('moving', {})
        self._tw_highlights = step.get('highlight', {})
        self._tw_pos_before = self._compute_positions(len(self._tw_heap_before))
        self._tw_pos_after = self._compute_positions(len(self._tw_heap_after))

        self._tween_tick()

    def _tween_tick(self):
        t_raw = self._tween_idx / TWEEN_STEPS
        t = _ease(t_raw)

        step = self._steps[self._step_idx]
        moving = step.get('moving', {})

        n_before = len(self._tw_heap_before)
        n_after = len(self._tw_heap_after)

        pos = {}
        for idx in range(max(n_before, n_after)):
            if idx in moving:
                fx, fy, tx, ty = moving[idx]
                pos[idx] = (fx + (tx - fx) * t, fy + (ty - fy) * t)
            elif idx in self._tw_pos_after:
                pos[idx] = self._tw_pos_after[idx]
            elif idx in self._tw_pos_before:
                pos[idx] = self._tw_pos_before[idx]

        label_map = {}
        if moving and self._tw_heap_before:
            for idx in moving:
                if idx < len(self._tw_heap_before):
                    label_map[idx] = self._tw_heap_before[idx]

        display_heap = self._tw_heap_after
        highlights = step.get('highlight', {})
        color_map = dict(highlights)

        self._paint_heap(display_heap, pos, color_map, label_map)
        self.sidebar.update_raw(display_heap)

        self._tween_idx += 1
        if self._tween_idx <= TWEEN_STEPS:
            self._anim_job = self.after(TWEEN_MS, self._tween_tick)
        else:
            pause = self.control_bar.speed_var.get()
            self._anim_job = self.after(pause, self._advance_step)

    def _advance_step(self):
        self._step_idx += 1
        self._run_next_step()

    def _manual_step(self):
        if self._anim_job:
            self.after_cancel(self._anim_job)
            self._anim_job = None

        step = self._steps[self._step_idx] if self._step_idx < len(self._steps) else {}
        heap = step.get('heap', self.pq.get_data())
        pos = self._compute_positions(len(heap))
        self._paint_heap(heap, pos, step.get('highlight', {}))

        self._step_idx += 1
        if self._step_idx >= len(self._steps):
            self._finish_animation()
        else:
            nxt = self._steps[self._step_idx]
            self._anim_label.config(text=f"⏸ {nxt.get('label', '')}")
            self._run_next_step()

    def _skip_all(self):
        if self._anim_job:
            self.after_cancel(self._anim_job)
            self._anim_job = None
        self._finish_animation()

    def _finish_animation(self):
        self._anim_running = False
        self._anim_job = None
        self._anim_label.config(text="")
        self._step_btn.config(state="disabled")
        self._skip_btn.config(state="disabled")
        self.control_bar.set_controls_state("normal")
        self._static_redraw()
        self.graph_panel.refresh_graph()
        self.sidebar.refresh(self.pq.get_data(), self.pq.is_max)

        # Sequentially triggers next pop step in the loop
        if self._autopop_running:
            if self.pq.get_data():
                self.control_bar.set_controls_state("disabled")
                pause = self.control_bar.speed_var.get()
                self._anim_job = self.after(pause, self._trigger_next_autopop_step)
            else:
                self._autopop_running = False
                self.sidebar.log("AUTO-POP — queue completely empty")
                self.control_bar.set_controls_state("normal")

    def _cancel_animation(self):
        if self._anim_job:
            self.after_cancel(self._anim_job)
            self._anim_job = None
        self._anim_running = False
        self._autopop_running = False
        self._steps = []
        self._step_idx = 0
        self._anim_label.config(text="")
        self._step_btn.config(state="disabled")
        self._skip_btn.config(state="disabled")

    def _start_random_fill(self):
        if self._fill_job is not None:
            self._cancel_active_fill()
            self.sidebar.log("Random fill stopped")
            return
        try:
            count = int(self.control_bar.fill_entry.get().strip())
            if count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Enter a positive integer.")
            return

        self._fill_queue = [(random.randint(1, 99), random.choice(string.ascii_uppercase) + str(random.randint(1, 9))) for _ in range(count)]
        self.control_bar.set_controls_state("disabled")
        self.control_bar.fill_btn.config(state="normal", text="Stop")
        self._pump_fill()

    def _pump_fill(self):
        BATCH = 10
        if not self._fill_queue:
            self._fill_job = None
            self.control_bar.fill_btn.config(text="Fill")
            self.control_bar.set_controls_state("normal")
            self._static_redraw()
            self.graph_panel.refresh_graph()
            self.sidebar.refresh(self.pq.get_data(), self.pq.is_max)
            self.sidebar.log("Random fill complete")
            return

        for p, v in self._fill_queue[:BATCH]:
            self.pq.push(p, v)
            self.sidebar.log(f"PUSH (Auto) P={p}  V='{v}'")

        self._fill_queue = self._fill_queue[BATCH:]
        self._static_redraw()
        self.graph_panel.refresh_graph()
        self.sidebar.refresh(self.pq.get_data(), self.pq.is_max)
        self._fill_job = self.after(0, self._pump_fill)

    def _cancel_active_fill(self):
        if self._fill_job:
            self.after_cancel(self._fill_job)
            self._fill_job = None
        self._fill_queue = []
        self.control_bar.fill_btn.config(text="Fill")
        self.control_bar.set_controls_state("normal")

    _ZOOM_MIN, _ZOOM_MAX, _ZOOM_STEP = 0.1, 5.0, 0.15

    def _zoom_in(self):
        self._zoom = min(self._ZOOM_MAX, self._zoom + self._ZOOM_STEP)
        self._update_zoom_label()
        self._static_redraw()

    def _zoom_out(self):
        self._zoom = max(self._ZOOM_MIN, self._zoom - self._ZOOM_STEP)
        self._update_zoom_label()
        self._static_redraw()

    def _zoom_reset(self):
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._update_zoom_label()
        self._static_redraw()

    def _update_zoom_label(self):
        self._zoom_label.config(text=f"{int(self._zoom * 100)}%")

    def _on_mousewheel(self, e):
        self._zoom_in() if e.delta > 0 else self._zoom_out()

    def _on_drag_start(self, e):
        self._drag_start = (e.x, e.y)

    def _on_drag_move(self, e):
        if not self._drag_start:
            return
        self._pan_x += e.x - self._drag_start[0]
        self._pan_y += e.y - self._drag_start[1]
        self._drag_start = (e.x, e.y)
        self._static_redraw()

    def _on_drag_end(self, _):
        self._drag_start = None

    def _on_tab_change(self, _=None):
        try:
            if self.notebook.index(self.notebook.select()) == 1:
                self.graph_panel.refresh_graph()
        except Exception:
            pass