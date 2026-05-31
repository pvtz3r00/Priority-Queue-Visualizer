"""
complexity_graph.py - Computes and renders algorithm tracking trends, 
O(log n) efficiency references, and raw microsecond latency statistics.
"""

import tkinter as tk
import math
from visual_constants import (
    BG_COLOR, CANVAS_COLOR, TEXT_COLOR, GRID_COLOR, AXIS_COLOR,
    PUSH_COLOR, POP_COLOR
)

class ComplexityGraphPanel(tk.Frame):
    def __init__(self, parent, tracker, **kwargs):
        super().__init__(parent, bg=BG_COLOR, **kwargs)
        self._tracker = tracker
        self._setup_ui()

    def _setup_ui(self):
        gt = tk.Frame(self, bg=BG_COLOR)
        gt.pack(fill="x", padx=10, pady=(6, 0))
        
        tk.Label(gt, text="Comparisons & Time per Operation", fg=TEXT_COLOR, bg=BG_COLOR, font=("Arial", 11, "bold")).pack(side="left")
        
        tk.Button(
            gt, text="Clear Graph", command=self._clear_graph,
            bg="#333333", fg=TEXT_COLOR, relief="flat", font=("Arial", 10), cursor="hand2"
        ).pack(side="right")
        
        # Legend Panels
        leg = tk.Frame(gt, bg=BG_COLOR)
        leg.pack(side="right", padx=12)
        for color, lbl in ((PUSH_COLOR, "PUSH"), (POP_COLOR, "POP"), ("#FFFF55", "O(log n)"), ("#FF88FF", "Time (µs)")):
            tk.Frame(leg, bg=color, width=12, height=12).pack(side="left", padx=(6, 2))
            tk.Label(leg, text=lbl, fg=TEXT_COLOR, bg=BG_COLOR, font=("Arial", 10)).pack(side="left")

        gm = tk.Frame(self, bg=BG_COLOR)
        gm.pack(fill="x", padx=10, pady=(2, 0))
        tk.Label(gm, text="Show:", fg="#AAAAAA", bg=BG_COLOR, font=("Arial", 10)).pack(side="left")
        
        self._graph_mode = tk.StringVar(value="both")
        for text, val in (("Comparisons", "cmp"), ("Time (µs)", "time"), ("Both", "both")):
            tk.Radiobutton(
                gm, text=text, variable=self._graph_mode, value=val,
                bg=BG_COLOR, fg=TEXT_COLOR, selectcolor="#333333",
                activebackground=BG_COLOR, activeforeground=TEXT_COLOR,
                font=("Arial", 10), command=self.refresh_graph
            ).pack(side="left", padx=6)

        self.canvas = tk.Canvas(self, bg=CANVAS_COLOR, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=8)
        self.canvas.bind("<Configure>", lambda e: self.refresh_graph())

    def _clear_graph(self):
        self._tracker.clear()
        self.refresh_graph()

    def refresh_graph(self):
        c = self.canvas
        c.delete("all")
        history = self._tracker.get_history()
        
        if not history:
            c.create_text(
                c.winfo_width() // 2, c.winfo_height() // 2,
                text="No operations recorded yet.\nPush or Pop items to see data.",
                fill="#666666", font=("Arial", 11), justify="center"
            )
            return

        cw, ch = c.winfo_width(), c.winfo_height()
        if cw < 50 or ch < 50:
            return

        mode = self._graph_mode.get()
        if mode == "both":
            self._draw_cmp_chart(c, history, cw, 0, ch // 2)
            c.create_line(0, ch // 2, cw, ch // 2, fill="#444444")
            c.create_text(
                10, ch // 2 - 2, text="▼ Time (µs)", fill="#FF88FF",
                font=("Arial", 7, "bold"), anchor="sw"
            )
            self._draw_time_chart(c, history, cw, ch // 2, ch)
        elif mode == "cmp":
            self._draw_cmp_chart(c, history, cw, 0, ch)
        else:
            self._draw_time_chart(c, history, cw, 0, ch)

    def _draw_cmp_chart(self, c, history, cw, y0, y1):
        PL, PR, PT, PB = 60, 20, y0 + 18, y1 - 24
        pw, ph = cw - PL - PR, PB - PT
        if ph < 10:
            return
            
        mc = max(h[2] for h in history) or 1
        nops = len(history)
        
        for i in range(6):
            v = int(mc * i / 5)
            gy = PB - int(ph * i / 5)
            c.create_line(PL, gy, PL + pw, gy, fill=GRID_COLOR, dash=(3, 4))
            c.create_text(PL - 6, gy, text=str(v), fill=AXIS_COLOR, font=("Arial", 7), anchor="e")
            
        c.create_line(PL, PT, PL, PB, fill=AXIS_COLOR, width=1)
        c.create_line(PL, PB, PL + pw, PB, fill=AXIS_COLOR, width=1)
        c.create_text(14, (PT + PB) // 2, text="Comparisons", fill=AXIS_COLOR, font=("Arial", 8, "bold"), angle=90)
        c.create_text(PL + pw // 2, y1 - 8, text="Operation #", fill=AXIS_COLOR, font=("Arial", 8))
        
        bw = max(2, min(30, pw / nops * 0.65))
        sw = pw / nops
        rpts = []
        
        for i, row in enumerate(history):
            op, sz, cmps = row[0], row[1], row[2]
            bx = PL + sw * i + sw / 2
            bh = int(ph * cmps / mc) if mc else 0
            bt = PB - bh
            c.create_rectangle(bx - bw / 2, bt, bx + bw / 2, PB, fill=PUSH_COLOR if op == "PUSH" else POP_COLOR, outline="")
            
            if bh > 10 or cmps:
                c.create_text(bx, max(bt - 7, PT + 4), text=str(cmps), fill="#EEEEEE", font=("Arial", 6), anchor="s")
                
            step = max(1, nops // 20)
            if i % step == 0:
                c.create_text(bx, PB + 12, text=str(sz), fill=AXIS_COLOR, font=("Arial", 6), anchor="n")
                
            ideal = math.log2(sz + 1) if sz >= 0 else 0
            rpts.append((bx, PB - int(ph * ideal / mc)))
            
        if len(rpts) >= 2:
            flat = [v for pt in rpts for v in pt]
            c.create_line(*flat, fill="#FFFF55", width=1, dash=(4, 3), smooth=True)
            c.create_text(rpts[-1][0] + 4, rpts[-1][1], text="O(log n)", fill="#FFFF55", font=("Arial", 7), anchor="w")

    def _draw_time_chart(self, c, history, cw, y0, y1):
        PL, PR, PT, PB = 60, 20, y0 + 18, y1 - 24
        pw, ph = cw - PL - PR, PB - PT
        if ph < 10:
            return
            
        times = [h[3] if len(h) > 3 else 0.0 for h in history]
        mt = max(times) or 1.0
        nops = len(history)
        
        for i in range(6):
            v = mt * i / 5
            gy = PB - int(ph * i / 5)
            lb = f"{v:.1f}" if mt < 100 else f"{v:.0f}"
            c.create_line(PL, gy, PL + pw, gy, fill=GRID_COLOR, dash=(3, 4))
            c.create_text(PL - 6, gy, text=lb, fill=AXIS_COLOR, font=("Arial", 7), anchor="e")
            
        c.create_line(PL, PT, PL, PB, fill=AXIS_COLOR, width=1)
        c.create_line(PL, PB, PL + pw, PB, fill=AXIS_COLOR, width=1)
        c.create_text(14, (PT + PB) // 2, text="Time (µs)", fill=AXIS_COLOR, font=("Arial", 8, "bold"), angle=90)
        c.create_text(PL + pw // 2, y1 - 8, text="Operation #  (size annotated)", fill=AXIS_COLOR, font=("Arial", 8))
        
        bw = max(2, min(30, pw / nops * 0.65))
        sw = pw / nops
        avgp = []
        
        for i, (row, t) in enumerate(zip(history, times)):
            op, sz = row[0], row[1]
            bx = PL + sw * i + sw / 2
            bh = int(ph * t / mt) if mt else 0
            bt = PB - bh
            c.create_rectangle(bx - bw / 2, bt, bx + bw / 2, PB, fill="#00AADD" if op == "PUSH" else "#EE6600", outline="")
            
            if bh > 10:
                lb2 = f"{t:.1f}" if t < 100 else f"{t:.0f}"
                c.create_text(bx, max(bt - 7, PT + 4), text=lb2, fill="#FFCCFF", font=("Arial", 6), anchor="s")
                
            step2 = max(1, nops // 20)
            if i % step2 == 0:
                c.create_text(bx, PB + 12, text=str(sz), fill=AXIS_COLOR, font=("Arial", 6), anchor="n")
                
            win = times[max(0, i - 4):i + 1]
            avgp.append((bx, PB - int(ph * (sum(win) / len(win)) / mt)))
            
        if len(avgp) >= 3:
            flat = [v for pt in avgp for v in pt]
            c.create_line(*flat, fill="#FF88FF", width=2, smooth=True)
            c.create_text(avgp[-1][0] + 4, avgp[-1][1], text="avg", fill="#FF88FF", font=("Arial", 7), anchor="w")