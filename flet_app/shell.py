"""App shell: header, countdown strip, tab bar, settings/title dialogs.
Ported from the Tkinter app's app/shell.py ShellMixin — same responsibilities,
rebuilt with Flet controls. No frameless/topmost/drag-window behaviour (that
was Windows-desktop-only and doesn't exist on mobile/web); this uses a
standard OS/browser window instead, per the agreed conversion scope.
"""
import asyncio

import flet as ft

import config, theme


class ShellMixin:
    async def init_shell(self):
        p = self.page
        pal = theme.get_palette(self.store.data["settings"].get("theme", "light"))
        self.palette = pal

        p.title = self.store.data["settings"].get("title", config.DEFAULT_TITLE)
        p.padding = 0
        p.bgcolor = pal["bg"]
        p.theme_mode = ft.ThemeMode.LIGHT
        p.window.width = 480
        p.window.height = 860
        p.window.min_width = 360
        p.window.min_height = 560

        self.active_tab = "todo"
        self.body_container = ft.Container(expand=True)

        self.title_text = ft.Text(p.title, color="#f8fafc", size=18, weight=ft.FontWeight.W_600)
        self.status_text = ft.Text("", color="#94a3b8", size=12)

        self.theme_dots = ft.Row(spacing=4)
        self._build_theme_dots()

        header = ft.Container(
            bgcolor=pal["titlebar_bg"],
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            self.title_text,
                            ft.IconButton(ft.Icons.EDIT, icon_size=16, icon_color="#94a3b8",
                                          tooltip="修改標題", on_click=self._on_edit_title),
                            self.status_text,
                        ],
                    ),
                    ft.Row(
                        spacing=6,
                        controls=[
                            self.theme_dots,
                            ft.IconButton(ft.Icons.SAVE_OUTLINED, icon_size=18, icon_color="#94a3b8",
                                          tooltip="儲存", on_click=self._on_manual_save),
                            ft.IconButton(ft.Icons.SETTINGS_OUTLINED, icon_size=18, icon_color="#94a3b8",
                                          tooltip="顯示設定", on_click=self._on_open_display_settings),
                        ],
                    ),
                ],
            ),
        )

        self.countdown_text = ft.Text("--", size=28, color=pal["accent"], weight=ft.FontWeight.BOLD)
        self.countdown_meta = ft.Text("", size=12, color=pal["muted"])
        self.exam_date_field = ft.TextField(
            value=self.store.exam_date, width=118, height=38, text_size=13,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=6), border_color=pal["border"],
        )

        countdown_strip = ft.Container(
            bgcolor=pal["card"],
            padding=ft.Padding(20, 14, 20, 14),
            border=ft.Border(bottom=ft.BorderSide(1, pal["border"])),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(spacing=2, controls=[self.countdown_text, self.countdown_meta]),
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.END, spacing=6,
                        controls=[
                            ft.Text("考試日期", size=12, color=pal["muted"]),
                            ft.Row(spacing=8, controls=[
                                self.exam_date_field,
                                ft.Button("更新", bgcolor=pal["accent"], color="white",
                                                   on_click=self._on_update_exam_date),
                            ]),
                        ],
                    ),
                ],
            ),
        )

        self.tab_buttons = {}
        tabbar_row = ft.Row(spacing=4)
        for key, label in [("todo", "待辦"), ("notes", "錯題"), ("stats", "統計")]:
            btn = ft.TextButton(
                content=ft.Text(label, size=14),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0)),
                on_click=lambda e, k=key: self.page.run_task(self.switch_tab, k),
            )
            self.tab_buttons[key] = btn
            tabbar_row.controls.append(btn)
        self.tabbar_container = ft.Container(
            bgcolor=pal["card"],
            padding=ft.Padding.symmetric(horizontal=4, vertical=0),
            border=ft.Border(bottom=ft.BorderSide(1, pal["border"])),
            content=tabbar_row,
        )

        p.controls.clear()
        p.add(
            ft.SafeArea(
                expand=True,
                content=ft.Column(
                    expand=True, spacing=0,
                    controls=[header, countdown_strip, self.tabbar_container, self.body_container],
                ),
            )
        )

        self.build_tab_todo()
        self.build_tab_notes()
        self.build_tab_stats()
        # All three tab frames are mounted at once (stacked, only one
        # visible) instead of swapping body_container.content per tab —
        # Flet controls must be attached to the page before .update() works,
        # and refresh_all() below updates every tab's widgets regardless of
        # which one is currently shown.
        for frame in self.tab_frames.values():
            frame.left = frame.top = frame.right = frame.bottom = 0
        self.body_container.content = ft.Stack(expand=True, controls=list(self.tab_frames.values()))
        self.body_container.update()
        await self.switch_tab("todo")
        await self.refresh_all()
        p.run_task(self._countdown_loop)

    def _build_theme_dots(self):
        self.theme_dots.controls.clear()
        current = self.store.data["settings"].get("theme", "light")
        for key, info in config.THEMES.items():
            active = key == current
            self.theme_dots.controls.append(
                ft.Container(
                    width=14, height=14, bgcolor=info["_dot"],
                    border_radius=999,
                    border=ft.Border.all(2, "white") if active else None,
                    tooltip=info["_label"],
                    on_click=lambda e, k=key: self.page.run_task(self.switch_theme, k),
                    ink=True,
                )
            )

    # ── theme / title / save ────────────────────────────────────────────────
    async def switch_theme(self, key):
        self.store.data["settings"]["theme"] = key
        await self.store.save()
        await self.init_shell()

    async def _on_edit_title(self, e):
        field = ft.TextField(value=self.title_text.value, label="新標題", autofocus=True)

        async def confirm(e=None):
            val = field.value.strip()
            if val:
                self.store.data["settings"]["title"] = val
                self.title_text.value = val
                self.page.title = val
                self.title_text.update()
                await self.store.save()
            self.page.pop_dialog()

        async def cancel(e=None):
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True, title=ft.Text("修改標題"), content=field,
            actions=[ft.TextButton("取消", on_click=cancel), ft.Button("儲存", on_click=confirm)],
        )
        self.page.show_dialog(dlg)

    async def _on_manual_save(self, e):
        await self.store.save()
        self._set_status_saved()

    def _set_status_saved(self):
        import datetime as _dt
        self.status_text.value = f"已儲存 {_dt.datetime.now().strftime('%H:%M:%S')}"
        self.status_text.update()

    async def _on_open_display_settings(self, e):
        scale_field = ft.TextField(
            value=str(self.store.data["settings"].get("ui_scale", 100)),
            label="介面縮放 (%)", width=140, keyboard_type=ft.KeyboardType.NUMBER,
        )

        async def apply_scale(e=None):
            try:
                val = int(scale_field.value)
            except (TypeError, ValueError):
                val = -1
            if not (60 <= val <= 200):
                scale_field.error_text = "請輸入 60 到 200 之間的數值"
                scale_field.update()
                return
            self.store.data["settings"]["ui_scale"] = val
            await self.store.save()
            self.page.pop_dialog()

        async def cancel(e=None):
            self.page.pop_dialog()

        async def confirm_reset(e=None):
            self.page.pop_dialog()  # the "確定要重置" confirm dialog
            self.page.pop_dialog()  # this display-settings dialog underneath it
            await self.store.reset_to_defaults()
            await self.init_shell()

        async def on_reset_app(e=None):
            self.page.show_dialog(ft.AlertDialog(
                modal=True, title=ft.Text("確定要重置整個 App 嗎？"),
                content=ft.Text(
                    "這會清空所有待辦、錯題、考試日期、標題、主題與介面縮放設定，"
                    "回到全新安裝的狀態。此操作無法復原。"
                ),
                actions=[
                    ft.TextButton("取消", on_click=lambda e: self.page.pop_dialog()),
                    ft.Button("確定重置", bgcolor=self.palette["warn"], color="white", on_click=confirm_reset),
                ],
            ))

        dlg = ft.AlertDialog(
            modal=True, title=ft.Text("顯示設定"),
            content=ft.Column(tight=True, controls=[
                scale_field,
                ft.Text("60 - 200", size=11, color=self.palette["muted"]),
                ft.Divider(height=20, color=self.palette["border"]),
                ft.Text("危險區域", size=12, weight=ft.FontWeight.BOLD, color=self.palette["warn"]),
                ft.OutlinedButton(
                    content=ft.Text("重置為原始狀態", color=self.palette["warn"]),
                    on_click=on_reset_app,
                ),
            ]),
            actions=[ft.TextButton("取消", on_click=cancel), ft.Button("套用", on_click=apply_scale)],
        )
        self.page.show_dialog(dlg)

    async def _on_update_exam_date(self, e):
        import datetime as _dt
        value = (self.exam_date_field.value or "").strip()
        try:
            _dt.datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            self.page.show_dialog(ft.SnackBar(ft.Text("請使用 YYYY-MM-DD 格式，例如 2026-10-18")))
            return
        self.store.exam_date = value
        await self.store.save()
        self.refresh_countdown()

    # ── tabs ─────────────────────────────────────────────────────────────────
    async def switch_tab(self, key):
        self.active_tab = key
        for k, btn in self.tab_buttons.items():
            active = k == key
            btn.content.color = self.palette["accent"] if active else self.palette["muted"]
            btn.content.weight = ft.FontWeight.BOLD if active else ft.FontWeight.NORMAL
        self.tabbar_container.update()
        for k, frame in self.tab_frames.items():
            frame.visible = k == key
        self.body_container.update()
        if key == "stats":
            self.refresh_stats()

    # ── periodic refresh ─────────────────────────────────────────────────────
    def refresh_countdown(self):
        delta = self.store.get_days_left()
        days, clock = self.store.format_countdown(delta)
        exam_date = self.exam_date_field.value or config.DEFAULT_EXAM_DATE
        if delta.total_seconds() > 0:
            self.countdown_text.value = f"{days} 天  {clock}"
            self.countdown_meta.value = f"距 {exam_date} 考試"
        elif delta.total_seconds() == 0:
            self.countdown_text.value = "今天考試！"
            self.countdown_meta.value = exam_date
        else:
            self.countdown_text.value = f"已過 {abs(days)} 天"
            self.countdown_meta.value = f"考試日：{exam_date}"
        self.countdown_text.update()
        self.countdown_meta.update()

    async def refresh_all(self):
        await self.refresh_day_state()
        self.exam_date_field.value = self.store.exam_date
        self.exam_date_field.update()
        self.refresh_countdown()
        self.render_todos()
        self.refresh_stats()
        self.refresh_notes()

    async def refresh_day_state(self):
        current_key = self.store.get_today_key()
        if current_key != self.store.today_key:
            await self.store.ensure_today_plan()

    async def _countdown_loop(self):
        while True:
            await asyncio.sleep(1)
            try:
                await self.refresh_day_state()
                self.refresh_countdown()
            except Exception:
                return
