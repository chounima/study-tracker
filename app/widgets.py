import tkinter as tk


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
                         font=(self.font_sm[0], 11), padx=8, cursor="hand2")
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
            px = outer.winfo_rootx()
            py = outer.winfo_rooty() + outer.winfo_height()
            ph = min(len(vals) * 28 + 6, 220)
            popup.geometry(f"{pw}x{ph}+{px}+{py}")

            card = tk.Frame(popup, bg=self.card, bd=1, relief="solid")
            card.pack(fill="both", expand=True)

            lb = tk.Listbox(
                card, font=self.font_ui,
                bg=self.card, fg=self.text,
                selectbackground=self.accent, selectforeground="white",
                activestyle="none", relief="flat", bd=0, highlightthickness=0,
            )
            lb.pack(fill="both", expand=True, padx=2, pady=2)

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

    # ── custom spin widget ────────────────────────────────────────────────────
    def _mk_spin(self, parent, var, values, bg, width=4):
        vals  = list(values)
        frame = tk.Frame(parent, bg=bg)

        def step(delta):
            cur = var.get().strip()
            try:
                idx = vals.index(cur)
            except ValueError:
                idx = 0
            var.set(vals[max(0, min(len(vals) - 1, idx + delta))])

        for text, d in [("−", -1), (None, None), ("＋", 1)]:
            if text is None:
                tk.Entry(
                    frame, textvariable=var, width=width,
                    font=self.font_md, bd=0, relief="flat",
                    highlightthickness=1, highlightcolor=self.accent, highlightbackground=self.border,
                    bg=self.input_bg, fg=self.text, insertbackground=self.text,
                    justify="center",
                ).pack(side="left", padx=1)
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
