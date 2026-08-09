"""Todo tab — ported from app/tab_todo.py TodoTabMixin."""
from datetime import date, datetime, timedelta

import flet as ft

import config, theme

HOURS = [f"{h:02d}" for h in range(24)]
MINUTES = ["00", "15", "30", "45"]
DURATIONS = ["0.5", "1", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5"]
WEEKDAYS = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]


def _opts(values):
    return [ft.DropdownOption(key=v, text=v) for v in values]


class TodoTabMixin:
    def build_tab_todo(self):
        pal = self.palette
        self.editing_todo_id = None
        self.noting_todo_id = None

        self.nav_date_btn_text = ft.Text(self.store.view_date_key, size=14)
        self.nav_weekday_text = ft.Text("", size=13, weight=ft.FontWeight.BOLD, color=pal["muted"])
        self.todo_progress_label = ft.Text("", size=12, color=pal["success"])
        self.todo_progress_bar = ft.ProgressBar(value=0, color=pal["accent"], bgcolor=pal["border"], height=3)

        nav_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=6, controls=[
                    ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=self._on_prev_day),
                    ft.OutlinedButton(content=ft.Row(spacing=6, controls=[
                        ft.Icon(ft.Icons.CALENDAR_MONTH, size=16),
                        self.nav_date_btn_text,
                    ]), on_click=self._on_open_date_picker),
                    self.nav_weekday_text,
                    ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=self._on_next_day),
                    ft.TextButton("今日", on_click=self._on_goto_today),
                ]),
                self.todo_progress_label,
            ],
        )

        self.todo_list_view = ft.ListView(expand=True, spacing=2, padding=ft.Padding.symmetric(horizontal=16))

        self.add_start_h = ft.Dropdown(value="08", options=_opts(HOURS), width=100, dense=True,
                                        content_padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                                        on_select=self._on_add_time_change)
        self.add_start_m = ft.Dropdown(value="30", options=_opts(MINUTES), width=100, dense=True,
                                        content_padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                                        on_select=self._on_add_time_change)
        self.add_hours = ft.Dropdown(value="1.5", options=_opts(DURATIONS), width=100, dense=True,
                                      content_padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                                      on_select=self._on_add_time_change)
        self.add_end_preview = ft.Text("→ 10:00", size=12, color=pal["accent"])
        self.add_subject = ft.Dropdown(value=(self.store.get_todo_options() or [""])[0],
                                        options=_opts(self.store.get_todo_options()), expand=True, dense=True)

        add_strip = ft.Container(
            bgcolor=pal["card"],
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            border=ft.Border(top=ft.BorderSide(1, pal["border"])),
            content=ft.Column(spacing=8, controls=[
                ft.Row(spacing=6, wrap=True, controls=[
                    ft.Text("開始", size=12, color=pal["muted"]),
                    self.add_start_h, ft.Text(":"), self.add_start_m,
                    ft.Text("時數", size=12, color=pal["muted"]), self.add_hours,
                    self.add_end_preview,
                ]),
                ft.Row(spacing=6, controls=[
                    ft.Text("項目", size=12, color=pal["muted"]),
                    self.add_subject,
                    ft.IconButton(ft.Icons.SETTINGS, icon_size=16, tooltip="管理待辦選項",
                                  on_click=self._on_open_todo_options),
                    ft.Button("新增", bgcolor=pal["accent"], color="white", on_click=self._on_add_custom_todo),
                ]),
            ]),
        )

        self.tab_frames["todo"] = ft.Column(
            expand=True, spacing=0,
            controls=[
                ft.Container(padding=ft.Padding.only(left=16, top=14, right=16, bottom=6), content=nav_row),
                ft.Container(padding=ft.Padding.symmetric(horizontal=16), content=self.todo_progress_bar),
                self.todo_list_view,
                add_strip,
            ],
        )

    # ── date navigation ──────────────────────────────────────────────────────
    async def _on_prev_day(self, e):
        d = date.fromisoformat(self.store.view_date_key) - timedelta(days=1)
        await self.store.switch_view_date(d.isoformat(), carry_forward=True)
        self.render_todos()
        self.refresh_stats()

    async def _on_next_day(self, e):
        d = date.fromisoformat(self.store.view_date_key) + timedelta(days=1)
        await self.store.switch_view_date(d.isoformat(), carry_forward=True)
        self.render_todos()
        self.refresh_stats()

    async def _on_goto_today(self, e):
        await self.store.switch_view_date(self.store.today_key)
        self.render_todos()
        self.refresh_stats()

    async def _on_open_date_picker(self, e):
        cur = date.fromisoformat(self.store.view_date_key)

        async def on_change(e):
            picked = dp.value
            if picked is None:
                return
            new_key = picked.date().isoformat() if hasattr(picked, "date") else picked.isoformat()
            if new_key != self.store.view_date_key:
                await self.store.switch_view_date(new_key)
                self.render_todos()
                self.refresh_stats()

        dp = ft.DatePicker(value=cur, on_change=on_change)
        self.page.show_dialog(dp)

    # ── render ───────────────────────────────────────────────────────────────
    def render_todos(self):
        view_dt = date.fromisoformat(self.store.view_date_key)
        is_today = self.store.view_date_key == self.store.today_key
        self.nav_date_btn_text.value = self.store.view_date_key
        self.nav_weekday_text.value = WEEKDAYS[view_dt.weekday()]
        self.nav_weekday_text.color = self.palette["accent"] if is_today else self.palette["muted"]

        todos = self.store.todos
        total = len(todos)
        done = sum(1 for t in todos if t.get("done"))
        rate = (done / total) if total else 0
        self.todo_progress_label.value = f"完成 {done}/{total}  {int(rate * 100)}%" + ("" if is_today else "  ◄ 歷史")
        self.todo_progress_bar.value = rate

        grouped = {}
        for item in todos:
            grouped.setdefault(item.get("section", "今日"), []).append(item)

        controls = []
        for section in config.SECTIONS:
            items = grouped.get(section)
            if not items:
                continue
            color = config.SECTION_COLORS.get(section, self.palette["muted"])
            controls.append(ft.Container(
                padding=ft.Padding.only(left=0, top=10, right=0, bottom=4),
                content=ft.Row(spacing=8, controls=[
                    ft.Container(width=3, height=16, bgcolor=color),
                    ft.Text(section, size=14, weight=ft.FontWeight.BOLD, color=color),
                ]),
            ))
            for item in items:
                controls.append(self._build_todo_item(item))

        self.todo_list_view.controls = controls
        self.todo_list_view.update()
        self.todo_progress_label.update()
        self.todo_progress_bar.update()
        self.nav_date_btn_text.update()
        self.nav_weekday_text.update()

    def _build_todo_item(self, item):
        if self.editing_todo_id == item.get("id"):
            return self._build_todo_edit_form(item)

        pal = self.palette
        is_done = item.get("done", False)
        ts = item.get("time_start", "--")
        te = item.get("time_end", "")
        time_text = f"{ts}–{te}" if te else ts
        has_note = bool(item.get("note", "").strip())

        row = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    bgcolor=pal["strip_bg"],
                    padding=ft.Padding.symmetric(horizontal=6, vertical=3),
                    content=ft.Text(time_text, size=12, color=pal["done_fg"] if is_done else pal["muted"]),
                ),
                ft.Checkbox(
                    label=item.get("text", ""), value=is_done,
                    label_style=ft.TextStyle(color=pal["done_fg"] if is_done else pal["text"]),
                    on_change=lambda e, i=item: self.page.run_task(self._on_todo_check, i, e.control.value),
                ),
                ft.Container(expand=True),
                ft.IconButton(ft.Icons.EDIT_NOTE, icon_size=16,
                              icon_color=pal["accent"] if has_note else pal["muted"],
                              on_click=lambda e, i=item: self._begin_note_todo(i)),
                ft.IconButton(ft.Icons.EDIT, icon_size=16, icon_color=pal["muted"],
                              on_click=lambda e, i=item: self._begin_edit_todo(i)),
                ft.IconButton(ft.Icons.CLOSE, icon_size=16, icon_color=pal["muted"],
                              on_click=lambda e, i=item: self.page.run_task(self._on_delete_todo, i)),
            ],
        )

        col_children = [row]
        if self.noting_todo_id == item.get("id"):
            col_children.append(self._build_note_form(item))
        elif has_note:
            col_children.append(ft.Container(
                padding=ft.Padding.only(left=16, top=0, right=8, bottom=2),
                content=ft.Row(spacing=4, controls=[
                    ft.Icon(ft.Icons.EDIT_NOTE, size=14, color=pal["accent"]),
                    ft.Text(item.get("note", ""), size=12, color=pal["muted"], expand=True),
                ]),
            ))
        return ft.Column(spacing=0, controls=col_children)

    def _build_todo_edit_form(self, item):
        pal = self.palette
        ts_raw = item.get("time_start", "08:30")
        try:
            tp = datetime.strptime(ts_raw, "%H:%M")
            init_h, init_m = f"{tp.hour:02d}", min(MINUTES, key=lambda x: abs(int(x) - tp.minute))
        except ValueError:
            init_h, init_m, ts_raw = "08", "30", "08:30"

        init_hours = "1.5"
        try:
            te0 = item.get("time_end", "")
            if te0:
                h = (datetime.strptime(te0, "%H:%M") - datetime.strptime(ts_raw, "%H:%M")).total_seconds() / 3600
                h = max(0.5, round(h * 2) / 2)
                init_hours = str(int(h)) if h == int(h) else str(h)
        except ValueError:
            pass

        pad = ft.Padding.symmetric(horizontal=10, vertical=8)
        h_dd = ft.Dropdown(value=init_h, options=_opts(HOURS), width=100, dense=True, content_padding=pad)
        m_dd = ft.Dropdown(value=init_m, options=_opts(MINUTES), width=100, dense=True, content_padding=pad)
        hrs_dd = ft.Dropdown(value=init_hours, options=_opts(DURATIONS), width=100, dense=True, content_padding=pad)
        subj_dd = ft.Dropdown(value=item.get("text", ""), options=_opts(self.store.get_todo_options()), expand=True, dense=True)

        async def save_edit(e):
            try:
                ts = f"{int(h_dd.value):02d}:{int(m_dd.value):02d}"
                te = (datetime.strptime(ts, "%H:%M") + timedelta(hours=float(hrs_dd.value))).strftime("%H:%M")
            except (TypeError, ValueError):
                return
            item["time_start"], item["time_end"] = ts, te
            item["text"] = subj_dd.value
            self.editing_todo_id = None
            await self.store.save()
            self.render_todos()

        async def cancel_edit(e):
            self.editing_todo_id = None
            self.render_todos()

        return ft.Container(
            bgcolor=pal["strip_bg"], border=ft.Border.all(1, pal["border"]),
            padding=ft.Padding.symmetric(horizontal=8, vertical=8),
            margin=ft.Margin.symmetric(vertical=4),
            content=ft.Column(spacing=6, controls=[
                ft.Row(spacing=6, wrap=True, controls=[
                    ft.Text("起", size=12, color=pal["muted"]), h_dd, ft.Text(":"), m_dd,
                    ft.Text("時數", size=12, color=pal["muted"]), hrs_dd,
                ]),
                ft.Row(spacing=6, controls=[ft.Text("項目", size=12, color=pal["muted"]), subj_dd]),
                ft.Row(spacing=8, controls=[
                    ft.Button("儲存", bgcolor=pal["accent"], color="white", on_click=save_edit),
                    ft.OutlinedButton("取消", on_click=cancel_edit),
                ]),
            ]),
        )

    def _build_note_form(self, item):
        pal = self.palette
        note_field = ft.TextField(value=item.get("note", ""), text_size=12, dense=True,
                                   content_padding=ft.Padding.symmetric(horizontal=8, vertical=6))

        async def save_note(e):
            item["note"] = (note_field.value or "").strip()
            self.noting_todo_id = None
            await self.store.save()
            self.render_todos()

        async def cancel_note(e):
            self.noting_todo_id = None
            self.render_todos()

        return ft.Container(
            bgcolor=pal["strip_bg"], padding=ft.Padding.only(left=16, top=4, right=8, bottom=4),
            content=ft.Row(controls=[
                ft.Icon(ft.Icons.EDIT_NOTE, size=14, color=pal["accent"]),
                ft.Container(content=note_field, expand=True),
                ft.IconButton(ft.Icons.CHECK, icon_size=16, icon_color=pal["success"], on_click=save_note),
                ft.IconButton(ft.Icons.CLOSE, icon_size=16, icon_color=pal["muted"], on_click=cancel_note),
            ]),
        )

    def _begin_edit_todo(self, item):
        self.editing_todo_id = item.get("id")
        self.noting_todo_id = None
        self.render_todos()

    def _begin_note_todo(self, item):
        self.noting_todo_id = item.get("id")
        self.editing_todo_id = None
        self.render_todos()

    # ── actions ──────────────────────────────────────────────────────────────
    async def _on_todo_check(self, item, value):
        item["done"] = bool(value)
        await self.store.save()
        self.render_todos()
        self.refresh_stats()

    async def _on_delete_todo(self, item):
        date_key = self.store.view_date_key
        todos_list = self.store.todos
        idx = self.store.pop_todo_with_index(item, todos_list)
        if idx is None:
            return
        self.editing_todo_id = None
        await self.store.save()
        self.render_todos()
        self.refresh_stats()

        async def undo(e=None):
            self.store.restore_todo_at(idx, item, todos_list)
            await self.store.save()
            if self.store.view_date_key == date_key:
                self.render_todos()
            self.refresh_stats()

        self.page.show_dialog(ft.SnackBar(
            content=ft.Text(f"已刪除「{item.get('text', '待辦事項')}」"),
            action="復原", on_action=undo, duration=5000,
        ))

    def _on_add_time_change(self, e):
        try:
            ts = f"{self.add_start_h.value}:{self.add_start_m.value}"
            te = (datetime.strptime(ts, "%H:%M") + timedelta(hours=float(self.add_hours.value))).strftime("%H:%M")
            self.add_end_preview.value = f"→ {te}"
        except (TypeError, ValueError):
            self.add_end_preview.value = "→ --:--"
        self.add_end_preview.update()

    async def _on_add_custom_todo(self, e):
        text = (self.add_subject.value or "").strip()
        if not text:
            return
        ts = f"{self.add_start_h.value}:{self.add_start_m.value}"
        try:
            te = (datetime.strptime(ts, "%H:%M") + timedelta(hours=float(self.add_hours.value))).strftime("%H:%M")
        except (TypeError, ValueError):
            return
        import time as _time
        self.store.todos.append({
            "id": str(_time.time_ns()),
            "section": self.store.infer_section(ts),
            "time_start": ts, "time_end": te,
            "text": text, "done": False, "date": self.store.view_date_key,
        })
        await self.store.save()
        self.render_todos()
        self.refresh_stats()

    # ── manage todo options ─────────────────────────────────────────────────
    async def _on_open_todo_options(self, e):
        pal = self.palette
        opts_list = ft.ListView(height=200, spacing=2)
        new_field = ft.TextField(hint_text="新增選項", expand=True, dense=True)

        def rebuild_list():
            opts_list.controls = [
                ft.Row(controls=[
                    ft.Text(o, expand=True),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color=pal["warn"],
                                  on_click=lambda e, o=o: self.page.run_task(remove_opt, o)),
                ]) for o in self.store.get_todo_options()
            ]

        async def persist():
            await self.store.save()
            self.refresh_option_dependents()
            rebuild_list()
            opts_list.update()

        async def add_opt(e=None):
            val = (new_field.value or "").strip()
            if not val or val in self.store.get_todo_options():
                return
            self.store.data["settings"]["todo_options"].append(val)
            new_field.value = ""
            new_field.update()
            await persist()

        async def remove_opt(val):
            opts = self.store.data["settings"]["todo_options"]
            if val in opts:
                opts.remove(val)
            await persist()

        rebuild_list()
        new_field.on_submit = add_opt
        dlg = ft.AlertDialog(
            modal=True, title=ft.Text("管理待辦選項"),
            content=ft.Container(width=280, content=ft.Column(controls=[
                opts_list,
                ft.Row(controls=[new_field, ft.IconButton(ft.Icons.ADD, on_click=add_opt)]),
            ])),
            actions=[ft.TextButton("關閉", on_click=lambda e: self.page.pop_dialog())],
        )
        self.page.show_dialog(dlg)
