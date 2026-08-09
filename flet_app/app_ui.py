"""Combines the shell + three tab mixins into one AppUI class — same
multi-inheritance composition pattern as the original Tkinter ExamPrepApp,
so the module boundaries stay familiar to anyone who's worked on that
version (see the original project's README section 4.2)."""
import flet as ft

from shell import ShellMixin
from store import Store
from tab_notes import NotesTabMixin
from tab_stats import StatsTabMixin
from tab_todo import TodoTabMixin


def _dd_opts(values):
    return [ft.DropdownOption(key=v, text=v) for v in values]


class AppUI(ShellMixin, TodoTabMixin, NotesTabMixin, StatsTabMixin):
    def __init__(self, page: ft.Page, store: Store):
        self.page = page
        self.store = store
        self.tab_frames = {}

    async def start(self):
        await self.init_shell()

    def refresh_option_dependents(self):
        """Called after the todo-options list (subjects) changes so every
        dropdown that offers those subjects as choices stays in sync."""
        opts = self.store.get_todo_options()
        if hasattr(self, "add_subject"):
            self.add_subject.options = _dd_opts(opts)
            if self.add_subject.value not in opts and opts:
                self.add_subject.value = opts[0]
            self.add_subject.update()
        if hasattr(self, "note_subject_dd"):
            self.note_subject_dd.options = _dd_opts(opts)
            if self.note_subject_dd.value not in opts and opts:
                self.note_subject_dd.value = opts[0]
            self.note_subject_dd.update()
        if hasattr(self, "note_filter_subject_dd"):
            self.note_filter_subject_dd.options = _dd_opts(["全部科目"] + opts)
            self.note_filter_subject_dd.update()
