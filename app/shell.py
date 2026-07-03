import tkinter as tk
from tkinter import messagebox, simpledialog

from .config import DEFAULT_EXAM_DATE, THEMES


class ShellMixin:
    def __init__(self, root):
        self.root = root
        self.root.title("國營企管衝刺管理工具")
        self.root.configure(bg="#f1f5f9")
        self.root.attributes("-topmost", True)
        self.root.resizable(True, True)

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = min(520, screen_width - 40)
        window_height = min(740, screen_height - 80)
        x = max(0, (screen_width - window_width) // 2)
        y = max(0, (screen_height - window_height) // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(min(480, window_width), min(640, window_height))

        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.today_key = self.get_today_key()
        self.active_tab = "todo"
        self.tab_frames = {}

        self.load_data()
        self.ensure_today_plan()
        self.define_colors()
        self.build_ui()
        self.bind_window_events()
        self.refresh_all()
        self.schedule_updates()

    # ── drag ─────────────────────────────────────────────────────────────────
    def bind_window_events(self):
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.titlebar.bind("<ButtonPress-1>", self.start_drag)
        self.titlebar.bind("<B1-Motion>", self.do_drag)
        for child in self.titlebar.winfo_children():
            child.bind("<ButtonPress-1>", self.start_drag)
            child.bind("<B1-Motion>", self.do_drag)

    def start_drag(self, event):
        self.drag_offset_x = event.x_root - self.root.winfo_x()
        self.drag_offset_y = event.y_root - self.root.winfo_y()

    def do_drag(self, event):
        self.root.geometry(f"+{event.x_root - self.drag_offset_x}+{event.y_root - self.drag_offset_y}")

    # ── titlebar ─────────────────────────────────────────────────────────────
    def build_titlebar(self):
        self.titlebar = tk.Frame(self.root, bg=self.titlebar_bg, height=46)
        self.titlebar.pack(fill="x")
        self.titlebar.pack_propagate(False)

        left = tk.Frame(self.titlebar, bg=self.titlebar_bg)
        left.pack(side="left", padx=16, fill="y")

        self.title_label = tk.Label(
            left,
            text=self.data["settings"].get("title", "國營企管衝刺管理工具"),
            fg="#f8fafc", bg=self.titlebar_bg, font=self.font_lg,
        )
        self.title_label.pack(side="left")

        tk.Button(
            left, text="✎", command=self._edit_title,
            bg=self.titlebar_bg, fg="#475569",
            bd=0, relief="flat", font=self.font_sm,
            padx=6, pady=2, cursor="hand2",
            highlightthickness=0,
            activebackground="#1e293b", activeforeground="#f8fafc",
        ).pack(side="left", padx=(8, 0))

        self.status_label = tk.Label(
            left, text="", fg="#475569", bg=self.titlebar_bg, font=self.font_sm,
        )
        self.status_label.pack(side="left", padx=(10, 0))

        right = tk.Frame(self.titlebar, bg=self.titlebar_bg)
        right.pack(side="right", padx=12, fill="y")

        tk.Button(
            right, text="✕", command=self.root.destroy,
            bg="#ef4444", fg="white",
            bd=0, relief="flat", font=self.font_sm,
            padx=10, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground="#dc2626", activeforeground="white",
        ).pack(side="right")

        tk.Button(
            right, text="設定", command=self.open_display_settings,
            bg="#1e293b", fg="#94a3b8",
            bd=0, relief="flat", font=self.font_sm,
            padx=12, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground="#334155", activeforeground="#f8fafc",
        ).pack(side="right", padx=(0, 8))

        tk.Button(
            right, text="儲存", command=self.save_data,
            bg="#1e293b", fg="#94a3b8",
            bd=0, relief="flat", font=self.font_sm,
            padx=12, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground="#334155", activeforeground="#f8fafc",
        ).pack(side="right", padx=(0, 8))

        # theme dots
        dot_frame = tk.Frame(right, bg=self.titlebar_bg)
        dot_frame.pack(side="right", padx=(0, 12))
        for key, info in THEMES.items():
            is_active = (key == self._theme_name)
            dot = tk.Button(
                dot_frame,
                text=info["_label"],
                command=lambda k=key: self.switch_theme(k),
                bg=info["_dot"],
                fg="white",
                bd=0, relief="flat",
                font=(self.font_sm[0], 8, "bold") if is_active else (self.font_sm[0], 8),
                padx=6, pady=4, cursor="hand2",
                highlightthickness=2 if is_active else 0,
                highlightbackground="white",
                activebackground=info["_dot"], activeforeground="white",
            )
            dot.pack(side="left", padx=1)

    def open_display_settings(self):
        win = tk.Toplevel(self.root)
        win.title("顯示設定")
        win.configure(bg=self.bg)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        win_width = min(360, int(screen_width * 0.32))
        win_height = min(240, int(screen_height * 0.28))
        win.geometry(f"{win_width}x{win_height}")
        win.resizable(False, False)
        win.attributes("-topmost", True)

        tk.Label(win, text="介面縮放 (%)", fg=self.text, bg=self.bg, font=self.font_md).pack(pady=(18, 6))

        scale_var = tk.IntVar(value=self.data["settings"].get("ui_scale", 100))
        scale_frame = tk.Frame(win, bg=self.bg)
        scale_frame.pack(pady=(0, 14))

        scale_entry = tk.Entry(
            scale_frame, textvariable=scale_var, width=6,
            font=self.font_ui, bd=0, relief="flat",
            highlightthickness=1, highlightcolor=self.accent, highlightbackground=self.border,
            bg=self.input_bg, fg=self.text, insertbackground=self.text,
        )
        scale_entry.pack(side="left", padx=(0, 8))

        tk.Label(win, text="60 - 200", fg=self.muted, bg=self.bg, font=self.font_sm).pack()

        btn_frame = tk.Frame(win, bg=self.bg)
        btn_frame.pack(fill="x", padx=16, pady=(16, 0))

        def apply_scale():
            val = scale_var.get()
            if val < 60 or val > 200:
                messagebox.showwarning("輸入錯誤", "請輸入 60 到 200 之間的數值。", parent=win)
                return
            self.data["settings"]["ui_scale"] = val
            self.define_fonts()
            self.rebuild_ui()
            self.save_data()
            win.destroy()

        tk.Button(
            btn_frame, text="套用", command=apply_scale,
            bg=self.accent, fg="white",
            bd=0, relief="flat", font=self.font_sm,
            padx=12, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=self.accent_lt, activeforeground="white",
        ).pack(side="left")

        tk.Button(
            btn_frame, text="取消", command=win.destroy,
            bg=self.border, fg=self.text,
            bd=0, relief="flat", font=self.font_sm,
            padx=12, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=self.card, activeforeground=self.text,
        ).pack(side="right")

    # ── countdown strip ───────────────────────────────────────────────────────
    def build_countdown_strip(self):
        strip = tk.Frame(self.root, bg=self.card)
        strip.pack(fill="x")
        tk.Frame(self.root, bg=self.border, height=1).pack(fill="x")

        inner = tk.Frame(strip, bg=self.card)
        inner.pack(fill="x", padx=20, pady=14)

        left = tk.Frame(inner, bg=self.card)
        left.pack(side="left")

        self.countdown_label = tk.Label(
            left, text="--", fg=self.accent, bg=self.card, font=self.font_xl,
        )
        self.countdown_label.pack(anchor="w")

        self.countdown_meta = tk.Label(
            left, text="", fg=self.muted, bg=self.card, font=self.font_sm,
        )
        self.countdown_meta.pack(anchor="w", pady=(2, 0))

        right = tk.Frame(inner, bg=self.card)
        right.pack(side="right")

        tk.Label(right, text="考試日期", fg=self.muted, bg=self.card, font=self.font_sm).pack(anchor="e")
        date_row = tk.Frame(right, bg=self.card)
        date_row.pack(anchor="e", pady=(6, 0))

        self.exam_date_var = tk.StringVar()
        tk.Entry(
            date_row, textvariable=self.exam_date_var, width=11,
            font=self.font_ui, bd=0, relief="flat",
            highlightthickness=1, highlightcolor=self.accent, highlightbackground=self.border,
            bg=self.input_bg, fg=self.text, insertbackground=self.text,
        ).pack(side="left")

        tk.Button(
            date_row, text="更新", command=self.update_exam_date,
            bg=self.accent, fg="white",
            bd=0, relief="flat", font=self.font_sm,
            padx=10, pady=4, cursor="hand2",
            highlightthickness=0,
            activebackground=self.accent_lt, activeforeground="white",
        ).pack(side="left", padx=(8, 0))

    # ── tab bar ───────────────────────────────────────────────────────────────
    def build_tab_bar(self):
        self._tab_indicators = {}
        outer = tk.Frame(self.root, bg=self.card)
        outer.pack(fill="x")
        tk.Frame(self.root, bg=self.border, height=1).pack(fill="x")

        tabbar = tk.Frame(outer, bg=self.card)
        tabbar.pack(side="left", padx=4)

        self.tab_buttons = {}
        for key, label in [("todo", "待辦"), ("notes", "錯題"), ("stats", "統計")]:
            col = tk.Frame(tabbar, bg=self.card)
            col.pack(side="left", padx=2)
            btn = tk.Button(
                col, text=label, font=self.font_md,
                bd=0, relief="flat", padx=16, pady=10,
                cursor="hand2", bg=self.card,
                highlightthickness=0,
                command=lambda k=key: self.switch_tab(k),
            )
            btn.pack(fill="x")
            ind = tk.Frame(col, height=2, bg=self.card)
            ind.pack(fill="x")
            self.tab_buttons[key] = btn
            self._tab_indicators[key] = ind

    def switch_tab(self, key):
        self.active_tab = key
        for k, btn in self.tab_buttons.items():
            if k == key:
                btn.config(fg=self.accent, font=(self.font_md[0], self.font_md[1], "bold"), bg=self.card)
                self._tab_indicators[k].config(bg=self.accent)
            else:
                btn.config(fg=self.muted, font=self.font_md, bg=self.card)
                self._tab_indicators[k].config(bg=self.card)
        for k, frame in self.tab_frames.items():
            if k == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        if key == "stats":
            self.root.after(60, lambda: self.switch_stats_mode(
                getattr(self, "stats_mode", "chart")))

    # ── title editing ─────────────────────────────────────────────────────────
    def _edit_title(self):
        cur = self.data["settings"].get("title", "國營企管衝刺管理工具")
        val = simpledialog.askstring("修改標題", "請輸入新標題：", initialvalue=cur, parent=self.root)
        if val and val.strip():
            val = val.strip()
            self.data["settings"]["title"] = val
            self.title_label.config(text=val)
            self.root.title(val)
            self.save_data()

    # ════════════════════════════════════════════════════════════════════════
    # REFRESH METHODS
    # ════════════════════════════════════════════════════════════════════════

    def refresh_countdown(self):
        delta = self.get_days_left()
        days, clock = self.format_countdown(delta)
        exam_date   = self.exam_date_var.get().strip() or DEFAULT_EXAM_DATE
        if delta.total_seconds() > 0:
            self.countdown_label.config(text=f"{days} 天  {clock}")
            self.countdown_meta.config(text=f"距 {exam_date} 考試")
        elif delta.total_seconds() == 0:
            self.countdown_label.config(text="今天考試！")
            self.countdown_meta.config(text=exam_date)
        else:
            self.countdown_label.config(text=f"已過 {abs(days)} 天")
            self.countdown_meta.config(text=f"考試日：{exam_date}")

    def refresh_all(self):
        self.refresh_day_state()
        self.exam_date_var.set(self.exam_date)
        self.refresh_countdown()
        self.render_todos()
        self.refresh_stats()
        self.refresh_notes()
        self.refresh_study_chart()

    def schedule_updates(self):
        self.refresh_day_state()
        self.refresh_countdown()
        self.root.after(1000, self.schedule_updates)

    def refresh_day_state(self):
        current_key = self.get_today_key()
        if current_key != self.today_key:
            self.today_key = current_key
            self.ensure_today_plan()
            self.exam_date_var.set(self.exam_date)
