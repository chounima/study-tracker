from .config import THEMES


class ThemeMixin:
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
