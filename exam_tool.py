import calendar
import json
import os
import time
import ctypes
import tkinter as tk
from datetime import datetime, date, timedelta
from tkinter import messagebox, simpledialog

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "exam_progress.json")
DEFAULT_EXAM_DATE = "2026-10-18"
DEFAULT_PLAN = [
    {"section": "上午", "time_start": "08:30", "time_end": "10:30", "subject": "企業管理"},
    {"section": "下午", "time_start": "13:30", "time_end": "15:30", "subject": "經濟學"},
    {"section": "晚上", "time_start": "19:00", "time_end": "20:00", "subject": "歷屆題"},
    {"section": "晚上", "time_start": "20:00", "time_end": "21:00", "subject": "法學"},
    {"section": "晚上", "time_start": "21:00", "time_end": "22:30", "subject": "國英"},
]
DEFAULT_SUBJECTS = ["企業管理", "經濟學", "法學", "國英", "歷屆題"]
SECTION_COLORS = {"上午": "#f59e0b", "下午": "#3b82f6", "晚上": "#8b5cf6", "今日": "#10b981"}

THEMES = {
    "light": {
        "bg": "#f1f5f9", "titlebar_bg": "#0f172a", "strip_bg": "#e2e8f0",
        "card": "#ffffff", "border": "#cbd5e1", "text": "#1e293b",
        "muted": "#64748b", "accent": "#6366f1", "accent_lt": "#818cf8",
        "success": "#22c55e", "warn": "#ef4444", "done_fg": "#94a3b8",
        "input_bg": "#ffffff",
        "_dot": "#6366f1", "_label": "淺色",
    },
    "dark": {
        "bg": "#0f172a", "titlebar_bg": "#020617", "strip_bg": "#1e293b",
        "card": "#1e293b", "border": "#334155", "text": "#e2e8f0",
        "muted": "#94a3b8", "accent": "#818cf8", "accent_lt": "#a5b4fc",
        "success": "#4ade80", "warn": "#f87171", "done_fg": "#475569",
        "input_bg": "#334155",
        "_dot": "#818cf8", "_label": "深色",
    },
    "coffee": {
        "bg": "#2c1810", "titlebar_bg": "#180d08", "strip_bg": "#3d2418",
        "card": "#3d2418", "border": "#5c3820", "text": "#f5e6d3",
        "muted": "#b08060", "accent": "#e8944a", "accent_lt": "#f0aa70",
        "success": "#6abf6a", "warn": "#f08070", "done_fg": "#7a5040",
        "input_bg": "#4a2e1c",
        "_dot": "#e8944a", "_label": "咖啡",
    },
    "light_coffee": {
        "bg": "#fdf6ee", "titlebar_bg": "#3d2412", "strip_bg": "#f0e0cc",
        "card": "#ffffff", "border": "#d4b896", "text": "#3d2412",
        "muted": "#8b6040", "accent": "#b8581a", "accent_lt": "#d4784a",
        "success": "#2e7d32", "warn": "#c62828", "done_fg": "#b09878",
        "input_bg": "#ffffff",
        "_dot": "#b8581a", "_label": "淺咖啡",
    },
}


class ExamPrepApp:
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

    # ── colors ────────────────────────────────────────────────────────────────
    def define_colors(self):
        theme_name = self.data.get("settings", {}).get("theme", "light")
        t = THEMES.get(theme_name, THEMES["light"])
        self.bg          = t["bg"]
        self.titlebar_bg = t["titlebar_bg"]
        self.strip_bg    = t["strip_bg"]
        self.card        = t["card"]
        self.border      = t["border"]
        self.text        = t["text"]
        self.muted       = t["muted"]
        self.accent      = t["accent"]
        self.accent_lt   = t["accent_lt"]
        self.success     = t["success"]
        self.warn        = t["warn"]
        self.done_fg     = t["done_fg"]
        self.input_bg    = t["input_bg"]
        self._theme_name = theme_name
        self.define_fonts()
        self.root.configure(bg=self.bg)

    def define_fonts(self):
        scale = self.data.get("settings", {}).get("ui_scale", 100)
        scale = max(60, min(200, int(scale)))
        factor = scale / 100
        self.font_ui  = ("Microsoft JhengHei UI", max(8, int(10 * factor)))
        self.font_sm  = ("Microsoft JhengHei UI", max(8, int(9 * factor)))
        self.font_md  = ("Microsoft JhengHei UI", max(8, int(11 * factor)))
        self.font_lg  = ("Microsoft JhengHei UI", max(10, int(13 * factor)), "bold")
        self.font_xl  = ("Microsoft JhengHei UI", max(16, int(24 * factor)), "bold")
        self.root.option_add("*Font", self.font_ui)
        try:
            self.root.tk.call("tk", "scaling", factor)
        except Exception:
            pass

    def rebuild_ui(self):
        prev_tab = getattr(self, "active_tab", "todo")
        for widget in self.root.winfo_children():
            widget.destroy()
        self.tab_frames = {}
        self._editing_todo_id = None
        self._noting_todo_id = None
        self.define_colors()
        self.build_ui()
        self.bind_window_events()
        self.switch_tab(prev_tab)
        self.refresh_all()

    # ── theme switch ──────────────────────────────────────────────────────────
    def switch_theme(self, theme_name):
        if theme_name == getattr(self, "_theme_name", None):
            return
        self.data["settings"]["theme"] = theme_name
        self.save_data()
        self.rebuild_ui()

    # ── build UI ──────────────────────────────────────────────────────────────
    def build_ui(self):
        self.build_titlebar()
        self.build_countdown_strip()
        self.build_tab_bar()
        self.build_tab_todo()
        self.build_tab_notes()
        self.build_tab_stats()
        self.switch_tab("todo")

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
        win.geometry("320x220")
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

    # ── Tab 待辦 ──────────────────────────────────────────────────────────────
    def build_tab_todo(self):
        frame = tk.Frame(self.root, bg=self.bg)
        self.tab_frames["todo"] = frame

        hdr = tk.Frame(frame, bg=self.bg)
        hdr.pack(fill="x", padx=16, pady=(14, 6))

        nav = tk.Frame(hdr, bg=self.bg)
        nav.pack(side="left")
        self._nav_btn(nav, "←", self._prev_day).pack(side="left")

        self.nav_date_var = tk.StringVar(value=self.view_date_key)
        tk.Button(
            nav, textvariable=self.nav_date_var,
            command=self._open_cal_picker,
            bg=self.card, fg=self.text,
            bd=1, relief="solid", font=self.font_md,
            padx=12, pady=5, cursor="hand2",
            highlightthickness=0,
            activebackground=self.strip_bg, activeforeground=self.text,
        ).pack(side="left", padx=6)

        self.nav_weekday = tk.Label(
            nav, text="", fg=self.muted, bg=self.bg,
            font=(self.font_md[0], self.font_md[1], "bold"),
        )
        self.nav_weekday.pack(side="left", padx=(0, 8))

        self._nav_btn(nav, "→", self._next_day).pack(side="left")
        tk.Button(
            nav, text="今日", command=self._goto_today,
            bg=self.accent, fg="white",
            bd=0, relief="flat", font=self.font_sm,
            padx=12, pady=5, cursor="hand2",
            highlightthickness=0,
            activebackground=self.accent_lt, activeforeground="white",
        ).pack(side="left", padx=(8, 0))

        self.today_progress_label = tk.Label(hdr, text="", fg=self.success, bg=self.bg, font=self.font_sm)
        self.today_progress_label.pack(side="right")

        self.pb_canvas = tk.Canvas(frame, height=3, bg=self.border, bd=0, highlightthickness=0)
        self.pb_canvas.pack(fill="x", padx=16, pady=(0, 8))
        self.pb_canvas.bind("<Configure>", lambda _: self.draw_progress_bar())

        list_outer = tk.Frame(frame, bg=self.bg)
        list_outer.pack(fill="both", expand=True, padx=16)

        self.todo_canvas = tk.Canvas(list_outer, bg=self.bg, bd=0, highlightthickness=0)
        todo_sb = tk.Scrollbar(list_outer, orient="vertical", command=self.todo_canvas.yview)
        self.todo_canvas.configure(yscrollcommand=todo_sb.set)
        todo_sb.pack(side="right", fill="y")
        self.todo_canvas.pack(side="left", fill="both", expand=True)

        self.todo_list_frame = tk.Frame(self.todo_canvas, bg=self.bg)
        self._todo_win = self.todo_canvas.create_window((0, 0), window=self.todo_list_frame, anchor="nw")
        self.todo_list_frame.bind("<Configure>", lambda _: self.todo_canvas.configure(
            scrollregion=self.todo_canvas.bbox("all")))
        self.todo_canvas.bind("<Configure>", lambda e: self.todo_canvas.itemconfig(
            self._todo_win, width=e.width))
        self.todo_canvas.bind("<MouseWheel>", lambda e: self.todo_canvas.yview_scroll(
            -1 * (e.delta // 120), "units"))

        tk.Frame(frame, bg=self.border, height=1).pack(fill="x")
        add_strip = tk.Frame(frame, bg=self.card)
        add_strip.pack(fill="x")

        add_inner = tk.Frame(add_strip, bg=self.card)
        add_inner.pack(fill="x", padx=16, pady=12)

        r1 = tk.Frame(add_inner, bg=self.card)
        r1.pack(fill="x", pady=(0, 8))

        tk.Label(r1, text="開始", fg=self.muted, bg=self.card, font=self.font_sm).pack(side="left", padx=(0, 6))
        self.todo_time_start_var = tk.StringVar(value="08:30")
        self.todo_start_h_var = tk.StringVar(value="08")
        self.todo_start_m_var = tk.StringVar(value="30")
        _h_vals = tuple(f"{h:02d}" for h in range(24))
        self._mk_spin(r1, self.todo_start_h_var, _h_vals, self.card, width=3).pack(side="left")
        tk.Label(r1, text=":", fg=self.text, bg=self.card, font=self.font_md).pack(side="left", padx=1)
        self._mk_spin(r1, self.todo_start_m_var, ("00", "15", "30", "45"), self.card, width=3).pack(side="left", padx=(0, 14))

        def _sync_add_start(*_):
            self.todo_time_start_var.set(f"{self.todo_start_h_var.get()}:{self.todo_start_m_var.get()}")
        self.todo_start_h_var.trace_add("write", _sync_add_start)
        self.todo_start_m_var.trace_add("write", _sync_add_start)

        tk.Label(r1, text="時數", fg=self.muted, bg=self.card, font=self.font_sm).pack(side="left", padx=(0, 6))
        self.todo_hours_var = tk.StringVar(value="1.5")
        self._mk_spin(r1, self.todo_hours_var,
                      ("0.5", "1", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5"),
                      self.card, width=4).pack(side="left", padx=(0, 10))

        self.todo_end_preview = tk.Label(r1, text="→ 10:00", fg=self.accent, bg=self.card, font=self.font_sm)
        self.todo_end_preview.pack(side="left")
        self.todo_time_start_var.trace_add("write", self._update_todo_end_preview)
        self.todo_hours_var.trace_add("write", self._update_todo_end_preview)

        r2 = tk.Frame(add_inner, bg=self.card)
        r2.pack(fill="x")

        tk.Label(r2, text="項目", fg=self.muted, bg=self.card, font=self.font_sm).pack(side="left", padx=(0, 6))
        self.todo_combo = self._make_dropdown(r2, self._get_todo_options())
        self.todo_combo.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            r2, text="⚙", command=self.open_todo_options_manager,
            bg=self.card, fg=self.muted,
            bd=0, relief="flat", font=(self.font_sm[0], 13),
            padx=4, pady=4, cursor="hand2",
            highlightthickness=0,
            activebackground=self.strip_bg, activeforeground=self.accent,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            r2, text="新增", command=self.add_custom_todo,
            bg=self.accent, fg="white",
            bd=0, relief="flat", font=self.font_sm,
            padx=16, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=self.accent_lt, activeforeground="white",
        ).pack(side="left")

    def draw_progress_bar(self, rate=0):
        w = self.pb_canvas.winfo_width()
        if w < 2:
            return
        self.pb_canvas.delete("all")
        self.pb_canvas.create_rectangle(0, 0, w, 3, fill=self.border, outline="")
        if rate > 0:
            self.pb_canvas.create_rectangle(0, 0, int(w * rate / 100), 3, fill=self.accent, outline="")

    # ── Tab 錯題 ──────────────────────────────────────────────────────────────
    def build_tab_notes(self):
        frame = tk.Frame(self.root, bg=self.bg)
        self.tab_frames["notes"] = frame

        mode_bar = tk.Frame(frame, bg=self.card)
        mode_bar.pack(fill="x")
        tk.Frame(frame, bg=self.border, height=1).pack(fill="x")

        self.note_add_btn = tk.Button(
            mode_bar, text="＋ 新增", font=self.font_sm,
            bd=0, relief="flat", padx=16, pady=10, cursor="hand2",
            command=lambda: self.switch_notes_mode("add"),
        )
        self.note_add_btn.pack(side="left")

        self.note_search_btn = tk.Button(
            mode_bar, text="🔍 查詢", font=self.font_sm,
            bd=0, relief="flat", padx=16, pady=10, cursor="hand2",
            command=lambda: self.switch_notes_mode("search"),
        )
        self.note_search_btn.pack(side="left")

        self.note_count_label = tk.Label(
            mode_bar, text="0 筆", fg=self.muted, bg=self.card, font=self.font_sm,
        )
        self.note_count_label.pack(side="right", padx=16)

        self.notes_form_area = tk.Frame(frame, bg=self.strip_bg)
        self.notes_form_area.pack(fill="x")
        tk.Frame(frame, bg=self.border, height=1).pack(fill="x")

        # add form
        self.notes_add_frame = tk.Frame(self.notes_form_area, bg=self.strip_bg)
        add_inner = tk.Frame(self.notes_add_frame, bg=self.strip_bg)
        add_inner.pack(fill="x", padx=16, pady=12)

        r0 = tk.Frame(add_inner, bg=self.strip_bg)
        r0.pack(fill="x", pady=(0, 6))
        tk.Label(r0, text="科目", fg=self.muted, bg=self.strip_bg,
                 font=self.font_sm, width=5, anchor="w").pack(side="left")
        opts0 = self._get_todo_options()
        self.note_subject_combo = self._make_dropdown(r0, opts0, initial=opts0[0] if opts0 else "")
        self.note_subject_combo.pack(side="left", fill="x", expand=True)

        self.note_question_var = tk.StringVar()
        self.note_answer_var   = tk.StringVar()
        self.note_reason_var   = tk.StringVar()
        self._note_form_row(add_inner, "題目", self.note_question_var)
        self._note_form_row(add_inner, "答案", self.note_answer_var)
        self._note_form_row(add_inner, "原因", self.note_reason_var)

        add_btn_row = tk.Frame(add_inner, bg=self.strip_bg)
        add_btn_row.pack(fill="x", pady=(10, 0))
        tk.Button(
            add_btn_row, text="新增錯題", command=self.add_note,
            bg=self.accent, fg="white",
            bd=0, relief="flat", font=self.font_sm,
            padx=16, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=self.accent_lt, activeforeground="white",
        ).pack(side="left")
        tk.Button(
            add_btn_row, text="清除全部", command=self.clear_notes,
            bg=self.strip_bg, fg=self.warn,
            bd=1, relief="solid", font=self.font_sm,
            padx=12, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=self.warn, activeforeground="white",
        ).pack(side="left", padx=(10, 0))

        # search form
        self.notes_search_frame = tk.Frame(self.notes_form_area, bg=self.strip_bg)
        srch_inner = tk.Frame(self.notes_search_frame, bg=self.strip_bg)
        srch_inner.pack(fill="x", padx=16, pady=12)

        kw_row = tk.Frame(srch_inner, bg=self.strip_bg)
        kw_row.pack(fill="x", pady=(0, 8))
        tk.Label(kw_row, text="關鍵字", fg=self.muted, bg=self.strip_bg,
                 font=self.font_sm, width=6, anchor="w").pack(side="left")
        self.note_search_var = tk.StringVar()
        kw_entry = tk.Entry(
            kw_row, textvariable=self.note_search_var,
            font=self.font_ui, bd=0, relief="flat",
            highlightthickness=1, highlightcolor=self.accent, highlightbackground=self.border,
            bg=self.input_bg, fg=self.text, insertbackground=self.text,
        )
        kw_entry.pack(side="left", fill="x", expand=True)
        kw_entry.bind("<Return>", lambda _: self.search_notes())

        filter_row = tk.Frame(srch_inner, bg=self.strip_bg)
        filter_row.pack(fill="x", pady=(0, 8))
        tk.Label(filter_row, text="科目", fg=self.muted, bg=self.strip_bg,
                 font=self.font_sm, width=6, anchor="w").pack(side="left")
        self._filter_subject_dd = self._make_dropdown(
            filter_row, ["全部科目"] + self._get_todo_options(), initial="全部科目")
        self._filter_subject_dd.pack(side="left", padx=(0, 12))

        tk.Label(filter_row, text="時段", fg=self.muted, bg=self.strip_bg,
                 font=self.font_sm).pack(side="left", padx=(0, 6))
        self._filter_period_dd = self._make_dropdown(
            filter_row, ["全部", "今天", "本週", "本月"], initial="全部")
        self._filter_period_dd.pack(side="left")

        srch_btn_row = tk.Frame(srch_inner, bg=self.strip_bg)
        srch_btn_row.pack(fill="x")
        tk.Button(
            srch_btn_row, text="搜尋", command=self.search_notes,
            bg=self.accent, fg="white",
            bd=0, relief="flat", font=self.font_sm,
            padx=16, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=self.accent_lt, activeforeground="white",
        ).pack(side="left")
        tk.Button(
            srch_btn_row, text="清除篩選", command=self.clear_note_search,
            bg=self.strip_bg, fg=self.muted,
            bd=1, relief="solid", font=self.font_sm,
            padx=10, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=self.border, activeforeground=self.text,
        ).pack(side="left", padx=(8, 0))
        self.note_result_label = tk.Label(
            srch_btn_row, text="", fg=self.muted, bg=self.strip_bg, font=self.font_sm,
        )
        self.note_result_label.pack(side="right")

        cards_outer = tk.Frame(frame, bg=self.bg)
        cards_outer.pack(fill="both", expand=True)

        self.note_canvas = tk.Canvas(cards_outer, bg=self.bg, bd=0, highlightthickness=0)
        note_sb = tk.Scrollbar(cards_outer, orient="vertical", command=self.note_canvas.yview)
        self.note_canvas.configure(yscrollcommand=note_sb.set)
        note_sb.pack(side="right", fill="y")
        self.note_canvas.pack(side="left", fill="both", expand=True)

        self.note_cards_frame = tk.Frame(self.note_canvas, bg=self.bg)
        self._note_cards_win = self.note_canvas.create_window(
            (0, 0), window=self.note_cards_frame, anchor="nw")
        self.note_cards_frame.bind("<Configure>", lambda _: self.note_canvas.configure(
            scrollregion=self.note_canvas.bbox("all")))
        self.note_canvas.bind("<Configure>", lambda e: self.note_canvas.itemconfig(
            self._note_cards_win, width=e.width))
        self.note_canvas.bind("<MouseWheel>", lambda e: self.note_canvas.yview_scroll(
            -1 * (e.delta // 120), "units"))

        self.switch_notes_mode("add")

    def _note_form_row(self, parent, label, var):
        row = tk.Frame(parent, bg=self.strip_bg)
        row.pack(fill="x", pady=(0, 6))
        tk.Label(row, text=label, fg=self.muted, bg=self.strip_bg,
                 font=self.font_sm, width=5, anchor="w").pack(side="left")
        tk.Entry(
            row, textvariable=var,
            font=self.font_ui, bd=0, relief="flat",
            highlightthickness=1, highlightcolor=self.accent, highlightbackground=self.border,
            bg=self.input_bg, fg=self.text, insertbackground=self.text,
        ).pack(side="left", fill="x", expand=True)

    # ── Tab 統計 ──────────────────────────────────────────────────────────────
    def build_tab_stats(self):
        frame = tk.Frame(self.root, bg=self.bg)
        self.tab_frames["stats"] = frame

        mode_bar = tk.Frame(frame, bg=self.card)
        mode_bar.pack(fill="x")
        tk.Frame(frame, bg=self.border, height=1).pack(fill="x")

        self.stats_chart_btn = tk.Button(
            mode_bar, text="📊 讀書統計", font=self.font_sm,
            bd=0, relief="flat", padx=16, pady=10, cursor="hand2",
            command=lambda: self.switch_stats_mode("chart"),
        )
        self.stats_chart_btn.pack(side="left")

        self.stats_detail_btn = tk.Button(
            mode_bar, text="🗓 全部詳細項", font=self.font_sm,
            bd=0, relief="flat", padx=16, pady=10, cursor="hand2",
            command=lambda: self.switch_stats_mode("detail"),
        )
        self.stats_detail_btn.pack(side="left")

        cards = tk.Frame(frame, bg=self.bg)
        cards.pack(fill="x", padx=16, pady=(16, 10))
        for i in range(3):
            cards.grid_columnconfigure(i, weight=1)

        self.stat_today = self._stat_card(cards, "今日完成率", 0, accent=self.success)
        self.stat_week  = self._stat_card(cards, "本週完成率", 1, accent="#3b82f6")
        self.stat_days  = self._stat_card(cards, "累積讀書天數", 2, accent=self.accent)

        tk.Frame(frame, bg=self.border, height=1).pack(fill="x", padx=16)

        self.stats_detail = tk.Label(
            frame, text="", fg=self.muted, bg=self.bg,
            font=self.font_sm, justify="left", anchor="w",
        )
        self.stats_detail.pack(anchor="w", padx=20, pady=(6, 4))

        self.stats_chart_frame = tk.Frame(frame, bg=self.bg)
        chart_card = tk.Frame(self.stats_chart_frame, bg=self.card, bd=1, relief="solid")
        chart_card.pack(fill="both", expand=True, padx=16, pady=(4, 12))
        tk.Label(chart_card, text="根據已完成待辦自動計算",
                 fg=self.muted, bg=self.card, font=self.font_sm,
                 anchor="w", padx=14).pack(fill="x", pady=(8, 0))
        self.study_chart_canvas = tk.Canvas(chart_card, bg=self.card, bd=0, highlightthickness=0)
        self.study_chart_canvas.pack(fill="both", expand=True, pady=(4, 8))
        self.study_chart_canvas.bind("<Configure>", lambda _: self.refresh_study_chart())

        self.stats_detail_frame = tk.Frame(frame, bg=self.bg)
        detail_card = tk.Frame(self.stats_detail_frame, bg=self.card, bd=1, relief="solid")
        detail_card.pack(fill="both", expand=True, padx=16, pady=(4, 12))

        detail_hdr = tk.Frame(detail_card, bg=self.strip_bg)
        detail_hdr.pack(fill="x")
        self.detail_date_lbl = tk.Label(
            detail_hdr, text="全部記錄", fg=self.muted, bg=self.strip_bg, font=self.font_sm,
        )
        self.detail_date_lbl.pack(anchor="w", padx=10, pady=6)

        _dc_outer = tk.Frame(detail_card, bg=self.card)
        _dc_outer.pack(fill="both", expand=True)
        self.detail_canvas = tk.Canvas(_dc_outer, bg=self.card, bd=0, highlightthickness=0)
        _dc_sb = tk.Scrollbar(_dc_outer, orient="vertical", command=self.detail_canvas.yview)
        self.detail_canvas.configure(yscrollcommand=_dc_sb.set)
        _dc_sb.pack(side="right", fill="y")
        self.detail_canvas.pack(side="left", fill="both", expand=True)

        self.detail_items_frame = tk.Frame(self.detail_canvas, bg=self.card)
        self._dc_win = self.detail_canvas.create_window(
            (0, 0), window=self.detail_items_frame, anchor="nw")
        self.detail_items_frame.bind("<Configure>", lambda e: self.detail_canvas.configure(
            scrollregion=self.detail_canvas.bbox("all")))
        self.detail_canvas.bind("<Configure>", lambda e: self.detail_canvas.itemconfig(
            self._dc_win, width=e.width))
        self.detail_canvas.bind("<Enter>", lambda e: self.root.bind_all(
            "<MouseWheel>",
            lambda ev: self.detail_canvas.yview_scroll(-1 * (ev.delta // 120), "units")))
        self.detail_canvas.bind("<Leave>", lambda e: self.root.unbind_all("<MouseWheel>"))

        self.detail_summary_lbl = tk.Label(
            detail_card, text="", fg=self.muted, bg=self.card,
            font=self.font_sm, anchor="e", padx=10, pady=4,
        )
        self.detail_summary_lbl.pack(fill="x")

        self.switch_stats_mode("chart")

    def switch_stats_mode(self, mode):
        self.stats_mode = mode
        if mode == "chart":
            if hasattr(self, "stats_detail_frame"):
                self.stats_detail_frame.pack_forget()
            self.stats_chart_frame.pack(fill="both", expand=True)
            self.stats_chart_btn.config(
                bg=self.card, fg=self.accent,
                font=(self.font_sm[0], self.font_sm[1], "bold"))
            self.stats_detail_btn.config(bg=self.card, fg=self.muted, font=self.font_sm)
            self.root.after(50, self.refresh_study_chart)
        else:
            if hasattr(self, "stats_chart_frame"):
                self.stats_chart_frame.pack_forget()
            self.stats_detail_frame.pack(fill="both", expand=True)
            self.stats_detail_btn.config(
                bg=self.card, fg=self.accent,
                font=(self.font_sm[0], self.font_sm[1], "bold"))
            self.stats_chart_btn.config(bg=self.card, fg=self.muted, font=self.font_sm)
            self.refresh_stats_detail()

    def _stat_card(self, parent, title, col, accent=None):
        accent = accent or self.accent
        c = tk.Frame(parent, bg=self.card, bd=1, relief="solid")
        c.grid(row=0, column=col, padx=(0 if col == 0 else 8, 0), sticky="nsew")
        tk.Frame(c, bg=accent, height=3).pack(fill="x")
        tk.Label(c, text=title, fg=self.muted, bg=self.card, font=self.font_sm).pack(pady=(10, 4))
        lbl = tk.Label(c, text="--", fg=accent, bg=self.card,
                       font=("Microsoft JhengHei UI", 22, "bold"))
        lbl.pack(pady=(0, 12))
        return lbl

    # ── button helpers ────────────────────────────────────────────────────────
    def _nav_btn(self, parent, text, command):
        return tk.Button(
            parent, text=text, command=command,
            bg=self.card, fg=self.text,
            bd=1, relief="solid", font=self.font_ui,
            padx=10, pady=5, cursor="hand2",
            highlightthickness=0,
            activebackground=self.strip_bg, activeforeground=self.text,
        )

    def _btn(self, parent, text, command, bg, fg, border=False):
        is_accent = (bg == self.accent)
        is_warn   = (fg == self.warn)
        if is_accent:
            abg, afg = self.accent_lt, "white"
        elif is_warn:
            abg, afg = self.warn, "white"
        else:
            abg, afg = self.border, self.text
        return tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, font=self.font_ui,
            bd=1 if border else 0,
            relief="solid" if border else "flat",
            padx=14, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=abg,
            activeforeground=afg,
        )

    # ── custom dropdown (no ttk.Combobox) ────────────────────────────────────
    def _make_dropdown(self, parent, values, initial="", **pack_kw):
        vals  = list(values)
        init  = initial if initial else (vals[0] if vals else "")
        var   = tk.StringVar(value=init)
        _ref  = [None]  # popup reference

        outer = tk.Frame(
            parent, bg=self.input_bg,
            highlightbackground=self.border, highlightthickness=1,
        )

        disp = tk.Button(
            outer, textvariable=var,
            anchor="w", bg=self.input_bg, fg=self.text,
            relief="flat", bd=0, font=self.font_ui,
            padx=10, pady=5, cursor="hand2",
            highlightthickness=0,
            activebackground=self.strip_bg, activeforeground=self.text,
        )
        disp.pack(side="left", fill="x", expand=True)

        arrow = tk.Label(outer, text="▾", bg=self.input_bg, fg=self.muted,
                         font=(self.font_sm[0], 11), padx=8, cursor="hand2")
        arrow.pack(side="right")

        def _open():
            if _ref[0] and _ref[0].winfo_exists():
                _ref[0].destroy()
                _ref[0] = None
                return

            popup = tk.Toplevel(self.root)
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)
            _ref[0] = popup

            outer.update_idletasks()
            pw = max(outer.winfo_width(), 120)
            px = outer.winfo_rootx()
            py = outer.winfo_rooty() + outer.winfo_height()
            ph = min(len(vals) * 28 + 6, 220)
            popup.geometry(f"{pw}x{ph}+{px}+{py}")

            card = tk.Frame(popup, bg=self.card, bd=1, relief="solid")
            card.pack(fill="both", expand=True)

            lb = tk.Listbox(
                card, font=self.font_ui,
                bg=self.card, fg=self.text,
                selectbackground=self.accent, selectforeground="white",
                activestyle="none", relief="flat", bd=0, highlightthickness=0,
            )
            lb.pack(fill="both", expand=True, padx=2, pady=2)

            for v in vals:
                lb.insert("end", v)

            try:
                idx = vals.index(var.get())
                lb.selection_set(idx)
                lb.activate(idx)
                lb.see(idx)
            except ValueError:
                pass

            def _pick(_=None):
                sel = lb.curselection()
                if sel:
                    var.set(vals[sel[0]])
                if popup.winfo_exists():
                    popup.destroy()
                _ref[0] = None

            def _blur(_=None):
                _p = popup
                outer.after(80, lambda: _p.destroy() if _p.winfo_exists() else None)
                _ref[0] = None

            lb.bind("<ButtonRelease-1>", _pick)
            lb.bind("<Return>", _pick)
            popup.bind("<FocusOut>", _blur)
            popup.bind("<Escape>", lambda _: popup.destroy() if popup.winfo_exists() else None)
            lb.focus_set()

        disp.config(command=_open)
        arrow.bind("<Button-1>", lambda _: _open())

        if pack_kw:
            outer.pack(**pack_kw)

        outer._var  = var
        outer._vals = vals
        outer.get   = var.get
        outer.set   = var.set

        def _bind_key(seq, func, add=""):
            disp.bind(seq, func, add)
        outer.bind      = _bind_key
        outer.focus_set = disp.focus_set

        return outer

    # ── custom spin widget ────────────────────────────────────────────────────
    def _mk_spin(self, parent, var, values, bg, width=4):
        vals  = list(values)
        frame = tk.Frame(parent, bg=bg)

        def step(delta):
            cur = var.get().strip()
            try:
                idx = vals.index(cur)
            except ValueError:
                idx = 0
            var.set(vals[max(0, min(len(vals) - 1, idx + delta))])

        for text, d in [("−", -1), (None, None), ("＋", 1)]:
            if text is None:
                tk.Entry(
                    frame, textvariable=var, width=width,
                    font=self.font_md, bd=0, relief="flat",
                    highlightthickness=1, highlightcolor=self.accent, highlightbackground=self.border,
                    bg=self.input_bg, fg=self.text, insertbackground=self.text,
                    justify="center",
                ).pack(side="left", padx=1)
            else:
                tk.Button(
                    frame, text=text, command=lambda d=d: step(d),
                    bg=bg, fg=self.accent,
                    bd=0, relief="flat",
                    font=(self.font_md[0], self.font_md[1], "bold"),
                    padx=5, pady=2, cursor="hand2",
                    highlightthickness=0,
                    activebackground=self.strip_bg, activeforeground=self.accent,
                ).pack(side="left")
        return frame

    # ════════════════════════════════════════════════════════════════════════
    # DATE NAVIGATION
    # ════════════════════════════════════════════════════════════════════════

    def _prev_day(self):
        d = date.fromisoformat(self.view_date_key) - timedelta(days=1)
        self._switch_view_date(d.isoformat(), carry_forward=True)

    def _next_day(self):
        d = date.fromisoformat(self.view_date_key) + timedelta(days=1)
        self._switch_view_date(d.isoformat(), carry_forward=True)

    def _goto_today(self):
        self._switch_view_date(self.today_key)

    def _open_cal_picker(self):
        cur = date.fromisoformat(self.view_date_key)
        try:
            from tkcalendar import Calendar
        except ModuleNotFoundError:
            self._open_simple_date_picker(cur)
            return

        top = tk.Toplevel(self.root)
        top.title("選擇日期")
        top.resizable(False, False)
        top.configure(bg=self.bg)
        top.attributes("-topmost", True)
        top.grab_set()
        top.focus_force()
        top.geometry(f"+{self.root.winfo_x() + 20}+{self.root.winfo_y() + 80}")

        cal = Calendar(
            top, selectmode="day",
            year=cur.year, month=cur.month, day=cur.day,
            date_pattern="yyyy-mm-dd",
            background=self.accent, foreground="white",
            headersbackground=self.accent_lt, headersforeground="white",
            selectbackground=self.accent, selectforeground="white",
            normalbackground=self.card, normalforeground=self.text,
            weekendbackground=self.card, weekendforeground=self.accent,
            othermonthbackground=self.strip_bg, othermonthforeground=self.muted,
            borderwidth=0, font=self.font_ui,
        )
        cal.pack(padx=10, pady=(10, 4))

        btn_row = tk.Frame(top, bg=self.bg)
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        def confirm(val=None):
            selected = val or cal.get_date()
            top.destroy()
            if selected != self.view_date_key:
                self._switch_view_date(selected)

        cal.bind("<<CalendarSelected>>", lambda _: confirm())
        self._btn(btn_row, "確定", confirm, self.accent, "white").pack(side="left")
        self._btn(btn_row, "取消", top.destroy, self.bg, self.muted, border=True).pack(side="left", padx=(8, 0))

    def _open_simple_date_picker(self, cur):
        top = tk.Toplevel(self.root)
        top.title("選擇日期")
        top.resizable(False, False)
        top.configure(bg=self.bg)
        top.attributes("-topmost", True)
        top.grab_set()
        top.focus_force()
        top.geometry(f"+{self.root.winfo_x() + 20}+{self.root.winfo_y() + 80}")

        year_var = tk.StringVar(value=str(cur.year))
        month_var = tk.StringVar(value=f"{cur.month:02d}")
        day_var = tk.StringVar(value=f"{cur.day:02d}")

        form = tk.Frame(top, bg=self.bg)
        form.pack(padx=16, pady=(14, 8))

        tk.Label(form, text="年", fg=self.muted, bg=self.bg, font=self.font_sm).pack(anchor="w")
        year_box = tk.Spinbox(
            form, from_=2000, to=2100, textvariable=year_var,
            width=6, font=self.font_ui, justify="center",
        )
        year_box.pack(fill="x", pady=(2, 8))

        tk.Label(form, text="月", fg=self.muted, bg=self.bg, font=self.font_sm).pack(anchor="w")
        month_box = tk.Spinbox(
            form, values=[f"{i:02d}" for i in range(1, 13)], textvariable=month_var,
            width=6, font=self.font_ui, justify="center",
        )
        month_box.pack(fill="x", pady=(2, 8))

        tk.Label(form, text="日", fg=self.muted, bg=self.bg, font=self.font_sm).pack(anchor="w")
        day_box = tk.Spinbox(
            form, from_=1, to=31, textvariable=day_var,
            width=6, font=self.font_ui, justify="center",
        )
        day_box.pack(fill="x", pady=(2, 0))

        def update_day_limit(*_):
            try:
                y = int(year_var.get())
                m = int(month_var.get())
            except ValueError:
                return
            max_day = calendar.monthrange(y, m)[1]
            day_box.config(from_=1, to=max_day)
            try:
                d = int(day_var.get())
                if d > max_day:
                    day_var.set(str(max_day))
            except ValueError:
                day_var.set("1")

        year_var.trace_add("write", update_day_limit)
        month_var.trace_add("write", update_day_limit)
        update_day_limit()

        btn_row = tk.Frame(top, bg=self.bg)
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        def confirm():
            try:
                selected = date(int(year_var.get()), int(month_var.get()), int(day_var.get())).isoformat()
            except ValueError:
                messagebox.showerror("格式錯誤", "請選擇有效日期")
                return
            top.destroy()
            if selected != self.view_date_key:
                self._switch_view_date(selected)

        self._btn(btn_row, "確定", confirm, self.accent, "white").pack(side="left")
        self._btn(btn_row, "取消", top.destroy, self.bg, self.muted, border=True).pack(side="left", padx=(8, 0))

    def _switch_view_date(self, new_key, carry_forward=False):
        self.data["todos_by_date"][self.view_date_key] = self.todos
        old_key = self.view_date_key
        self.view_date_key = new_key
        if carry_forward and (
            new_key not in self.data["todos_by_date"]
            or not self.data["todos_by_date"][new_key]
        ):
            template = self.data["todos_by_date"].get(old_key, [])
            self.data["todos_by_date"][new_key] = [
                {
                    **{k: v for k, v in item.items()
                       if k not in ("done", "note", "auto_logged", "id", "date")},
                    "id":   str(time.time_ns()) + item.get("text", ""),
                    "date": new_key,
                    "done": False,
                    "note": "",
                }
                for item in template
            ]
        elif new_key not in self.data["todos_by_date"]:
            self.data["todos_by_date"][new_key] = []
        self.todos = self.data["todos_by_date"][new_key]
        self.fill_missing_todo_times(self.todos)
        self.save_data()
        if hasattr(self, "nav_date_var"):
            self.nav_date_var.set(new_key)
        self.render_todos()
        self.refresh_stats()
        self.refresh_study_chart()

    # ════════════════════════════════════════════════════════════════════════
    # RENDER — TODOS
    # ════════════════════════════════════════════════════════════════════════

    def render_todos(self):
        for child in self.todo_list_frame.winfo_children():
            child.destroy()

        view_dt  = date.fromisoformat(self.view_date_key)
        is_today = (self.view_date_key == self.today_key)
        wdays    = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]

        if hasattr(self, "nav_date_var"):
            self.nav_date_var.set(self.view_date_key)
        if hasattr(self, "nav_weekday"):
            self.nav_weekday.config(
                text=wdays[view_dt.weekday()],
                fg=self.accent if is_today else self.muted,
            )

        total = len(self.todos)
        done  = sum(1 for t in self.todos if t.get("done"))
        rate  = int((done / total) * 100) if total else 0
        self.today_progress_label.config(
            text=f"完成 {done}/{total}  {rate}%" + ("" if is_today else "  ◄ 歷史"),
            fg=self.muted if not is_today else self.success,
        )
        self.root.after_idle(lambda r=rate: self.draw_progress_bar(r))

        grouped = {}
        for item in self.todos:
            grouped.setdefault(item.get("section", "今日"), []).append(item)

        for section in ["上午", "下午", "晚上", "今日"]:
            items = grouped.get(section)
            if not items:
                continue
            color = SECTION_COLORS.get(section, self.muted)
            hdr = tk.Frame(self.todo_list_frame, bg=self.bg)
            hdr.pack(fill="x", pady=(12, 2))
            tk.Frame(hdr, bg=color, width=3).pack(side="left", fill="y", padx=(0, 8))
            tk.Label(hdr, text=section, fg=color, bg=self.bg,
                     font=(self.font_md[0], self.font_md[1], "bold")).pack(side="left")
            tk.Frame(self.todo_list_frame, bg=self.border, height=1).pack(fill="x", pady=(0, 4))
            for item in items:
                self._render_todo_item(item)

    def _render_todo_item(self, item):
        is_done  = item.get("done", False)
        item_id  = item.get("id", "")
        has_note = bool(item.get("note", "").strip())

        if getattr(self, "_editing_todo_id", None) == item_id:
            self._render_todo_edit_form(item)
            return

        container = tk.Frame(self.todo_list_frame, bg=self.bg)
        container.pack(fill="x", pady=2)

        row = tk.Frame(container, bg=self.bg)
        row.pack(fill="x")

        ts = item.get("time_start", item.get("time", "--"))
        te = item.get("time_end", "")
        time_text = f"{ts}–{te}" if te else ts

        time_tag = tk.Frame(row, bg=self.strip_bg, highlightbackground=self.border, highlightthickness=0)
        time_tag.pack(side="left", padx=(2, 8))
        tk.Label(
            time_tag, text=time_text,
            fg=self.done_fg if is_done else self.muted,
            bg=self.strip_bg, font=self.font_sm, padx=6, pady=3,
        ).pack()

        var = tk.BooleanVar(value=is_done)
        tk.Checkbutton(
            row, text=item.get("text", ""),
            variable=var,
            command=lambda i=item, v=var: self._on_todo_check(i, v),
            bg=self.bg,
            fg=self.done_fg if is_done else self.text,
            selectcolor=self.bg,
            activebackground=self.bg, activeforeground=self.text,
            font=self.font_ui, anchor="w",
            wraplength=220, justify="left", cursor="hand2",
            disabledforeground=self.done_fg,
        ).pack(side="left", fill="x", expand=True)

        act = tk.Frame(row, bg=self.bg)
        act.pack(side="right", padx=(4, 2))
        for sym, fg_col, hover, cmd in [
            ("📝", self.accent if has_note else self.muted, self.accent, lambda i=item: self._begin_note_todo(i)),
            ("✎",  self.muted, self.accent,  lambda i=item: self._begin_edit_todo(i)),
            ("✕",  self.muted, self.warn,    lambda i=item: self._delete_todo(i)),
        ]:
            tk.Button(
                act, text=sym, fg=fg_col, bg=self.bg,
                bd=0, relief="flat", font=self.font_sm,
                padx=4, pady=2, cursor="hand2",
                highlightthickness=0,
                activebackground=self.bg, activeforeground=hover,
                command=cmd,
            ).pack(side="left")

        if getattr(self, "_noting_todo_id", None) == item_id:
            self._render_note_form(item, container)
        elif has_note:
            note_row = tk.Frame(container, bg=self.bg)
            note_row.pack(fill="x", padx=(16, 8), pady=(0, 2))
            tk.Label(note_row, text="📝", fg=self.accent, bg=self.bg, font=self.font_sm).pack(side="left", padx=(0, 4))
            tk.Label(note_row, text=item.get("note", ""),
                     fg=self.muted, bg=self.bg, font=self.font_sm,
                     anchor="w", wraplength=360, justify="left").pack(side="left", fill="x", expand=True)

    def _render_todo_edit_form(self, item):
        form = tk.Frame(self.todo_list_frame, bg=self.strip_bg, bd=1, relief="solid")
        form.pack(fill="x", pady=4, padx=2)

        r1 = tk.Frame(form, bg=self.strip_bg)
        r1.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(r1, text="起", fg=self.muted, bg=self.strip_bg, font=self.font_sm).pack(side="left")

        _ts_raw = item.get("time_start", item.get("time", "08:30"))
        try:
            _tp = datetime.strptime(_ts_raw, "%H:%M")
            _eh = f"{_tp.hour:02d}"
            _em = f"{min((0, 15, 30, 45), key=lambda x: abs(x - _tp.minute)):02d}"
        except ValueError:
            _eh, _em, _ts_raw = "08", "30", "08:30"

        _ts_h = tk.StringVar(value=_eh)
        _ts_m = tk.StringVar(value=_em)
        self._mk_spin(r1, _ts_h, tuple(f"{h:02d}" for h in range(24)), self.strip_bg, width=3).pack(side="left", padx=(4, 0))
        tk.Label(r1, text=":", fg=self.text, bg=self.strip_bg, font=self.font_ui).pack(side="left", padx=1)
        self._mk_spin(r1, _ts_m, ("00", "15", "30", "45"), self.strip_bg, width=3).pack(side="left", padx=(0, 10))

        _init_h = "1.5"
        try:
            _te0 = item.get("time_end", "")
            if _te0:
                _h = (datetime.strptime(_te0, "%H:%M") - datetime.strptime(_ts_raw, "%H:%M")).total_seconds() / 3600
                _h = max(0.5, round(_h * 2) / 2)
                _init_h = str(int(_h)) if _h == int(_h) else str(_h)
        except ValueError:
            pass

        tk.Label(r1, text="時數", fg=self.muted, bg=self.strip_bg, font=self.font_sm).pack(side="left")
        hrs_var = tk.StringVar(value=_init_h)
        self._mk_spin(r1, hrs_var,
                      ("0.5", "1", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5"),
                      self.strip_bg, width=4).pack(side="left", padx=(4, 10))

        def _get_ts():
            try:
                return f"{int(_ts_h.get()):02d}:{int(_ts_m.get()):02d}"
            except ValueError:
                return ""

        def _calc_end():
            try:
                return (datetime.strptime(_get_ts(), "%H:%M") + timedelta(hours=float(hrs_var.get()))).strftime("%H:%M")
            except ValueError:
                return "--:--"

        end_lbl = tk.Label(r1, text=f"→ {_calc_end()}", fg=self.accent, bg=self.strip_bg, font=self.font_sm)
        end_lbl.pack(side="left")

        def _upd(*_):
            end_lbl.config(text=f"→ {_calc_end()}")
        for v in (_ts_h, _ts_m, hrs_var):
            v.trace_add("write", _upd)

        r2 = tk.Frame(form, bg=self.strip_bg)
        r2.pack(fill="x", padx=8, pady=(0, 4))
        tk.Label(r2, text="項目", fg=self.muted, bg=self.strip_bg, font=self.font_sm).pack(side="left")

        _opts = self._get_todo_options()
        _cur  = item.get("text", "")
        txt_entry = self._make_dropdown(r2, _opts, initial=_cur)
        txt_entry.pack(side="left", fill="x", expand=True, padx=(4, 0))

        r3 = tk.Frame(form, bg=self.strip_bg)
        r3.pack(fill="x", padx=8, pady=(0, 8))

        def save_edit():
            ts  = _get_ts()
            txt = txt_entry.get().strip()
            if not txt or not ts:
                return
            try:
                te = (datetime.strptime(ts, "%H:%M") + timedelta(hours=float(hrs_var.get()))).strftime("%H:%M")
            except ValueError:
                messagebox.showerror("格式錯誤", "起始時間請用 24 小時制，例如 08:30")
                return
            item["time_start"] = ts
            item["time_end"]   = te
            item.pop("time", None)
            item["text"] = txt
            self._editing_todo_id = None
            self.save_data()
            self.render_todos()
            self.refresh_study_chart()

        def cancel_edit():
            self._editing_todo_id = None
            self.render_todos()

        txt_entry.bind("<Return>", lambda _: save_edit())
        txt_entry.bind("<Escape>", lambda _: cancel_edit())

        tk.Button(
            r3, text="儲存", command=save_edit,
            bg=self.accent, fg="white",
            bd=0, relief="flat", font=self.font_sm,
            padx=14, pady=5, cursor="hand2",
            highlightthickness=0,
            activebackground=self.accent_lt, activeforeground="white",
        ).pack(side="left")
        tk.Button(
            r3, text="取消", command=cancel_edit,
            bg=self.strip_bg, fg=self.muted,
            bd=1, relief="solid", font=self.font_sm,
            padx=10, pady=5, cursor="hand2",
            highlightthickness=0,
            activebackground=self.border, activeforeground=self.text,
        ).pack(side="left", padx=(8, 0))
        txt_entry.focus_set()

    def _begin_edit_todo(self, item):
        self._editing_todo_id = item.get("id")
        self._noting_todo_id  = None
        self.render_todos()

    def _begin_note_todo(self, item):
        self._noting_todo_id  = item.get("id")
        self._editing_todo_id = None
        self.render_todos()

    def _render_note_form(self, item, container):
        note_row = tk.Frame(container, bg=self.strip_bg)
        note_row.pack(fill="x", padx=2, pady=(2, 2))
        inner = tk.Frame(note_row, bg=self.strip_bg)
        inner.pack(fill="x", padx=8, pady=6)

        tk.Label(inner, text="📝", fg=self.accent, bg=self.strip_bg, font=self.font_sm).pack(side="left", padx=(0, 4))
        note_var   = tk.StringVar(value=item.get("note", ""))
        note_entry = tk.Entry(
            inner, textvariable=note_var,
            font=self.font_sm, bd=0, relief="flat",
            highlightthickness=1, highlightcolor=self.accent, highlightbackground=self.border,
            bg=self.input_bg, fg=self.text, insertbackground=self.text,
        )
        note_entry.pack(side="left", fill="x", expand=True)

        def save_note():
            item["note"] = note_var.get().strip()
            self._noting_todo_id = None
            self.save_data()
            self.render_todos()

        def cancel_note():
            self._noting_todo_id = None
            self.render_todos()

        note_entry.bind("<Return>", lambda _: save_note())
        note_entry.bind("<Escape>", lambda _: cancel_note())

        for sym, fg_c, hover, cmd in [
            ("✔", self.success, self.success, save_note),
            ("✕", self.muted,   self.warn,    cancel_note),
        ]:
            tk.Button(
                inner, text=sym, command=cmd,
                fg=fg_c, bg=self.strip_bg,
                bd=0, relief="flat", font=self.font_sm,
                padx=4, pady=2, cursor="hand2",
                highlightthickness=0,
                activebackground=self.strip_bg, activeforeground=hover,
            ).pack(side="left", padx=(4, 0))
        note_entry.focus_set()

    def _delete_todo(self, item):
        try:
            self.todos.remove(item)
        except ValueError:
            return
        self._editing_todo_id = None
        self.save_data()
        self.render_todos()
        self.refresh_stats()
        self.refresh_study_chart()

    def _infer_section(self, time_start: str) -> str:
        try:
            h = datetime.strptime(time_start, "%H:%M").hour
        except ValueError:
            return "今日"
        if 5  <= h < 12: return "上午"
        if 12 <= h < 18: return "下午"
        return "晚上"

    def _on_todo_check(self, item, var):
        item["done"] = var.get()
        self.save_data()
        self.render_todos()
        self.refresh_stats()
        self.refresh_study_chart()

    def set_todo_state(self, item, done):
        item["done"] = bool(done)
        self.save_data()
        self.refresh_stats()

    def add_custom_todo(self):
        ts   = self.todo_time_start_var.get().strip()
        text = self.todo_combo.get().strip()
        if not text:
            return
        try:
            hours = float(self.todo_hours_var.get())
            te    = (datetime.strptime(ts, "%H:%M") + timedelta(hours=hours)).strftime("%H:%M")
        except ValueError:
            messagebox.showerror("格式錯誤", "起始時間請用 24 小時制，例如 08:30")
            return
        self.todos.append({
            "id":         str(time.time_ns()),
            "section":    self._infer_section(ts),
            "time_start": ts,
            "time_end":   te,
            "text":       text,
            "done":       False,
            "date":       self.view_date_key,
        })
        self.todo_start_h_var.set("08")
        self.todo_start_m_var.set("30")
        self.todo_hours_var.set("1.5")
        self.save_data()
        self.render_todos()
        self.refresh_stats()

    def _update_todo_end_preview(self, *_):
        try:
            ts = self.todo_time_start_var.get().strip()
            h  = float(self.todo_hours_var.get())
            te = (datetime.strptime(ts, "%H:%M") + timedelta(hours=h)).strftime("%H:%M")
            self.todo_end_preview.config(text=f"→ {te}")
        except (ValueError, AttributeError):
            if hasattr(self, "todo_end_preview"):
                self.todo_end_preview.config(text="→ --:--")

    def _get_todo_options(self):
        return list(self.data.get("settings", {}).get("todo_options", DEFAULT_SUBJECTS))

    def open_todo_options_manager(self):
        win = tk.Toplevel(self.root)
        win.title("管理待辦選項")
        win.geometry("280x340")
        win.configure(bg=self.bg)
        win.grab_set()
        win.attributes("-topmost", True)
        win.resizable(False, False)

        tk.Label(win, text="管理待辦選項",
                 fg=self.text, bg=self.bg,
                 font=(self.font_md[0], self.font_md[1], "bold")).pack(pady=(14, 8), padx=16, anchor="w")

        list_frame = tk.Frame(win, bg=self.bg)
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        sb = tk.Scrollbar(list_frame)
        sb.pack(side="right", fill="y")
        listbox = tk.Listbox(
            list_frame, yscrollcommand=sb.set,
            font=self.font_ui, bg=self.card, fg=self.text,
            bd=1, relief="solid", selectmode="single", activestyle="none",
        )
        listbox.pack(side="left", fill="both", expand=True)
        sb.config(command=listbox.yview)
        for opt in self._get_todo_options():
            listbox.insert("end", opt)

        add_row = tk.Frame(win, bg=self.bg)
        add_row.pack(fill="x", padx=16, pady=(0, 6))
        new_var   = tk.StringVar()
        new_entry = tk.Entry(
            add_row, textvariable=new_var,
            font=self.font_ui, bd=0, relief="flat",
            highlightthickness=1, highlightcolor=self.accent, highlightbackground=self.border,
            bg=self.input_bg, fg=self.text, insertbackground=self.text,
        )
        new_entry.pack(side="left", fill="x", expand=True)

        def _persist():
            opts = list(listbox.get(0, "end"))
            self.data["settings"]["todo_options"] = opts
            self.save_data()
            if hasattr(self, "todo_combo"):
                self.todo_combo._vals[:] = opts
            if hasattr(self, "note_subject_combo"):
                self.note_subject_combo._vals[:] = opts
            if hasattr(self, "_filter_subject_dd"):
                self._filter_subject_dd._vals[:] = ["全部科目"] + opts
            self.refresh_study_chart()

        def add_opt():
            val = new_var.get().strip()
            if not val or val in listbox.get(0, "end"):
                return
            listbox.insert("end", val)
            _persist()
            new_var.set("")
            new_entry.focus_set()

        def del_opt():
            sel = listbox.curselection()
            if sel:
                listbox.delete(sel[0])
                _persist()

        new_entry.bind("<Return>", lambda _: add_opt())
        tk.Button(
            add_row, text="新增", command=add_opt,
            bg=self.accent, fg="white",
            bd=0, relief="flat", font=self.font_sm,
            padx=12, pady=4, cursor="hand2",
            highlightthickness=0,
            activebackground=self.accent_lt, activeforeground="white",
        ).pack(side="left", padx=(6, 0))

        btn_row = tk.Frame(win, bg=self.bg)
        btn_row.pack(fill="x", padx=16, pady=(0, 14))
        tk.Button(
            btn_row, text="刪除選取", command=del_opt,
            bg=self.bg, fg=self.warn,
            bd=1, relief="solid", font=self.font_sm,
            padx=10, pady=5, cursor="hand2",
            highlightthickness=0,
            activebackground=self.warn, activeforeground="white",
        ).pack(side="left")
        tk.Button(
            btn_row, text="關閉", command=win.destroy,
            bg=self.bg, fg=self.muted,
            bd=1, relief="solid", font=self.font_sm,
            padx=10, pady=5, cursor="hand2",
            highlightthickness=0,
            activebackground=self.border, activeforeground=self.text,
        ).pack(side="right")

    # ════════════════════════════════════════════════════════════════════════
    # DATA METHODS
    # ════════════════════════════════════════════════════════════════════════

    def get_today_key(self):
        return date.today().isoformat()

    def load_data(self):
        self.data = {
            "settings": {
                "exam_date":    DEFAULT_EXAM_DATE,
                "todo_options": list(DEFAULT_SUBJECTS),
                "title":        "國營企管衝刺管理工具",
                "theme":        "light",
                "ui_scale":     100,
            },
            "todos_by_date": {},
            "notes":         [],
            "study_logs":    [],
        }
        if not os.path.exists(DATA_FILE):
            self.exam_date = DEFAULT_EXAM_DATE
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
        except Exception:
            self.exam_date = DEFAULT_EXAM_DATE
            return

        if "settings"      in loaded: self.data["settings"].update(loaded["settings"])
        if "todos_by_date" in loaded: self.data["todos_by_date"] = loaded["todos_by_date"]
        if "notes"         in loaded: self.data["notes"] = self.normalize_notes(loaded["notes"])
        if "study_logs"    in loaded: self.data["study_logs"] = loaded["study_logs"]
        if "todos"         in loaded: self.migrate_legacy_todos(loaded["todos"])

        self.exam_date = self.data["settings"].get("exam_date", DEFAULT_EXAM_DATE)
        self.ui_scale = self.data["settings"].get("ui_scale", 100)

    def migrate_legacy_todos(self, legacy_todos):
        today     = self.get_today_key()
        converted = []
        for todo in legacy_todos:
            converted.append({
                "id":         str(time.time_ns()),
                "section":    "今日",
                "time_start": todo.get("time", "08:30"),
                "time_end":   "10:00",
                "text":       todo.get("text", ""),
                "done":       bool(todo.get("done", False)),
                "date":       todo.get("date", today),
            })
        if converted:
            self.data["todos_by_date"][today] = converted

    def normalize_notes(self, notes):
        normalized = []
        for note in notes:
            if isinstance(note, dict):
                if "question" not in note and "wrong" in note:
                    note = {**note, "question": note.get("wrong", ""), "answer": note.get("answer", "")}
                normalized.append(note)
                continue
            if isinstance(note, str):
                lines = note.splitlines()
                header = lines[0].strip() if lines else ""
                body   = "\n".join(lines[1:]).strip() if len(lines) > 1 else note.strip()
                normalized.append({
                    "date":     header.rstrip(":") or f"{date.today().month}/{date.today().day}",
                    "subject":  "",
                    "question": body or note.strip(),
                    "answer":   "",
                    "reason":   "",
                })
        return normalized

    def save_data(self):
        exam_val = getattr(self, "exam_date_var", None)
        if exam_val is not None:
            exam_val = exam_val.get().strip() or DEFAULT_EXAM_DATE
        else:
            exam_val = getattr(self, "exam_date", DEFAULT_EXAM_DATE)
        self.data["settings"]["exam_date"] = exam_val
        self.data["settings"]["ui_scale"] = self.data["settings"].get("ui_scale", 100)
        self.data["todos_by_date"][getattr(self, "view_date_key", self.today_key)] = self.todos
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)
        if hasattr(self, "status_label"):
            self.status_label.config(text=f"已儲存 {datetime.now().strftime('%H:%M:%S')}")

    def ensure_today_plan(self):
        self.today_key = self.get_today_key()
        if not hasattr(self, "view_date_key") or self.view_date_key is None:
            self.view_date_key = self.today_key
        if self.today_key not in self.data["todos_by_date"]:
            self.data["todos_by_date"][self.today_key] = []
        if self.view_date_key not in self.data["todos_by_date"]:
            self.data["todos_by_date"][self.view_date_key] = []
        self.todos = self.data["todos_by_date"][self.view_date_key]
        self.fill_missing_todo_times(self.todos)
        if self.view_date_key == self.today_key and not self.todos:
            for item in DEFAULT_PLAN:
                self.todos.append({
                    "id":         str(time.time_ns()) + item["subject"],
                    "section":    item["section"],
                    "time_start": item["time_start"],
                    "time_end":   item["time_end"],
                    "text":       item["subject"],
                    "done":       False,
                    "date":       self.today_key,
                })
            self.save_data()

    def fill_missing_todo_times(self, todos):
        d_start = {i["subject"]: i["time_start"] for i in DEFAULT_PLAN}
        d_end   = {i["subject"]: i["time_end"]   for i in DEFAULT_PLAN}
        s_start = {i["section"]: i["time_start"] for i in DEFAULT_PLAN}
        s_end   = {i["section"]: i["time_end"]   for i in DEFAULT_PLAN}
        changed = False
        for todo in todos:
            subj = todo.get("text", "")
            sect = todo.get("section", "")
            if not todo.get("time_start"):
                todo["time_start"] = todo.pop("time", None) or d_start.get(subj, s_start.get(sect, "08:30"))
                changed = True
            if not todo.get("time_end"):
                todo["time_end"] = d_end.get(subj, s_end.get(sect, "10:00"))
                changed = True
        if changed:
            self.save_data()

    def update_exam_date(self):
        value = self.exam_date_var.get().strip()
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("格式錯誤", "請使用 YYYY-MM-DD 格式，例如 2026-10-18")
            return
        self.exam_date = value
        self.save_data()
        self.refresh_countdown()

    def get_days_left(self):
        try:
            exam_day = datetime.strptime(self.exam_date_var.get().strip() or DEFAULT_EXAM_DATE, "%Y-%m-%d")
        except ValueError:
            exam_day = datetime.strptime(DEFAULT_EXAM_DATE, "%Y-%m-%d")
        return exam_day - datetime.now()

    def format_countdown(self, delta):
        total = max(0, int(delta.total_seconds()))
        days, r  = divmod(total, 86400)
        hours, r = divmod(r, 3600)
        mins, sec = divmod(r, 60)
        return days, f"{hours:02d}:{mins:02d}:{sec:02d}"

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

    def refresh_stats(self):
        total_today = len(self.todos)
        done_today  = sum(1 for t in self.todos if t.get("done"))
        today_rate  = int((done_today / total_today) * 100) if total_today else 0

        week_start   = date.today().toordinal() - 6
        weekly_total = weekly_done = 0
        for todo_date, items in self.data["todos_by_date"].items():
            try:
                if date.fromisoformat(todo_date).toordinal() < week_start:
                    continue
            except ValueError:
                continue
            weekly_total += len(items)
            weekly_done  += sum(1 for t in items if t.get("done"))

        weekly_rate = int((weekly_done / weekly_total) * 100) if weekly_total else 0
        cum_days    = self.get_study_days()

        self.stat_today.config(text=f"{today_rate}%")
        self.stat_week.config(text=f"{weekly_rate}%")
        self.stat_days.config(text=f"{cum_days} 天")
        self.stats_detail.config(
            text=f"今日完成：{done_today}/{total_today}　本週：{weekly_done}/{weekly_total}")
        self.refresh_stats_detail()

    def get_study_days(self):
        return sum(
            1 for items in self.data["todos_by_date"].values()
            if any(t.get("done") for t in items)
        )

    def refresh_stats_detail(self):
        if not hasattr(self, "detail_items_frame"):
            return
        for child in self.detail_items_frame.winfo_children():
            child.destroy()

        all_dates = sorted(
            (k for k, v in self.data["todos_by_date"].items() if v), reverse=True)

        if not all_dates:
            tk.Label(self.detail_items_frame, text="（尚無任何待辦記錄）",
                     fg=self.muted, bg=self.card, font=self.font_sm).pack(pady=12)
            self.detail_summary_lbl.config(text="")
            self.detail_date_lbl.config(text="全部日期")
            return

        wdays   = ["一", "二", "三", "四", "五", "六", "日"]
        total_h = done_h = 0.0
        total_n = done_n = 0

        for date_key in all_dates:
            items = self.data["todos_by_date"].get(date_key, [])
            try:
                d        = date.fromisoformat(date_key)
                is_today = (date_key == self.today_key)
                dlabel   = f"{d.year}/{d.month:02d}/{d.day:02d}（週{wdays[d.weekday()]}）"
                if is_today:
                    dlabel += "  ◀ 今日"
            except ValueError:
                dlabel   = date_key
                is_today = False

            date_hdr = tk.Frame(self.detail_items_frame, bg=self.strip_bg)
            date_hdr.pack(fill="x", pady=(4, 0))
            tk.Label(
                date_hdr, text=dlabel,
                fg=self.accent if is_today else self.muted,
                bg=self.strip_bg,
                font=(self.font_sm[0], self.font_sm[1], "bold"),
                padx=8, pady=4,
            ).pack(side="left")

            for item in items:
                is_done = item.get("done", False)
                ts, te  = item.get("time_start", ""), item.get("time_end", "")
                note    = item.get("note", "").strip()
                hours   = 0.0
                if ts and te:
                    try:
                        hours = max(0.0, (
                            datetime.strptime(te, "%H:%M") - datetime.strptime(ts, "%H:%M")
                        ).total_seconds() / 3600)
                    except ValueError:
                        pass
                total_h += hours
                total_n += 1
                if is_done:
                    done_h += hours
                    done_n += 1

                row = tk.Frame(self.detail_items_frame, bg=self.card)
                row.pack(fill="x", padx=8, pady=(2, 0))
                tk.Label(row,
                         text="✓" if is_done else "◦",
                         fg=self.success if is_done else self.done_fg,
                         bg=self.card,
                         font=(self.font_sm[0], self.font_sm[1], "bold"), width=2).pack(side="left")
                tk.Label(row,
                         text=f"{ts}–{te}" if ts and te else "―",
                         fg=self.muted if not is_done else self.done_fg,
                         bg=self.card, font=self.font_sm, width=13, anchor="w").pack(side="left", padx=(2, 6))
                tk.Label(row, text=item.get("text", ""),
                         fg=self.done_fg if is_done else self.text,
                         bg=self.card, font=self.font_ui, anchor="w").pack(side="left", fill="x", expand=True)
                if hours > 0:
                    tk.Label(row, text=f"{hours:.1f}h",
                             fg=self.success if is_done else self.muted,
                             bg=self.card, font=self.font_sm, width=5, anchor="e").pack(side="right", padx=(0, 6))
                if note:
                    nr = tk.Frame(self.detail_items_frame, bg=self.card)
                    nr.pack(fill="x", padx=(28, 12), pady=(0, 2))
                    tk.Label(nr, text=note, fg=self.muted, bg=self.card,
                             font=self.font_sm, anchor="w", wraplength=340, justify="left").pack(side="left")

        tk.Frame(self.detail_items_frame, bg=self.border, height=1).pack(fill="x", padx=8, pady=(6, 0))
        parts = []
        if total_h > 0: parts.append(f"完成 {done_h:.1f}h / 共 {total_h:.1f}h")
        if total_n > 0: parts.append(f"事項 {done_n}/{total_n}")
        parts.append(f"共 {len(all_dates)} 天有記錄")
        self.detail_summary_lbl.config(text="   ".join(parts))
        self.detail_date_lbl.config(text=f"全部記錄 ({len(all_dates)} 日)")

        if hasattr(self, "detail_canvas"):
            self.detail_canvas.update_idletasks()
            self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox("all"))

    def add_note(self):
        subject  = self.note_subject_combo.get().strip()
        question = self.note_question_var.get().strip()
        answer   = self.note_answer_var.get().strip()
        reason   = self.note_reason_var.get().strip()
        if not subject or not question or not answer:
            messagebox.showerror("欄位不足", "請至少填入科目、題目、答案")
            return
        self.data["notes"].insert(0, {
            "date":     f"{date.today().month}/{date.today().day}",
            "subject":  subject,
            "question": question,
            "answer":   answer,
            "reason":   reason,
        })
        self.note_question_var.set("")
        self.note_answer_var.set("")
        self.note_reason_var.set("")
        self.save_data()
        self.refresh_notes()

    def clear_notes(self):
        if messagebox.askyesno("確認", "確定要清除所有錯題紀錄？"):
            self.data["notes"] = []
            self.save_data()
            self.refresh_notes()

    def refresh_notes(self, notes=None):
        if notes is None:
            notes = self.data["notes"]
        for child in self.note_cards_frame.winfo_children():
            child.destroy()
        self.note_count_label.config(text=f"{len(self.data['notes'])} 筆")
        valid = [n for n in notes if isinstance(n, dict)]
        if not valid:
            tk.Label(self.note_cards_frame,
                     text="（尚無符合的錯題紀錄）",
                     fg=self.muted, bg=self.bg, font=self.font_sm).pack(pady=24)
        else:
            for note in valid:
                self._render_note_card(note)
            tk.Frame(self.note_cards_frame, bg=self.bg, height=8).pack(fill="x")
        self.note_canvas.update_idletasks()
        self.note_canvas.configure(scrollregion=self.note_canvas.bbox("all"))

    def _render_note_card(self, note):
        card = tk.Frame(self.note_cards_frame, bg=self.card, bd=1, relief="solid")
        card.pack(fill="x", padx=10, pady=(8, 0))

        def on_scroll(e):
            self.note_canvas.yview_scroll(-1 * (e.delta // 120), "units")

        subject = note.get("subject", "")
        sbg     = self._subject_badge_color(subject)

        hdr = tk.Frame(card, bg=sbg if subject else self.strip_bg)
        hdr.pack(fill="x")
        hdr.bind("<MouseWheel>", on_scroll)

        if subject:
            slbl = tk.Label(hdr, text=f"  {subject}  ",
                            fg="white", bg=sbg, font=self.font_sm, pady=6)
            slbl.pack(side="left")
            slbl.bind("<MouseWheel>", on_scroll)

        dlbl = tk.Label(hdr, text=note.get("date", "--"),
                        fg="white" if subject else self.muted,
                        bg=sbg if subject else self.strip_bg,
                        font=self.font_sm, padx=8, pady=6)
        dlbl.pack(side="left")
        dlbl.bind("<MouseWheel>", on_scroll)

        del_btn = tk.Button(
            hdr, text="✕",
            fg="white" if subject else self.warn,
            bg=sbg if subject else self.strip_bg,
            bd=0, relief="flat", font=self.font_sm,
            padx=8, pady=6, cursor="hand2",
            command=lambda n=note: self.delete_note(n),
            activebackground=self.warn, activeforeground="white",
        )
        del_btn.pack(side="right")
        del_btn.bind("<MouseWheel>", on_scroll)

        body = tk.Frame(card, bg=self.card)
        body.pack(fill="x", padx=10, pady=(8, 10))
        body.bind("<MouseWheel>", on_scroll)

        question = note.get("question", note.get("wrong", ""))
        answer   = note.get("answer", "")
        reason   = note.get("reason", "")

        self._card_field(body, "Q", question, self.text,    bold=True, scroll_fn=on_scroll)
        self._card_field(body, "A", answer,   "#166534",    scroll_fn=on_scroll)
        if reason:
            self._card_field(body, "原", reason, self.muted, scroll_fn=on_scroll)

    def _card_field(self, parent, prefix, content, fg, bold=False, scroll_fn=None):
        row   = tk.Frame(parent, bg=self.card)
        row.pack(fill="x", pady=1)
        p_font = (self.font_sm[0], self.font_sm[1], "bold")
        c_font = (self.font_sm[0], self.font_sm[1], "bold") if bold else self.font_sm
        pfx = tk.Label(row, text=prefix, fg=self.accent, bg=self.card,
                       font=p_font, width=2, anchor="nw")
        pfx.pack(side="left", anchor="nw", pady=(1, 0))
        txt = tk.Label(row, text=content, fg=fg, bg=self.card,
                       font=c_font, anchor="w", wraplength=400, justify="left")
        txt.pack(side="left", fill="x", expand=True)
        if scroll_fn:
            for w in (row, pfx, txt):
                w.bind("<MouseWheel>", scroll_fn)

    def _subject_badge_color(self, subject):
        return {
            "企業管理": "#6366f1",
            "經濟學":   "#3b82f6",
            "法學":     "#8b5cf6",
            "國英":     "#22c55e",
            "歷屆題":   "#f59e0b",
        }.get(subject, self.muted)

    def switch_notes_mode(self, mode):
        self.notes_mode = mode
        if mode == "add":
            self.notes_search_frame.pack_forget()
            self.notes_add_frame.pack(fill="both", expand=True)
            self.note_add_btn.config(
                bg=self.card, fg=self.accent,
                font=(self.font_sm[0], self.font_sm[1], "bold"))
            self.note_search_btn.config(bg=self.card, fg=self.muted, font=self.font_sm)
        else:
            self.notes_add_frame.pack_forget()
            self.notes_search_frame.pack(fill="both", expand=True)
            self.note_search_btn.config(
                bg=self.card, fg=self.accent,
                font=(self.font_sm[0], self.font_sm[1], "bold"))
            self.note_add_btn.config(bg=self.card, fg=self.muted, font=self.font_sm)

    def search_notes(self):
        keyword        = self.note_search_var.get().strip().lower()
        subject_filter = self._filter_subject_dd.get()
        period_filter  = self._filter_period_dd.get()
        today          = date.today()
        results        = []
        for note in self.data["notes"]:
            if not isinstance(note, dict):
                continue
            if subject_filter != "全部科目" and note.get("subject") != subject_filter:
                continue
            if period_filter != "全部":
                note_date_str = note.get("date", "")
                try:
                    month, day = map(int, note_date_str.split("/"))
                    note_dt    = date(today.year, month, day)
                    if period_filter == "今天" and note_dt != today:
                        continue
                    elif period_filter == "本週":
                        if note_dt < today - timedelta(days=today.weekday()):
                            continue
                    elif period_filter == "本月" and note_dt.month != today.month:
                        continue
                except (ValueError, AttributeError):
                    pass
            if keyword:
                haystack = " ".join([
                    note.get("subject", ""),
                    note.get("question", note.get("wrong", "")),
                    note.get("answer", ""),
                    note.get("reason", ""),
                ]).lower()
                if keyword not in haystack:
                    continue
            results.append(note)
        self.note_result_label.config(text=f"找到 {len(results)} 筆")
        self.refresh_notes(results)

    def clear_note_search(self):
        self.note_search_var.set("")
        self._filter_subject_dd.set("全部科目")
        self._filter_period_dd.set("全部")
        self.note_result_label.config(text="")
        self.refresh_notes()

    def delete_note(self, note):
        try:
            self.data["notes"].remove(note)
        except ValueError:
            return
        self.save_data()
        if getattr(self, "notes_mode", "add") == "search":
            self.search_notes()
        else:
            self.refresh_notes()

    def refresh_study_chart(self):
        if not hasattr(self, "study_chart_canvas"):
            return
        canvas = self.study_chart_canvas
        totals = {}
        for items in self.data["todos_by_date"].values():
            for item in items:
                if not item.get("done"):
                    continue
                ts = item.get("time_start", item.get("time", ""))
                te = item.get("time_end", "")
                if not ts or not te:
                    continue
                try:
                    hours = (datetime.strptime(te, "%H:%M") - datetime.strptime(ts, "%H:%M")).total_seconds() / 3600
                    if hours <= 0:
                        continue
                except ValueError:
                    continue
                subj = item.get("text", "")
                opts = self._get_todo_options()
                if subj not in opts:
                    subj = next((s for s in opts if s in subj), subj)
                totals[subj] = totals.get(subj, 0.0) + hours

        canvas.delete("all")
        opts = self._get_todo_options()
        w    = canvas.winfo_width()
        if w < 60:
            return

        if not totals:
            canvas.create_text(w // 2, 40,
                               text="尚無讀書記錄（完成待辦後自動計算）",
                               fill=self.muted, font=self.font_sm, anchor="center")
            canvas.configure(height=80)
            return

        label_w = 72
        hours_w = 56
        bar_x0  = label_w + 6
        bar_x1  = w - hours_w - 8
        row_h   = 36
        pad_top = 14
        bar_h   = 14
        max_hrs = max(totals.values()) or 1
        total_h = sum(totals.values())

        for i, subj in enumerate(opts):
            hours   = totals.get(subj, 0.0)
            y_mid   = pad_top + i * row_h + row_h // 2
            y_top   = y_mid - bar_h // 2
            y_bot   = y_mid + bar_h // 2
            color   = self._subject_badge_color(subj)
            has_val = hours > 0

            canvas.create_text(label_w, y_mid, text=subj, anchor="e",
                               fill=self.text if has_val else self.muted,
                               font=(self.font_sm[0], self.font_sm[1], "bold" if has_val else ""))
            canvas.create_rectangle(bar_x0, y_top, bar_x1, y_bot, fill=self.strip_bg, outline="")

            if has_val:
                bw = max(6, int((hours / max_hrs) * (bar_x1 - bar_x0)))
                canvas.create_rectangle(bar_x0, y_top, bar_x0 + bw, y_bot, fill=color, outline="")
                if bw > 28:
                    canvas.create_text(bar_x0 + bw - 4, y_mid,
                                       text=f"{hours:.1f}h", anchor="e",
                                       fill="white",
                                       font=(self.font_sm[0], self.font_sm[1], "bold"))

            canvas.create_text(bar_x1 + 8, y_mid,
                               text=f"{hours:.1f} h", anchor="w",
                               fill=color if has_val else self.muted,
                               font=(self.font_sm[0], self.font_sm[1], "bold" if has_val else ""))

        y_sep = pad_top + len(opts) * row_h + 4
        canvas.create_line(bar_x0, y_sep, bar_x1, y_sep, fill=self.border)
        canvas.create_text(bar_x0, y_sep + 14,
                           text=f"共讀 {total_h:.1f} 小時", anchor="w",
                           fill=self.accent, font=(self.font_md[0], self.font_md[1], "bold"))
        canvas.create_text(bar_x1, y_sep + 14,
                           text=f"{self.get_study_days()} 天有記錄", anchor="e",
                           fill=self.muted, font=self.font_sm)
        canvas.configure(height=y_sep + 34)

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


if __name__ == "__main__":
    root = tk.Tk()
    app  = ExamPrepApp(root)
    root.mainloop()
