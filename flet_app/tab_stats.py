"""Stats tab — ported from app/tab_stats.py StatsTabMixin.

The hand-drawn Canvas bar chart is replaced with Flet Container rows using
integer flex weights (`expand=`) to render proportional bars — no charting
library needed, works identically on every platform including mobile/web.
The ttk.Treeview detail list becomes a sortable ft.DataTable.
"""
from datetime import date, datetime

import flet as ft

import theme

DETAIL_COLUMNS = [
    ("date", "日期"), ("weekday", "星期"), ("time", "時間"),
    ("item", "項目"), ("done", "完成"), ("hours", "時數"), ("note", "備註"),
]
WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]


class StatsTabMixin:
    def build_tab_stats(self):
        pal = self.palette
        self.stats_mode = "chart"

        self.stats_chart_btn = ft.TextButton("📊 讀書統計", on_click=lambda e: self.page.run_task(self.switch_stats_mode, "chart"))
        self.stats_detail_btn = ft.TextButton("🗓 全部詳細項", on_click=lambda e: self.page.run_task(self.switch_stats_mode, "detail"))
        mode_bar = ft.Container(
            bgcolor=pal["card"], border=ft.Border(bottom=ft.BorderSide(1, pal["border"])),
            content=ft.Row(controls=[self.stats_chart_btn, self.stats_detail_btn]),
        )

        self.stat_today_lbl = self._stat_card(pal["success"], "今日完成率")
        self.stat_week_lbl = self._stat_card("#3b82f6", "本週完成率")
        self.stat_days_lbl = self._stat_card(pal["accent"], "累積讀書天數")
        cards_row = ft.Container(
            padding=ft.Padding.symmetric(horizontal=16, vertical=16),
            content=ft.Row(spacing=8, controls=[
                self.stat_today_lbl.parent_card, self.stat_week_lbl.parent_card, self.stat_days_lbl.parent_card,
            ]),
        )

        self.stats_summary_text = ft.Text("", size=12, color=pal["muted"])

        self.chart_column = ft.ListView(expand=True, spacing=10, padding=ft.Padding.all(16))
        self.stats_chart_frame = ft.Container(
            expand=True,
            padding=ft.Padding.symmetric(horizontal=16),
            content=ft.Container(border=ft.Border.all(1, pal["border"]), bgcolor=pal["card"],
                                  padding=ft.Padding.all(4), content=self.chart_column, expand=True),
        )

        self._detail_rows_cache = []
        self._detail_sort = (None, False)
        self.detail_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(label), on_sort=lambda e, k=key: self.page.run_task(self._sort_detail, k))
                     for key, label in DETAIL_COLUMNS],
            rows=[],
            heading_row_color=pal["strip_bg"],
        )
        self.detail_summary_text = ft.Text("", size=12, color=pal["muted"])
        manage_row = self._build_history_manage_row()
        self.stats_detail_frame = ft.Container(
            expand=True,
            padding=ft.Padding.symmetric(horizontal=16),
            content=ft.Column(expand=True, controls=[
                manage_row,
                ft.Container(
                    border=ft.Border.all(1, pal["border"]), bgcolor=pal["card"], expand=True,
                    content=ft.Column(expand=True, controls=[
                        ft.Row(scroll=ft.ScrollMode.AUTO, controls=[self.detail_table]),
                    ], scroll=ft.ScrollMode.AUTO),
                ),
                ft.Container(alignment=ft.Alignment.CENTER_RIGHT, padding=ft.Padding.symmetric(vertical=4),
                             content=self.detail_summary_text),
            ]),
        )

        # Both frames are mounted together (like the outer tab-bar Stack in
        # shell.py) so refresh_stats() can update the detail table even
        # while chart mode is showing, and vice versa.
        self.stats_detail_frame.visible = False
        self.stats_chart_frame.left = self.stats_chart_frame.top = 0
        self.stats_chart_frame.right = self.stats_chart_frame.bottom = 0
        self.stats_detail_frame.left = self.stats_detail_frame.top = 0
        self.stats_detail_frame.right = self.stats_detail_frame.bottom = 0
        self.stats_body = ft.Container(
            expand=True,
            content=ft.Stack(expand=True, controls=[self.stats_chart_frame, self.stats_detail_frame]),
        )

        summary_row = ft.Container(
            padding=ft.Padding.only(left=20, top=0, right=20, bottom=6), content=self.stats_summary_text)

        self.tab_frames["stats"] = ft.Column(
            expand=True, spacing=0,
            controls=[mode_bar, cards_row, summary_row, self.stats_body],
        )

    # ── history management (delete a whole day / a date range) ─────────────
    def _build_history_manage_row(self):
        pal = self.palette
        self._manage_day_key = self.store.today_key
        self._manage_range_start = self.store.today_key
        self._manage_range_end = self.store.today_key

        self.manage_day_text = ft.Text(self._manage_day_key, size=12)
        self.manage_range_start_text = ft.Text(self._manage_range_start, size=12)
        self.manage_range_end_text = ft.Text(self._manage_range_end, size=12)

        def _open_picker(get_key, on_pick):
            async def handler(e):
                async def on_change(e):
                    if dp.value is None:
                        return
                    picked = dp.value.date() if hasattr(dp.value, "date") else dp.value
                    on_pick(picked.isoformat())
                dp = ft.DatePicker(value=date.fromisoformat(get_key()), on_change=on_change)
                self.page.show_dialog(dp)
            return handler

        def _pick_day(new_key):
            self._manage_day_key = new_key
            self.manage_day_text.value = new_key
            self.manage_day_text.update()

        def _pick_range_start(new_key):
            self._manage_range_start = new_key
            self.manage_range_start_text.value = new_key
            self.manage_range_start_text.update()

        def _pick_range_end(new_key):
            self._manage_range_end = new_key
            self.manage_range_end_text.value = new_key
            self.manage_range_end_text.update()

        async def confirm_delete_day(e):
            key = self._manage_day_key
            count = len(self.store.data["todos_by_date"].get(key, []))
            if count == 0:
                self.page.show_dialog(ft.SnackBar(ft.Text(f"{key} 沒有資料可刪除")))
                return

            async def do_delete(e=None):
                self.page.pop_dialog()
                await self.store.delete_date(key)
                self.render_todos()
                self.refresh_stats()
                self.page.show_dialog(ft.SnackBar(ft.Text(f"已刪除 {key} 當天的 {count} 筆待辦")))

            self.page.show_dialog(ft.AlertDialog(
                modal=True, title=ft.Text("確認刪除"),
                content=ft.Text(f"確定要刪除 {key} 當天的 {count} 筆待辦嗎？此操作無法復原。"),
                actions=[ft.TextButton("取消", on_click=lambda e: self.page.pop_dialog()),
                         ft.Button("刪除", bgcolor=pal["warn"], color="white", on_click=do_delete)],
            ))

        async def confirm_delete_range(e):
            start, end = self._manage_range_start, self._manage_range_end
            if start > end:
                start, end = end, start
            days, items = self.store.count_date_range(start, end)
            if days == 0:
                self.page.show_dialog(ft.SnackBar(ft.Text("這個區間沒有資料可刪除")))
                return

            async def do_delete(e=None):
                self.page.pop_dialog()
                await self.store.delete_date_range(start, end)
                self.render_todos()
                self.refresh_stats()
                self.page.show_dialog(ft.SnackBar(ft.Text(f"已刪除 {days} 天、共 {items} 筆待辦")))

            self.page.show_dialog(ft.AlertDialog(
                modal=True, title=ft.Text("確認刪除"),
                content=ft.Text(f"確定要刪除 {start} ～ {end} 共 {days} 天、{items} 筆待辦嗎？此操作無法復原。"),
                actions=[ft.TextButton("取消", on_click=lambda e: self.page.pop_dialog()),
                         ft.Button("刪除", bgcolor=pal["warn"], color="white", on_click=do_delete)],
            ))

        return ft.Container(
            bgcolor=pal["strip_bg"], border=ft.Border(bottom=ft.BorderSide(1, pal["border"])),
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            content=ft.Column(spacing=6, controls=[
                ft.Row(spacing=6, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("刪除整天", size=12, color=pal["muted"]),
                    ft.OutlinedButton(content=self.manage_day_text,
                                       on_click=_open_picker(lambda: self._manage_day_key, _pick_day)),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color=pal["warn"],
                                  tooltip="刪除該天所有待辦", on_click=confirm_delete_day),
                ]),
                ft.Row(spacing=6, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("刪除區間", size=12, color=pal["muted"]),
                    ft.OutlinedButton(content=self.manage_range_start_text,
                                       on_click=_open_picker(lambda: self._manage_range_start, _pick_range_start)),
                    ft.Text("～"),
                    ft.OutlinedButton(content=self.manage_range_end_text,
                                       on_click=_open_picker(lambda: self._manage_range_end, _pick_range_end)),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color=pal["warn"],
                                  tooltip="刪除區間內所有待辦", on_click=confirm_delete_range),
                ]),
            ]),
        )

    def _stat_card(self, accent, title):
        pal = self.palette
        value_lbl = ft.Text("--", size=22, weight=ft.FontWeight.BOLD, color=accent)
        card = ft.Container(
            expand=True, border=ft.Border.all(1, pal["border"]), bgcolor=pal["card"],
            content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4, controls=[
                ft.Container(height=3, bgcolor=accent),
                ft.Container(padding=ft.Padding.only(left=0, top=10, right=0, bottom=0),
                             content=ft.Text(title, size=11, color=pal["muted"])),
                ft.Container(padding=ft.Padding.only(left=0, top=0, right=0, bottom=12), content=value_lbl),
            ]),
        )
        value_lbl.parent_card = card
        return value_lbl

    async def switch_stats_mode(self, mode):
        self.stats_mode = mode
        pal = self.palette
        if mode == "chart":
            self.stats_chart_frame.visible = True
            self.stats_detail_frame.visible = False
            self.stats_chart_btn.style = ft.ButtonStyle(color=pal["accent"])
            self.stats_detail_btn.style = ft.ButtonStyle(color=pal["muted"])
        else:
            self.stats_chart_frame.visible = False
            self.stats_detail_frame.visible = True
            self.stats_detail_btn.style = ft.ButtonStyle(color=pal["accent"])
            self.stats_chart_btn.style = ft.ButtonStyle(color=pal["muted"])
        self.stats_body.update()
        self.stats_chart_btn.update()
        self.stats_detail_btn.update()
        self.refresh_stats()

    # ── data refresh ─────────────────────────────────────────────────────────
    def refresh_stats(self):
        todos = self.store.todos
        total_today = len(todos)
        done_today = sum(1 for t in todos if t.get("done"))
        today_rate = int((done_today / total_today) * 100) if total_today else 0

        week_start = date.today().toordinal() - 6
        weekly_total = weekly_done = 0
        for todo_date, items in self.store.data["todos_by_date"].items():
            try:
                if date.fromisoformat(todo_date).toordinal() < week_start:
                    continue
            except ValueError:
                continue
            weekly_total += len(items)
            weekly_done += sum(1 for t in items if t.get("done"))
        weekly_rate = int((weekly_done / weekly_total) * 100) if weekly_total else 0
        cum_days = self.store.get_study_days()

        self.stat_today_lbl.value = f"{today_rate}%"
        self.stat_week_lbl.value = f"{weekly_rate}%"
        self.stat_days_lbl.value = f"{cum_days} 天"
        self.stats_summary_text.value = f"今日完成：{done_today}/{total_today}　本週：{weekly_done}/{weekly_total}"
        for c in (self.stat_today_lbl, self.stat_week_lbl, self.stat_days_lbl, self.stats_summary_text):
            c.update()

        self._refresh_study_chart()
        self._refresh_stats_detail()

    def _refresh_study_chart(self):
        pal = self.palette
        totals = {}
        opts = self.store.get_todo_options()
        for items in self.store.data["todos_by_date"].values():
            for item in items:
                if not item.get("done"):
                    continue
                ts, te = item.get("time_start", ""), item.get("time_end", "")
                if not ts or not te:
                    continue
                try:
                    hours = (datetime.strptime(te, "%H:%M") - datetime.strptime(ts, "%H:%M")).total_seconds() / 3600
                    if hours <= 0:
                        continue
                except ValueError:
                    continue
                subj = item.get("text", "")
                if subj not in opts:
                    subj = next((s for s in opts if s in subj), subj)
                totals[subj] = totals.get(subj, 0.0) + hours

        if not totals:
            self.chart_column.controls = [ft.Container(alignment=ft.Alignment.CENTER, padding=ft.Padding.symmetric(vertical=30),
                                                         content=ft.Text("尚無讀書記錄（完成待辦後自動計算）", size=12, color=pal["muted"]))]
            self.chart_column.update()
            return

        max_hrs = max(totals.values()) or 1
        total_h = sum(totals.values())
        rows = []
        for subj in opts:
            hours = totals.get(subj, 0.0)
            has_val = hours > 0
            color = theme.subject_color(subj, pal["muted"])
            weight = max(1, round((hours / max_hrs) * 100)) if has_val else 0
            remainder = max(0, 100 - weight)
            bar_children = []
            if weight:
                bar_children.append(ft.Container(bgcolor=color, expand=weight, height=14, border_radius=3))
            if remainder:
                bar_children.append(ft.Container(expand=remainder, height=14))
            rows.append(ft.Row(vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Container(width=64, content=ft.Text(subj, size=12, color=pal["text"] if has_val else pal["muted"],
                                                          weight=ft.FontWeight.BOLD if has_val else ft.FontWeight.NORMAL, text_align=ft.TextAlign.RIGHT)),
                ft.Container(bgcolor=pal["strip_bg"], expand=True, height=14, border_radius=3,
                             content=ft.Row(spacing=0, controls=bar_children) if bar_children else None),
                ft.Container(width=56, content=ft.Text(f"{hours:.1f} h", size=12,
                                                          color=color if has_val else pal["muted"],
                                                          weight=ft.FontWeight.BOLD if has_val else ft.FontWeight.NORMAL)),
            ]))
        rows.append(ft.Divider(height=1, color=pal["border"]))
        rows.append(ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
            ft.Text(f"共讀 {total_h:.1f} 小時", size=14, weight=ft.FontWeight.BOLD, color=pal["accent"]),
            ft.Text(f"{self.store.get_study_days()} 天有記錄", size=12, color=pal["muted"]),
        ]))
        self.chart_column.controls = rows
        self.chart_column.update()

    def _refresh_stats_detail(self):
        pal = self.palette
        all_dates = sorted((k for k, v in self.store.data["todos_by_date"].items() if v), reverse=True)
        entries = []
        total_h = done_h = 0.0
        total_n = done_n = 0
        for date_key in all_dates:
            items = self.store.data["todos_by_date"].get(date_key, [])
            try:
                d = date.fromisoformat(date_key)
                is_today = date_key == self.store.today_key
                dlabel = f"{d.year}/{d.month:02d}/{d.day:02d}"
                wlabel = f"週{WEEKDAYS[d.weekday()]}"
            except ValueError:
                dlabel, wlabel, is_today = date_key, "", False
            for item in items:
                is_done = item.get("done", False)
                ts, te = item.get("time_start", ""), item.get("time_end", "")
                note = item.get("note", "").strip()
                hours = 0.0
                if ts and te:
                    try:
                        hours = max(0.0, (datetime.strptime(te, "%H:%M") - datetime.strptime(ts, "%H:%M")).total_seconds() / 3600)
                    except ValueError:
                        pass
                total_h += hours
                total_n += 1
                if is_done:
                    done_h += hours
                    done_n += 1
                entries.append({
                    "date": dlabel, "date_sort": date_key, "weekday": wlabel,
                    "time": f"{ts}–{te}" if ts and te else "―",
                    "item": item.get("text", ""), "done": "✓" if is_done else "",
                    "hours": hours, "note": note, "is_today": is_today, "is_done": is_done,
                })
        self._detail_rows_cache = entries
        self._detail_sort = (None, False)
        self._render_detail_table(entries)

        parts = []
        if total_h > 0:
            parts.append(f"完成 {done_h:.1f}h / 共 {total_h:.1f}h")
        if total_n > 0:
            parts.append(f"事項 {done_n}/{total_n}")
        parts.append(f"共 {len(all_dates)} 天有記錄")
        self.detail_summary_text.value = "   ".join(parts)
        self.detail_summary_text.update()

    def _render_detail_table(self, entries):
        pal = self.palette
        rows = []
        for entry in entries:
            color = pal["done_fg"] if entry["is_done"] else pal["text"]
            rows.append(ft.DataRow(
                color=pal["strip_bg"] if entry["is_today"] else None,
                cells=[
                    ft.DataCell(ft.Text(entry["date"], size=12, color=color)),
                    ft.DataCell(ft.Text(entry["weekday"], size=12, color=color)),
                    ft.DataCell(ft.Text(entry["time"], size=12, color=color)),
                    ft.DataCell(ft.Text(entry["item"], size=12, color=color)),
                    ft.DataCell(ft.Text(entry["done"], size=12, color=color)),
                    ft.DataCell(ft.Text(f"{entry['hours']:.1f}h" if entry["hours"] > 0 else "", size=12, color=color)),
                    ft.DataCell(ft.Text(entry["note"], size=12, color=color)),
                ],
            ))
        self.detail_table.rows = rows
        self.detail_table.update()

    async def _sort_detail(self, col):
        prev_col, prev_reverse = self._detail_sort
        reverse = prev_col == col and not prev_reverse
        key_map = {
            "date": lambda e: e["date_sort"], "hours": lambda e: e["hours"],
        }
        keyfunc = key_map.get(col, lambda e: e.get(col, ""))
        entries = sorted(self._detail_rows_cache, key=keyfunc, reverse=reverse)
        self._detail_sort = (col, reverse)
        self._render_detail_table(entries)
