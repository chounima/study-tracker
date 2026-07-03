import tkinter as tk

from .shell import ShellMixin
from .storage import DataMixin
from .tab_notes import NotesTabMixin
from .tab_stats import StatsTabMixin
from .tab_todo import TodoTabMixin
from .theme import ThemeMixin
from .widgets import WidgetHelpersMixin


class ExamPrepApp(
    ShellMixin,
    ThemeMixin,
    DataMixin,
    WidgetHelpersMixin,
    TodoTabMixin,
    NotesTabMixin,
    StatsTabMixin,
):
    # ── build UI ──────────────────────────────────────────────────────────────
    def build_ui(self):
        self.build_titlebar()
        self.build_countdown_strip()
        self.build_tab_bar()
        self.build_tab_todo()
        self.build_tab_notes()
        self.build_tab_stats()
        self.switch_tab("todo")


def main():
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

    root = tk.Tk()
    app = ExamPrepApp(root)
    root.mainloop()
