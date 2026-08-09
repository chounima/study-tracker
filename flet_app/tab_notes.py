"""Notes (錯題) tab — ported from app/tab_notes.py NotesTabMixin."""
from datetime import date, timedelta

import flet as ft

import theme

PERIODS = ["全部", "今天", "本週", "本月"]
ALL_SUBJECTS = "全部科目"


def _opts(values):
    return [ft.DropdownOption(key=v, text=v) for v in values]


class NotesTabMixin:
    def build_tab_notes(self):
        pal = self.palette
        self.notes_mode = "add"

        self.note_add_mode_btn = ft.TextButton("＋ 新增", on_click=lambda e: self.page.run_task(self.switch_notes_mode, "add"))
        self.note_search_mode_btn = ft.TextButton("🔍 查詢", on_click=lambda e: self.page.run_task(self.switch_notes_mode, "search"))
        self.note_count_label = ft.Text("0 筆", size=12, color=pal["muted"])

        mode_bar = ft.Container(
            bgcolor=pal["card"], border=ft.Border(bottom=ft.BorderSide(1, pal["border"])),
            content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Row(controls=[self.note_add_mode_btn, self.note_search_mode_btn]),
                ft.Container(padding=ft.Padding.only(left=0, top=0, right=16, bottom=0), content=self.note_count_label),
            ]),
        )

        opts0 = self.store.get_todo_options()
        self.note_subject_dd = ft.Dropdown(value=(opts0[0] if opts0 else None), options=_opts(opts0), expand=True, dense=True)
        self.note_question_field = ft.TextField(label="題目", dense=True)
        self.note_answer_field = ft.TextField(label="答案", dense=True)
        self.note_reason_field = ft.TextField(label="原因（選填）", dense=True)

        self.notes_add_frame = ft.Container(
            bgcolor=pal["strip_bg"], padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            content=ft.Column(spacing=8, controls=[
                ft.Row(controls=[ft.Text("科目", size=12, color=pal["muted"], width=44), self.note_subject_dd]),
                self.note_question_field, self.note_answer_field, self.note_reason_field,
                ft.Row(spacing=10, controls=[
                    ft.Button("新增錯題", bgcolor=pal["accent"], color="white", on_click=self._on_add_note),
                    ft.OutlinedButton("清除全部", on_click=self._on_clear_notes),
                ]),
            ]),
        )

        self.note_search_field = ft.TextField(label="關鍵字", dense=True, on_submit=self._on_search_notes)
        self.note_filter_subject_dd = ft.Dropdown(value=ALL_SUBJECTS, options=_opts([ALL_SUBJECTS] + opts0), width=140, dense=True)
        self.note_filter_period_dd = ft.Dropdown(value="全部", options=_opts(PERIODS), width=110, dense=True)
        self.note_result_label = ft.Text("", size=12, color=pal["muted"])

        self.notes_search_frame = ft.Container(
            bgcolor=pal["strip_bg"], padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            content=ft.Column(spacing=8, controls=[
                self.note_search_field,
                ft.Row(spacing=12, controls=[
                    ft.Text("科目", size=12, color=pal["muted"]), self.note_filter_subject_dd,
                    ft.Text("時段", size=12, color=pal["muted"]), self.note_filter_period_dd,
                ]),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Row(spacing=8, controls=[
                        ft.Button("搜尋", bgcolor=pal["accent"], color="white", on_click=self._on_search_notes),
                        ft.OutlinedButton("清除篩選", on_click=self._on_clear_note_search),
                    ]),
                    self.note_result_label,
                ]),
            ]),
        )

        # Both forms are mounted together (one hidden via `visible`) rather
        # than swapped in on demand, so refresh_option_dependents() can
        # safely .update() the search form's dropdowns even before the user
        # has ever switched to search mode — see the analogous fix in
        # shell.py's tab body / tab_stats.py's chart-vs-detail switch.
        self.notes_search_frame.visible = False
        self.notes_form_area = ft.Column(spacing=0, controls=[self.notes_add_frame, self.notes_search_frame])
        self.note_cards_list = ft.ListView(expand=True, spacing=8, padding=ft.Padding.all(10))

        self.tab_frames["notes"] = ft.Column(
            expand=True, spacing=0,
            controls=[mode_bar, self.notes_form_area, self.note_cards_list],
        )

    async def switch_notes_mode(self, mode):
        self.notes_mode = mode
        pal = self.palette
        if mode == "add":
            self.notes_add_frame.visible = True
            self.notes_search_frame.visible = False
            self.note_add_mode_btn.style = ft.ButtonStyle(color=pal["accent"])
            self.note_search_mode_btn.style = ft.ButtonStyle(color=pal["muted"])
        else:
            self.notes_add_frame.visible = False
            self.notes_search_frame.visible = True
            self.note_search_mode_btn.style = ft.ButtonStyle(color=pal["accent"])
            self.note_add_mode_btn.style = ft.ButtonStyle(color=pal["muted"])
        self.notes_form_area.update()
        self.note_add_mode_btn.update()
        self.note_search_mode_btn.update()

    async def _on_add_note(self, e):
        subject = self.note_subject_dd.value or ""
        question = (self.note_question_field.value or "").strip()
        answer = (self.note_answer_field.value or "").strip()
        reason = (self.note_reason_field.value or "").strip()
        if not subject or not question or not answer:
            self.page.show_dialog(ft.SnackBar(ft.Text("請至少填入科目、題目、答案")))
            return
        self.store.data["notes"].insert(0, {
            "date": f"{date.today().month}/{date.today().day}",
            "subject": subject, "question": question, "answer": answer, "reason": reason,
        })
        self.note_question_field.value = ""
        self.note_answer_field.value = ""
        self.note_reason_field.value = ""
        self.note_question_field.update()
        self.note_answer_field.update()
        self.note_reason_field.update()
        await self.store.save()
        self.refresh_notes()

    async def _on_clear_notes(self, e):
        async def confirm(e=None):
            self.store.data["notes"] = []
            await self.store.save()
            self.refresh_notes()
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True, title=ft.Text("確認"), content=ft.Text("確定要清除所有錯題紀錄？"),
            actions=[ft.TextButton("取消", on_click=lambda e: self.page.pop_dialog()),
                     ft.Button("清除", bgcolor=self.palette["warn"], color="white", on_click=confirm)],
        )
        self.page.show_dialog(dlg)

    def refresh_notes(self, notes=None):
        if notes is None:
            notes = self.store.data["notes"]
        self.note_count_label.value = f"{len(self.store.data['notes'])} 筆"
        self.note_count_label.update()
        valid = [n for n in notes if isinstance(n, dict)]
        if not valid:
            self.note_cards_list.controls = [
                ft.Container(alignment=ft.Alignment.CENTER, padding=ft.Padding.symmetric(vertical=24),
                             content=ft.Text("（尚無符合的錯題紀錄）", size=12, color=self.palette["muted"]))
            ]
        else:
            self.note_cards_list.controls = [self._build_note_card(n) for n in valid]
        self.note_cards_list.update()

    def _build_note_card(self, note):
        pal = self.palette
        subject = note.get("subject", "")
        sbg = theme.subject_color(subject, pal["muted"])
        header = ft.Container(
            bgcolor=sbg if subject else pal["strip_bg"],
            padding=ft.Padding.symmetric(horizontal=8, vertical=6),
            content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Row(spacing=8, controls=[
                    ft.Text(subject, size=12, color="white") if subject else ft.Text(""),
                    ft.Text(note.get("date", "--"), size=12, color="white" if subject else pal["muted"]),
                ]),
                ft.IconButton(ft.Icons.CLOSE, icon_size=14,
                              icon_color="white" if subject else pal["warn"],
                              on_click=lambda e, n=note: self.page.run_task(self._on_delete_note, n)),
            ]),
        )
        question = note.get("question", note.get("wrong", ""))
        answer = note.get("answer", "")
        reason = note.get("reason", "")
        body_children = [
            ft.Row(spacing=6, controls=[ft.Text("Q", size=12, weight=ft.FontWeight.BOLD, color=pal["accent"]),
                                          ft.Text(question, size=13, color=pal["text"], expand=True)]),
            ft.Row(spacing=6, controls=[ft.Text("A", size=12, weight=ft.FontWeight.BOLD, color=pal["accent"]),
                                          ft.Text(answer, size=13, color="#166534", expand=True)]),
        ]
        if reason:
            body_children.append(ft.Row(spacing=6, controls=[
                ft.Text("原", size=12, weight=ft.FontWeight.BOLD, color=pal["accent"]),
                ft.Text(reason, size=13, color=pal["muted"], expand=True)]))
        body = ft.Container(bgcolor=pal["card"], padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                             content=ft.Column(spacing=2, controls=body_children))
        return ft.Container(border=ft.Border.all(1, pal["border"]), content=ft.Column(spacing=0, controls=[header, body]))

    async def _on_search_notes(self, e):
        keyword = (self.note_search_field.value or "").strip().lower()
        subject_filter = self.note_filter_subject_dd.value
        period_filter = self.note_filter_period_dd.value
        today = date.today()
        results = []
        for note in self.store.data["notes"]:
            if not isinstance(note, dict):
                continue
            if subject_filter != ALL_SUBJECTS and note.get("subject") != subject_filter:
                continue
            if period_filter != "全部":
                note_date_str = note.get("date", "")
                try:
                    month, day = map(int, note_date_str.split("/"))
                    note_dt = date(today.year, month, day)
                    if period_filter == "今天" and note_dt != today:
                        continue
                    if period_filter == "本週" and note_dt < today - timedelta(days=today.weekday()):
                        continue
                    if period_filter == "本月" and note_dt.month != today.month:
                        continue
                except (ValueError, AttributeError):
                    pass
            if keyword:
                haystack = " ".join([
                    note.get("subject", ""), note.get("question", note.get("wrong", "")),
                    note.get("answer", ""), note.get("reason", ""),
                ]).lower()
                if keyword not in haystack:
                    continue
            results.append(note)
        self.note_result_label.value = f"找到 {len(results)} 筆"
        self.note_result_label.update()
        self.refresh_notes(results)

    async def _on_clear_note_search(self, e):
        self.note_search_field.value = ""
        self.note_filter_subject_dd.value = ALL_SUBJECTS
        self.note_filter_period_dd.value = "全部"
        self.note_result_label.value = ""
        self.note_search_field.update()
        self.note_filter_subject_dd.update()
        self.note_filter_period_dd.update()
        self.note_result_label.update()
        self.refresh_notes()

    async def _on_delete_note(self, note):
        idx = self.store.pop_note_with_index(note)
        if idx is None:
            return
        await self.store.save()
        if self.notes_mode == "search":
            await self._on_search_notes(None)
        else:
            self.refresh_notes()

        async def undo(e=None):
            self.store.restore_note_at(idx, note)
            await self.store.save()
            if self.notes_mode == "search":
                await self._on_search_notes(None)
            else:
                self.refresh_notes()

        label = note.get("question", note.get("subject", "錯題"))
        self.page.show_dialog(ft.SnackBar(content=ft.Text(f"已刪除「{label}」"), action="復原", on_action=undo, duration=5000))
