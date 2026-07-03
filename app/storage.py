import json
import os
import time
from datetime import datetime, date
from tkinter import messagebox

from .config import DATA_FILE, DEFAULT_EXAM_DATE, DEFAULT_PLAN, DEFAULT_SUBJECTS


class DataMixin:
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

    def get_study_days(self):
        return sum(
            1 for items in self.data["todos_by_date"].values()
            if any(t.get("done") for t in items)
        )
