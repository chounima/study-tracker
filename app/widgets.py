import tkinter as tk
from tkinter import font as tkfont


class WidgetHelpersMixin:
    # ── button helpers ────────────────────────────────────────────────────────
    def _nav_btn(self, parent, text, command):
        return tk.Button(
            parent, text=text, command=command,
            bg=self.card, fg=self.text,
            bd=1, relief="solid", font=self.font_ui,
            padx=10, pady=5, cursor="hand2",
            highlightthickness=0,
            activebackground=self.strip_bg, activeforeground=self.text,
        )

    def _btn(self, parent, text, command, bg, fg, border=False):
        is_accent = (bg == self.accent)
        is_warn   = (fg == self.warn)
        if is_accent:
            abg, afg = self.accent_lt, "white"
        elif is_warn:
            abg, afg = self.warn, "white"
        else:
            abg, afg = self.border, self.text
        return tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, font=self.font_ui,
            bd=1 if border else 0,
            relief="solid" if border else "flat",
            padx=14, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=abg,
            activeforeground=afg,
        )

    # ── custom dropdown (no ttk.Combobox) ────────────────────────────────────
    def _make_dropdown(self, parent, values, initial="", **pack_kw):
        vals  = list(values)
        init  = initial if initial else (vals[0] if vals else "")
        var   = tk.StringVar(value=init)
        _ref  = [None]  # popup reference

        outer = tk.Frame(
            parent, bg=self.input_bg,
            highlightbackground=self.border, highlightthickness=1,
        )

        disp = tk.Button(
            outer, textvariable=var,
            anchor="w", bg=self.input_bg, fg=self.text,
            relief="flat", bd=0, font=self.font_ui,
            padx=10, pady=5, cursor="hand2",
            highlightthickness=0,
            activebackground=self.strip_bg, activeforeground=self.text,
        )
        disp.pack(side="left", fill="x", expand=True)

        arrow = tk.Label(outer, text="▾", bg=self.input_bg, fg=self.muted,
                         font=(self.font_sm[0], max(8, int(11 * self.ui_scale_factor))), padx=8, cursor="hand2")
        arrow.pack(side="right")

        def _open():
            if _ref[0] and _ref[0].winfo_exists():
                _ref[0].destroy()
                _ref[0] = None
                return

            popup = tk.Toplevel(self.root)
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)
            _ref[0] = popup

            outer.update_idletasks()
            pw = max(outer.winfo_width(), 120)
            margin = 8
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()

            # Size the popup to fit every item unless that would run off the screen —
            # only then does it shrink to the available space and gain a scrollbar.
            row_h = tkfont.Font(font=self.font_ui).metrics("linespace") + 6
            content_h = len(vals) * row_h + 6

            anchor_top = outer.winfo_rooty()
            below_y = anchor_top + outer.winfo_height()
            space_below = screen_h - margin - below_y
            space_above = anchor_top - margin
            if content_h <= space_below or space_below >= space_above:
                py = below_y
                ph = min(content_h, max(row_h, space_below))
            else:
                ph = min(content_h, max(row_h, space_above))
                py = anchor_top - ph

            px = outer.winfo_rootx()
            px = max(margin, min(px, screen_w - pw - margin))
            popup.geometry(f"{pw}x{int(ph)}+{int(px)}+{int(py)}")

            card = tk.Frame(popup, bg=self.card, bd=1, relief="solid")
            card.pack(fill="both", expand=True)

            list_wrap = tk.Frame(card, bg=self.card)
            list_wrap.pack(fill="both", expand=True, padx=2, pady=2)

            lb = tk.Listbox(
                list_wrap, font=self.font_ui,
                bg=self.card, fg=self.text,
                selectbackground=self.accent, selectforeground="white",
                activestyle="none", relief="flat", bd=0, highlightthickness=0,
            )
            if content_h > ph + 1:
                sb = tk.Scrollbar(list_wrap, orient="vertical", command=lb.yview)
                lb.configure(yscrollcommand=sb.set)
                sb.pack(side="right", fill="y")
            lb.pack(side="left", fill="both", expand=True)

            for v in vals:
                lb.insert("end", v)

            try:
                idx = vals.index(var.get())
                lb.selection_set(idx)
                lb.activate(idx)
                lb.see(idx)
            except ValueError:
                pass

            def _pick(_=None):
                sel = lb.curselection()
                if sel:
                    var.set(vals[sel[0]])
                if popup.winfo_exists():
                    popup.destroy()
                _ref[0] = None

            def _blur(_=None):
                _p = popup
                outer.after(80, lambda: _p.destroy() if _p.winfo_exists() else None)
                _ref[0] = None

            lb.bind("<ButtonRelease-1>", _pick)
            lb.bind("<Return>", _pick)
            popup.bind("<FocusOut>", _blur)
            popup.bind("<Escape>", lambda _: popup.destroy() if popup.winfo_exists() else None)
            lb.focus_set()

        disp.config(command=_open)
        arrow.bind("<Button-1>", lambda _: _open())

        if pack_kw:
            outer.pack(**pack_kw)

        outer._var  = var
        outer._vals = vals
        outer.get   = var.get
        outer.set   = var.set

        def _bind_key(seq, func, add=""):
            disp.bind(seq, func, add)
        outer.bind      = _bind_key
        outer.focus_set = disp.focus_set

        return outer

    # ── undo toast ────────────────────────────────────────────────────────────
    def _show_undo_toast(self, message, on_undo):
        self._dismiss_undo_toast()

        toast = tk.Frame(self.root, bg=self.text, bd=0)

        tk.Label(
            toast, text=message, fg=self.bg, bg=self.text,
            font=self.font_sm, padx=14, pady=10,
        ).pack(side="left")

        def _undo_clicked():
            self._dismiss_undo_toast()
            on_undo()

        tk.Button(
            toast, text="復原", command=_undo_clicked,
            bg=self.text, fg=self.accent_lt,
            bd=0, relief="flat", font=(self.font_sm[0], self.font_sm[1], "bold"),
            padx=14, pady=10, cursor="hand2",
            highlightthickness=0,
            activebackground=self.text, activeforeground=self.accent_lt,
        ).pack(side="left")

        toast.place(relx=0.5, rely=1.0, anchor="s", y=-14)
        self._undo_toast     = toast
        self._undo_after_id  = self.root.after(5000, self._dismiss_undo_toast)

    def _dismiss_undo_toast(self):
        after_id = getattr(self, "_undo_after_id", None)
        if after_id is not None:
            try:
                self.root.after_cancel(after_id)
            except Exception:
                pass
        toast = getattr(self, "_undo_toast", None)
        if toast is not None:
            try:
                toast.destroy()
            except Exception:
                pass
        self._undo_toast    = None
        self._undo_after_id = None

    # ── custom spin widget ────────────────────────────────────────────────────
    def _mk_spin(self, parent, var, values, bg, width=4):
        vals  = list(values)
        frame = tk.Frame(parent, bg=bg)
        frame.entry = None

        def step(delta):
            cur = var.get().strip()
            try:
                idx = vals.index(cur)
            except ValueError:
                idx = 0
            var.set(vals[max(0, min(len(vals) - 1, idx + delta))])

        for text, d in [("−", -1), (None, None), ("＋", 1)]:
            if text is None:
                entry = tk.Entry(
                    frame, textvariable=var, width=width,
                    font=self.font_md, bd=0, relief="flat",
                    highlightthickness=1, highlightcolor=self.accent, highlightbackground=self.border,
                    bg=self.input_bg, fg=self.text, insertbackground=self.text,
                    justify="center",
                )
                entry.pack(side="left", padx=1)
                frame.entry = entry
            else:
                tk.Button(
                    frame, text=text, command=lambda d=d: step(d),
                    bg=bg, fg=self.accent,
                    bd=0, relief="flat",
                    font=(self.font_md[0], self.font_md[1], "bold"),
                    padx=5, pady=2, cursor="hand2",
                    highlightthickness=0,
                    activebackground=self.strip_bg, activeforeground=self.accent,
                ).pack(side="left")
        return frame
