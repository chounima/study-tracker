import calendar
import time
import tkinter as tk
from datetime import datetime, date, timedelta
from tkinter import messagebox

from .config import DEFAULT_SUBJECTS, SECTION_COLORS


class TodoTabMixin:
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
