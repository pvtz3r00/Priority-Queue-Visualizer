"""
sidebar_widgets.py - Manages operational logging, structural data readouts,
and custom index-to-parent relational diagrams.
"""

import tkinter as tk
from visual_constants import TEXT_COLOR, COL_DEFAULT, COL_DEFAULT_MAX

class SidebarPanel(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1A1A1A", width=220, **kwargs)
        self.pack_propagate(False)
        self._setup_widgets()

    def _setup_widgets(self):
        # Operational Logs Section
        lf = self._create_panel("Operations Log")
        self._log_text = tk.Text(
            lf, bg="#1A1A1A", fg="#CCCCCC", font=("Courier", 10),
            state="disabled", wrap="word", relief="flat",
            highlightthickness=0, cursor="arrow", width=26
        )
        self._log_text.pack(fill="both", expand=True, padx=6, pady=(0, 2))
        
        tk.Button(
            lf, text="Clear Log", command=self.clear_log,
            bg="#333333", fg=TEXT_COLOR, relief="flat", font=("Arial", 10), cursor="hand2"
        ).pack(pady=(0, 4))

        tk.Frame(self, bg="#333333", height=2).pack(fill="x")

        # Raw heap structures
        rf = self._create_panel("Raw Data", "heap[]")
        self._raw_text = tk.Text(
            rf, bg="#111111", fg="#88FF88", font=("Courier", 10),
            state="disabled", wrap="word", relief="flat",
            highlightthickness=0, cursor="arrow", width=26
        )
        self._raw_text.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        tk.Frame(self, bg="#333333", height=2).pack(fill="x")

        # Memory Mapping Array representation
        mf = self._create_panel("Memory Map", "index · value")
        self._mem_canvas = tk.Canvas(mf, bg="#111111", highlightthickness=0)
        self._mem_canvas.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    def _create_panel(self, title, hint=""):
        f = tk.Frame(self, bg="#1A1A1A")
        f.pack(fill="both", expand=True)
        hdr = tk.Frame(f, bg="#1A1A1A")
        hdr.pack(fill="x", pady=(6, 2), padx=8)
        
        tk.Label(hdr, text=title, fg=TEXT_COLOR, bg="#1A1A1A", font=("Arial", 11, "bold")).pack(side="left")
        if hint:
            tk.Label(hdr, text=hint, fg="#555555", bg="#1A1A1A", font=("Courier", 9)).pack(side="right")
            
        tk.Frame(f, bg="#444444", height=1).pack(fill="x", padx=8, pady=(0, 4))
        return f

    def log(self, msg):
        self._log_text.config(state="normal")
        self._log_text.insert("1.0", msg + "\n")
        self._log_text.config(state="disabled")

    def clear_log(self):
        self._log_text.config(state="normal")
        self._log_text.delete("1.0", tk.END)
        self._log_text.config(state="disabled")

    def refresh(self, data, is_max):
        self.update_raw(data)
        self.update_memory_map(data, is_max)

    def update_raw(self, data):
        self._raw_text.config(state="normal")
        self._raw_text.delete("1.0", tk.END)
        if not data:
            self._raw_text.insert(tk.END, "(empty)")
        else:
            self._raw_text.insert(tk.END, "\n".join(f"[{i:>2}]  P={p:<4} V={v}" for i, (p, v) in enumerate(data)))
        self._raw_text.config(state="disabled")

    def update_memory_map(self, data, is_max):
        c = self._mem_canvas
        c.delete("all")
        self.update_idletasks()
        cw = c.winfo_width()
        
        if cw < 10:
            return
        if not data:
            c.create_text(cw // 2, 30, text="(empty)", fill="#444444", font=("Courier", 8))
            return

        nc = COL_DEFAULT_MAX if is_max else COL_DEFAULT
        ch2, px, cw2 = 22, 6, cw - 12
        for i, (pri, val) in enumerate(data):
            yt, yb = i * ch2, i * ch2 + ch2 - 2
            c.create_rectangle(px, yt, px + cw2, yb, fill="#1A2A1A" if i % 2 == 0 else "#111111", outline="#2A2A2A")
            c.create_rectangle(px, yt, px + 28, yb, fill="#222222", outline="")
            
            c.create_text(px + 14, (yt + yb) // 2, text=str(i), fill="#666666", font=("Courier", 8, "bold"), anchor="center")
            
            c.create_rectangle(px + 32, yt + 3, px + 70, yb - 3, fill=nc, outline="")
            c.create_text(px + 51, (yt + yb) // 2, text=f"P:{pri}", fill="black", font=("Courier", 8, "bold"), anchor="center")
            
            c.create_text(px + 76, (yt + yb) // 2, text=str(val), fill="#CCCCCC", font=("Courier", 9), anchor="w")
            if i > 0:
                c.create_text(px + cw2 - 2, (yt + yb) // 2, text=f"↑{(i - 1) // 2}", fill="#444444", font=("Courier", 8), anchor="e")
                
        c.config(scrollregion=(0, 0, cw, len(data) * ch2))