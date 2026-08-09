"""Pure data layer — ported from the Tkinter app's app/storage.py DataMixin,
with all tkinter references removed and file I/O replaced by Flet's
SharedPreferences service (cross-platform key/value storage: works
identically on Windows/macOS/Linux/Android/iOS/Web, each install keeping
its own local data — no tkinter widgets, no page access here at all).
"""
import json
import time
from datetime import date, datetime

import flet as ft

import config


class Store:
    def __init__(self, prefs: ft.SharedPreferences):
        self.prefs = prefs
        self.data: dict = {}
        self.exam_date = config.DEFAULT_EXAM_DATE
        self.today_key = self.get_today_key()
        self.view_date_key = self.today_key
        self.todos: list = []

    @staticmethod
    def get_today_key():
        return date.today().isoformat()

    # ── load / save ──────────────────────────────────────────────────────────
    @staticmethod
    def _default_data():
        return {
            "settings": {
                "exam_date": config.DEFAULT_EXAM_DATE,
                "todo_options": list(config.DEFAULT_SUBJECTS),
                "title": config.DEFAULT_TITLE,
                "theme": "light",
                "ui_scale": 100,
            },
            "todos_by_date": {},
            "notes": [],
            "study_logs": [],
        }

    async def load(self):
        self.data = self._default_data()
        raw = await self.prefs.get(config.STORAGE_KEY)
        loaded = None
        if raw:
            try:
                loaded = json.loads(raw)
            except (TypeError, ValueError):
                loaded = None
        if loaded:
            if "settings" in loaded:
                self.data["settings"].update(loaded["settings"])
            if "todos_by_date" in loaded:
                self.data["todos_by_date"] = loaded["todos_by_date"]
            if "notes" in loaded:
                self.data["notes"] = self.normalize_notes(loaded["notes"])
            if "study_logs" in loaded:
                self.data["study_logs"] = loaded["study_logs"]
            if "todos" in loaded:
                self.migrate_legacy_todos(loaded["todos"])
        self.exam_date = self.data["settings"].get("exam_date", config.DEFAULT_EXAM_DATE)

    def migrate_legacy_todos(self, legacy_todos):
        today = self.get_today_key()
        converted = []
        for todo in legacy_todos:
            converted.append({
                "id": str(time.time_ns()),
                "section": "今日",
                "time_start": todo.get("time", "08:30"),
                "time_end": "10:00",
                "text": todo.get("text", ""),
                "done": bool(todo.get("done", False)),
                "date": todo.get("date", today),
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
                body = "\n".join(lines[1:]).strip() if len(lines) > 1 else note.strip()
                normalized.append({
                    "date": header.rstrip(":") or f"{date.today().month}/{date.today().day}",
                    "subject": "",
                    "question": body or note.strip(),
                    "answer": "",
                    "reason": "",
                })
        return normalized

    async def save(self):
        self.data["settings"]["exam_date"] = self.exam_date or config.DEFAULT_EXAM_DATE
        self.data["settings"]["ui_scale"] = self.data["settings"].get("ui_scale", 100)
        self.data["todos_by_date"][self.view_date_key] = self.todos
        await self.prefs.set(config.STORAGE_KEY, json.dumps(self.data, ensure_ascii=False))

    # ── undo helpers ─────────────────────────────────────────────────────────
    def pop_todo_with_index(self, item, todos=None):
        todos = self.todos if todos is None else todos
        try:
            idx = todos.index(item)
        except ValueError:
            return None
        todos.pop(idx)
        return idx

    def restore_todo_at(self, idx, item, todos=None):
        todos = self.todos if todos is None else todos
        todos.insert(min(idx, len(todos)), item)

    def pop_note_with_index(self, note):
        try:
            idx = self.data["notes"].index(note)
        except ValueError:
            return None
        self.data["notes"].pop(idx)
        return idx

    def restore_note_at(self, idx, note):
        self.data["notes"].insert(min(idx, len(self.data["notes"])), note)

    # ── date / plan ──────────────────────────────────────────────────────────
    async def ensure_today_plan(self):
        self.today_key = self.get_today_key()
        self.data["todos_by_date"].setdefault(self.today_key, [])
        self.data["todos_by_date"].setdefault(self.view_date_key, [])
        self.todos = self.data["todos_by_date"][self.view_date_key]
        changed = self.fill_missing_todo_times(self.todos)
        if self.view_date_key == self.today_key and not self.todos:
            for item in config.DEFAULT_PLAN:
                self.todos.append({
                    "id": str(time.time_ns()) + item["subject"],
                    "section": item["section"],
                    "time_start": item["time_start"],
                    "time_end": item["time_end"],
                    "text": item["subject"],
                    "done": False,
                    "date": self.today_key,
                })
            changed = True
        if changed:
            await self.save()

    def fill_missing_todo_times(self, todos):
        d_start = {i["subject"]: i["time_start"] for i in config.DEFAULT_PLAN}
        d_end = {i["subject"]: i["time_end"] for i in config.DEFAULT_PLAN}
        s_start = {i["section"]: i["time_start"] for i in config.DEFAULT_PLAN}
        s_end = {i["section"]: i["time_end"] for i in config.DEFAULT_PLAN}
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
        return changed

    async def switch_view_date(self, new_key, carry_forward=False):
        self.data["todos_by_date"][self.view_date_key] = self.todos
        old_key = self.view_date_key
        self.view_date_key = new_key
        if carry_forward and (
            new_key not in self.data["todos_by_date"] or not self.data["todos_by_date"][new_key]
        ):
            template = self.data["todos_by_date"].get(old_key, [])
            self.data["todos_by_date"][new_key] = [
                {
                    **{k: v for k, v in item.items() if k not in ("done", "note", "auto_logged", "id", "date")},
                    "id": str(time.time_ns()) + item.get("text", ""),
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
        await self.save()

    def infer_section(self, time_start: str) -> str:
        try:
            h = datetime.strptime(time_start, "%H:%M").hour
        except ValueError:
            return "今日"
        if 5 <= h < 12:
            return "上午"
        if 12 <= h < 18:
            return "下午"
        return "晚上"

    # ── countdown ────────────────────────────────────────────────────────────
    def get_days_left(self):
        try:
            exam_day = datetime.strptime(self.exam_date or config.DEFAULT_EXAM_DATE, "%Y-%m-%d")
        except ValueError:
            exam_day = datetime.strptime(config.DEFAULT_EXAM_DATE, "%Y-%m-%d")
        return exam_day - datetime.now()

    @staticmethod
    def format_countdown(delta):
        total = max(0, int(delta.total_seconds()))
        days, r = divmod(total, 86400)
        hours, r = divmod(r, 3600)
        mins, sec = divmod(r, 60)
        return days, f"{hours:02d}:{mins:02d}:{sec:02d}"

    def get_study_days(self):
        return sum(1 for items in self.data["todos_by_date"].values() if any(t.get("done") for t in items))

    def get_todo_options(self):
        return list(self.data.get("settings", {}).get("todo_options", config.DEFAULT_SUBJECTS))

    # ── history management (delete-by-day / delete-by-range) ───────────────
    def count_date_range(self, start_key, end_key):
        """(day_count, item_count) for dates within [start_key, end_key] that hold data."""
        days = items = 0
        for key, todos in self.data["todos_by_date"].items():
            if todos and start_key <= key <= end_key:
                days += 1
                items += len(todos)
        return days, items

    async def delete_date(self, date_key):
        removed = self.data["todos_by_date"].pop(date_key, None)
        await self._after_history_delete([date_key])
        return len(removed) if removed else 0

    async def delete_date_range(self, start_key, end_key):
        keys = [k for k in list(self.data["todos_by_date"]) if start_key <= k <= end_key]
        removed_items = sum(len(self.data["todos_by_date"][k]) for k in keys)
        for k in keys:
            del self.data["todos_by_date"][k]
        await self._after_history_delete(keys)
        return len(keys), removed_items

    async def _after_history_delete(self, deleted_keys):
        # self.todos is a *reference* into todos_by_date — if the date being
        # viewed just got deleted, that reference now points at a detached
        # list, so hop back to today before anything tries to edit it.
        if self.view_date_key in deleted_keys:
            self.view_date_key = self.today_key
        await self.ensure_today_plan()
        await self.save()

    # ── factory reset ────────────────────────────────────────────────────────
    async def reset_to_defaults(self):
        self.data = self._default_data()
        self.exam_date = config.DEFAULT_EXAM_DATE
        self.today_key = self.get_today_key()
        self.view_date_key = self.today_key
        self.todos = []
        await self.ensure_today_plan()
        await self.save()
