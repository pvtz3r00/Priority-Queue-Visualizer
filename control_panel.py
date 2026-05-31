import tkinter as tk
from visual_constants import BG_COLOR, TEXT_COLOR, DEFAULT_STEP_MS

class ControlPanel(tk.Frame):
    def __init__(self, parent, on_push, on_pop, on_clear, on_toggle, on_fill, **kwargs):
        # Safely extract and discard the legacy on_autopop parameter if passed from visualizer_tab.py
        kwargs.pop('on_autopop', None)

        super().__init__(parent, bg=BG_COLOR, **kwargs)
        self._on_push = on_push
        self._on_pop = on_pop
        self._on_clear = on_clear
        self._on_toggle = on_toggle
        self._on_fill = on_fill

        self._is_max = False
        self.speed_var = tk.IntVar(value=DEFAULT_STEP_MS)
        self.speed_display_var = tk.StringVar()

        self._setup_widgets()
        self._update_speed_label(DEFAULT_STEP_MS)

    def _setup_widgets(self):
        # Value & Priority Entries
        tk.Label(self, text="Value:", fg=TEXT_COLOR, bg=BG_COLOR, font=("Arial", 11)).pack(side="left", padx=5)
        self.val_entry = tk.Entry(self, width=10, font=("Arial", 11))
        self.val_entry.pack(side="left", padx=5)

        tk.Label(self, text="Priority:", fg=TEXT_COLOR, bg=BG_COLOR, font=("Arial", 11)).pack(side="left", padx=5)
        self.pri_entry = tk.Entry(self, width=10, font=("Arial", 11))
        self.pri_entry.pack(side="left", padx=5)

        # Primary Operation Buttons
        self.push_btn = tk.Button(
            self, text="Push", command=self._on_push,
            bg="#1A8C3A", fg="white", activebackground="#22AA48", activeforeground="white",
            relief="flat", cursor="hand2", font=("Arial", 11, "bold"), padx=8
        )
        self.push_btn.pack(side="left", padx=5)

        self.pop_btn = tk.Button(self, text="Pop", command=self._on_pop,
            bg="#C47200", fg="white", activebackground="#E08800", activeforeground="white",
            relief="flat", cursor="hand2", font=("Arial", 11, "bold"), padx=8)
        self.pop_btn.pack(side="left", padx=5)

        self.clear_btn = tk.Button(
            self, text="Clear Queue", command=self._on_clear,
            bg="#882222", fg="white", activebackground="#AA3333",
            relief="flat", cursor="hand2", font=("Arial", 11, "bold"), padx=8
        )
        self.clear_btn.pack(side="left", padx=8)

        # Min / Max Strategy Selector Toggle Box
        self._tog_frame = tk.Frame(self, bg=BG_COLOR)
        self._tog_frame.pack(side="left", padx=12)

        self._min_label = tk.Label(self._tog_frame, text="MIN", fg="#00CED1", bg=BG_COLOR, font=("Arial", 11, "bold"))
        self._min_label.pack(side="left", padx=(0, 4))

        self._toggle_canvas = tk.Canvas(self._tog_frame, width=44, height=22, bg=BG_COLOR, highlightthickness=0, cursor="hand2")
        self._toggle_canvas.pack(side="left")
        self._toggle_canvas.bind("<Button-1>", lambda e: self._handle_toggle())

        self._max_label = tk.Label(self._tog_frame, text="MAX", fg="#888888", bg=BG_COLOR, font=("Arial", 11, "bold"))
        self._max_label.pack(side="left", padx=(4, 0))
        self._draw_toggle()

        # Operational Velocity scale (Time slider)
        sp = tk.Frame(self, bg=BG_COLOR)
        sp.pack(side="left", padx=10)
        tk.Label(sp, text="Speed:", fg=TEXT_COLOR, bg=BG_COLOR, font=("Arial", 10)).pack(side="left")

        # Configured snap adjustments to exactly 100ms increments and widened horizontal footprint
        self.scale = tk.Scale(
            sp, from_=100, to=1500, resolution=100, orient="horizontal",
            variable=self.speed_var, bg=BG_COLOR, fg=TEXT_COLOR,
            highlightthickness=0, troughcolor="#333333", length=160,
            showvalue=False, command=self._update_speed_label
        )
        self.scale.pack(side="left")

        # Informational tag presenting duration in milliseconds and seconds simultaneously
        tk.Label(sp, textvariable=self.speed_display_var, fg="#AAAAAA", bg=BG_COLOR, font=("Arial", 10), width=11).pack(side="left", padx=(2, 0))

        # Automatic Batch Inserters
        fl = tk.Frame(self, bg=BG_COLOR)
        fl.pack(side="left", padx=10)
        tk.Label(fl, text="Random Fill:", fg=TEXT_COLOR, bg=BG_COLOR, font=("Arial", 11)).pack(side="left", padx=4)

        self.fill_entry = tk.Entry(fl, width=6, font=("Arial", 11))
        self.fill_entry.pack(side="left", padx=4)

        self.fill_btn = tk.Button(
            fl, text="Fill", command=self._on_fill,
            bg="#2255AA", fg="white", activebackground="#3366CC", activeforeground="white",
            relief="flat", cursor="hand2", font=("Arial", 11, "bold"), padx=8
        )
        self.fill_btn.pack(side="left", padx=4)

    def _update_speed_label(self, val):
        ms = int(val)
        sec = ms / 1000.0
        self.speed_display_var.set(f"{ms}ms ({sec:.1f}s)")

    def _draw_toggle(self):
        c = self._toggle_canvas
        c.delete("all")
        color = "#FF8C00" if self._is_max else "#00CED1"
        self._rounded_rect(c, 1, 3, 43, 19, radius=8, fill=color, outline="")
        kx = 30 if self._is_max else 14
        c.create_oval(kx - 8, 3, kx + 8, 19, fill="white", outline="")

    def _handle_toggle(self):
        self._is_max = not self._is_max
        self._draw_toggle()
        self._min_label.config(fg="#00CED1" if not self._is_max else "#888888")
        self._max_label.config(fg="#FF8C00" if self._is_max else "#888888")
        self._on_toggle(self._is_max)

    def reset_toggle(self, is_max):
        self._is_max = is_max
        self._draw_toggle()
        self._min_label.config(fg="#00CED1" if not self._is_max else "#888888")
        self._max_label.config(fg="#FF8C00" if self._is_max else "#888888")

    def set_controls_state(self, state):
        for widget in (self.val_entry, self.pri_entry, self.fill_entry,
                       self.push_btn, self.pop_btn, self.clear_btn, self.fill_btn):
            widget.config(state=state)

    @staticmethod
    def _rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
        pts = [x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
               x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
               x1, y2, x1, y2-radius, x1, y1+radius, x1, y1]
        return canvas.create_polygon(pts, smooth=True, **kwargs)