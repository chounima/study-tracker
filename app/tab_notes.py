import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox


class NotesTabMixin:
    # ── Tab 錯題 ──────────────────────────────────────────────────────────────
    def build_tab_notes(self):
        frame = tk.Frame(self.root, bg=self.bg)
        self.tab_frames["notes"] = frame

        mode_bar = tk.Frame(frame, bg=self.card)
        mode_bar.pack(fill="x")
        tk.Frame(frame, bg=self.border, height=1).pack(fill="x")

        self.note_add_btn = tk.Button(
            mode_bar, text="＋ 新增", font=self.font_sm,
            bd=0, relief="flat", padx=16, pady=10, cursor="hand2",
            command=lambda: self.switch_notes_mode("add"),
        )
        self.note_add_btn.pack(side="left")

        self.note_search_btn = tk.Button(
            mode_bar, text="🔍 查詢", font=self.font_sm,
            bd=0, relief="flat", padx=16, pady=10, cursor="hand2",
            command=lambda: self.switch_notes_mode("search"),
        )
        self.note_search_btn.pack(side="left")

        self.note_count_label = tk.Label(
            mode_bar, text="0 筆", fg=self.muted, bg=self.card, font=self.font_sm,
        )
        self.note_count_label.pack(side="right", padx=16)

        self.notes_form_area = tk.Frame(frame, bg=self.strip_bg)
        self.notes_form_area.pack(fill="x")
        tk.Frame(frame, bg=self.border, height=1).pack(fill="x")

        # add form
        self.notes_add_frame = tk.Frame(self.notes_form_area, bg=self.strip_bg)
        add_inner = tk.Frame(self.notes_add_frame, bg=self.strip_bg)
        add_inner.pack(fill="x", padx=16, pady=12)

        r0 = tk.Frame(add_inner, bg=self.strip_bg)
        r0.pack(fill="x", pady=(0, 6))
        tk.Label(r0, text="科目", fg=self.muted, bg=self.strip_bg,
                 font=self.font_sm, width=5, anchor="w").pack(side="left")
        opts0 = self._get_todo_options()
        self.note_subject_combo = self._make_dropdown(r0, opts0, initial=opts0[0] if opts0 else "")
        self.note_subject_combo.pack(side="left", fill="x", expand=True)

        self.note_question_var = tk.StringVar()
        self.note_answer_var   = tk.StringVar()
        self.note_reason_var   = tk.StringVar()
        self._note_form_row(add_inner, "題目", self.note_question_var)
        self._note_form_row(add_inner, "答案", self.note_answer_var)
        self._note_form_row(add_inner, "原因", self.note_reason_var)

        add_btn_row = tk.Frame(add_inner, bg=self.strip_bg)
        add_btn_row.pack(fill="x", pady=(10, 0))
        tk.Button(
            add_btn_row, text="新增錯題", command=self.add_note,
            bg=self.accent, fg="white",
            bd=0, relief="flat", font=self.font_sm,
            padx=16, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=self.accent_lt, activeforeground="white",
        ).pack(side="left")
        tk.Button(
            add_btn_row, text="清除全部", command=self.clear_notes,
            bg=self.strip_bg, fg=self.warn,
            bd=1, relief="solid", font=self.font_sm,
            padx=12, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=self.warn, activeforeground="white",
        ).pack(side="left", padx=(10, 0))

        # search form
        self.notes_search_frame = tk.Frame(self.notes_form_area, bg=self.strip_bg)
        srch_inner = tk.Frame(self.notes_search_frame, bg=self.strip_bg)
        srch_inner.pack(fill="x", padx=16, pady=12)

        kw_row = tk.Frame(srch_inner, bg=self.strip_bg)
        kw_row.pack(fill="x", pady=(0, 8))
        tk.Label(kw_row, text="關鍵字", fg=self.muted, bg=self.strip_bg,
                 font=self.font_sm, width=6, anchor="w").pack(side="left")
        self.note_search_var = tk.StringVar()
        kw_entry = tk.Entry(
            kw_row, textvariable=self.note_search_var,
            font=self.font_ui, bd=0, relief="flat",
            highlightthickness=1, highlightcolor=self.accent, highlightbackground=self.border,
            bg=self.input_bg, fg=self.text, insertbackground=self.text,
        )
        kw_entry.pack(side="left", fill="x", expand=True)
        kw_entry.bind("<Return>", lambda _: self.search_notes())

        filter_row = tk.Frame(srch_inner, bg=self.strip_bg)
        filter_row.pack(fill="x", pady=(0, 8))
        tk.Label(filter_row, text="科目", fg=self.muted, bg=self.strip_bg,
                 font=self.font_sm, width=6, anchor="w").pack(side="left")
        self._filter_subject_dd = self._make_dropdown(
            filter_row, ["全部科目"] + self._get_todo_options(), initial="全部科目")
        self._filter_subject_dd.pack(side="left", padx=(0, 12))

        tk.Label(filter_row, text="時段", fg=self.muted, bg=self.strip_bg,
                 font=self.font_sm).pack(side="left", padx=(0, 6))
        self._filter_period_dd = self._make_dropdown(
            filter_row, ["全部", "今天", "本週", "本月"], initial="全部")
        self._filter_period_dd.pack(side="left")

        srch_btn_row = tk.Frame(srch_inner, bg=self.strip_bg)
        srch_btn_row.pack(fill="x")
        tk.Button(
            srch_btn_row, text="搜尋", command=self.search_notes,
            bg=self.accent, fg="white",
            bd=0, relief="flat", font=self.font_sm,
            padx=16, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=self.accent_lt, activeforeground="white",
        ).pack(side="left")
        tk.Button(
            srch_btn_row, text="清除篩選", command=self.clear_note_search,
            bg=self.strip_bg, fg=self.muted,
            bd=1, relief="solid", font=self.font_sm,
            padx=10, pady=6, cursor="hand2",
            highlightthickness=0,
            activebackground=self.border, activeforeground=self.text,
        ).pack(side="left", padx=(8, 0))
        self.note_result_label = tk.Label(
            srch_btn_row, text="", fg=self.muted, bg=self.strip_bg, font=self.font_sm,
        )
        self.note_result_label.pack(side="right")

        cards_outer = tk.Frame(frame, bg=self.bg)
        cards_outer.pack(fill="both", expand=True)

        self.note_canvas = tk.Canvas(cards_outer, bg=self.bg, bd=0, highlightthickness=0)
        note_sb = tk.Scrollbar(cards_outer, orient="vertical", command=self.note_canvas.yview)
        self.note_canvas.configure(yscrollcommand=note_sb.set)
        note_sb.pack(side="right", fill="y")
        self.note_canvas.pack(side="left", fill="both", expand=True)

        self.note_cards_frame = tk.Frame(self.note_canvas, bg=self.bg)
        self._note_cards_win = self.note_canvas.create_window(
            (0, 0), window=self.note_cards_frame, anchor="nw")
        self.note_cards_frame.bind("<Configure>", lambda _: self.note_canvas.configure(
            scrollregion=self.note_canvas.bbox("all")))
        self.note_canvas.bind("<Configure>", lambda e: self.note_canvas.itemconfig(
            self._note_cards_win, width=e.width))
        self.note_canvas.bind("<MouseWheel>", lambda e: self.note_canvas.yview_scroll(
            -1 * (e.delta // 120), "units"))

        self.switch_notes_mode("add")

    def _note_form_row(self, parent, label, var):
        row = tk.Frame(parent, bg=self.strip_bg)
        row.pack(fill="x", pady=(0, 6))
        tk.Label(row, text=label, fg=self.muted, bg=self.strip_bg,
                 font=self.font_sm, width=5, anchor="w").pack(side="left")
        tk.Entry(
            row, textvariable=var,
            font=self.font_ui, bd=0, relief="flat",
            highlightthickness=1, highlightcolor=self.accent, highlightbackground=self.border,
            bg=self.input_bg, fg=self.text, insertbackground=self.text,
        ).pack(side="left", fill="x", expand=True)

    def add_note(self):
        subject  = self.note_subject_combo.get().strip()
        question = self.note_question_var.get().strip()
        answer   = self.note_answer_var.get().strip()
        reason   = self.note_reason_var.get().strip()
        if not subject or not question or not answer:
            messagebox.showerror("欄位不足", "請至少填入科目、題目、答案")
            return
        self.data["notes"].insert(0, {
            "date":     f"{date.today().month}/{date.today().day}",
            "subject":  subject,
            "question": question,
            "answer":   answer,
            "reason":   reason,
        })
        self.note_question_var.set("")
        self.note_answer_var.set("")
        self.note_reason_var.set("")
        self.save_data()
        self.refresh_notes()

    def clear_notes(self):
        if messagebox.askyesno("確認", "確定要清除所有錯題紀錄？"):
            self.data["notes"] = []
            self.save_data()
            self.refresh_notes()

    def refresh_notes(self, notes=None):
        if notes is None:
            notes = self.data["notes"]
        for child in self.note_cards_frame.winfo_children():
            child.destroy()
        self.note_count_label.config(text=f"{len(self.data['notes'])} 筆")
        valid = [n for n in notes if isinstance(n, dict)]
        if not valid:
            tk.Label(self.note_cards_frame,
                     text="（尚無符合的錯題紀錄）",
                     fg=self.muted, bg=self.bg, font=self.font_sm).pack(pady=24)
        else:
            for note in valid:
                self._render_note_card(note)
            tk.Frame(self.note_cards_frame, bg=self.bg, height=8).pack(fill="x")
        self.note_canvas.update_idletasks()
        self.note_canvas.configure(scrollregion=self.note_canvas.bbox("all"))

    def _render_note_card(self, note):
        card = tk.Frame(self.note_cards_frame, bg=self.card, bd=1, relief="solid")
        card.pack(fill="x", padx=10, pady=(8, 0))

        def on_scroll(e):
            self.note_canvas.yview_scroll(-1 * (e.delta // 120), "units")

        subject = note.get("subject", "")
        sbg     = self._subject_badge_color(subject)

        hdr = tk.Frame(card, bg=sbg if subject else self.strip_bg)
        hdr.pack(fill="x")
        hdr.bind("<MouseWheel>", on_scroll)

        if subject:
            slbl = tk.Label(hdr, text=f"  {subject}  ",
                            fg="white", bg=sbg, font=self.font_sm, pady=6)
            slbl.pack(side="left")
            slbl.bind("<MouseWheel>", on_scroll)

        dlbl = tk.Label(hdr, text=note.get("date", "--"),
                        fg="white" if subject else self.muted,
                        bg=sbg if subject else self.strip_bg,
                        font=self.font_sm, padx=8, pady=6)
        dlbl.pack(side="left")
        dlbl.bind("<MouseWheel>", on_scroll)

        del_btn = tk.Button(
            hdr, text="✕",
            fg="white" if subject else self.warn,
            bg=sbg if subject else self.strip_bg,
            bd=0, relief="flat", font=self.font_sm,
            padx=8, pady=6, cursor="hand2",
            command=lambda n=note: self.delete_note(n),
            activebackground=self.warn, activeforeground="white",
        )
        del_btn.pack(side="right")
        del_btn.bind("<MouseWheel>", on_scroll)

        body = tk.Frame(card, bg=self.card)
        body.pack(fill="x", padx=10, pady=(8, 10))
        body.bind("<MouseWheel>", on_scroll)

        question = note.get("question", note.get("wrong", ""))
        answer   = note.get("answer", "")
        reason   = note.get("reason", "")

        self._card_field(body, "Q", question, self.text,    bold=True, scroll_fn=on_scroll)
        self._card_field(body, "A", answer,   "#166534",    scroll_fn=on_scroll)
        if reason:
            self._card_field(body, "原", reason, self.muted, scroll_fn=on_scroll)

    def _card_field(self, parent, prefix, content, fg, bold=False, scroll_fn=None):
        row   = tk.Frame(parent, bg=self.card)
        row.pack(fill="x", pady=1)
        p_font = (self.font_sm[0], self.font_sm[1], "bold")
        c_font = (self.font_sm[0], self.font_sm[1], "bold") if bold else self.font_sm
        pfx = tk.Label(row, text=prefix, fg=self.accent, bg=self.card,
                       font=p_font, width=2, anchor="nw")
        pfx.pack(side="left", anchor="nw", pady=(1, 0))
        txt = tk.Label(row, text=content, fg=fg, bg=self.card,
                       font=c_font, anchor="w", wraplength=400, justify="left")
        txt.pack(side="left", fill="x", expand=True)
        if scroll_fn:
            for w in (row, pfx, txt):
                w.bind("<MouseWheel>", scroll_fn)

    def _subject_badge_color(self, subject):
        return {
            "企業管理": "#6366f1",
            "經濟學":   "#3b82f6",
            "法學":     "#8b5cf6",
            "國英":     "#22c55e",
            "歷屆題":   "#f59e0b",
        }.get(subject, self.muted)

    def switch_notes_mode(self, mode):
        self.notes_mode = mode
        if mode == "add":
            self.notes_search_frame.pack_forget()
            self.notes_add_frame.pack(fill="both", expand=True)
            self.note_add_btn.config(
                bg=self.card, fg=self.accent,
                font=(self.font_sm[0], self.font_sm[1], "bold"))
            self.note_search_btn.config(bg=self.card, fg=self.muted, font=self.font_sm)
        else:
            self.notes_add_frame.pack_forget()
            self.notes_search_frame.pack(fill="both", expand=True)
            self.note_search_btn.config(
                bg=self.card, fg=self.accent,
                font=(self.font_sm[0], self.font_sm[1], "bold"))
            self.note_add_btn.config(bg=self.card, fg=self.muted, font=self.font_sm)

    def search_notes(self):
        keyword        = self.note_search_var.get().strip().lower()
        subject_filter = self._filter_subject_dd.get()
        period_filter  = self._filter_period_dd.get()
        today          = date.today()
        results        = []
        for note in self.data["notes"]:
            if not isinstance(note, dict):
                continue
            if subject_filter != "全部科目" and note.get("subject") != subject_filter:
                continue
            if period_filter != "全部":
                note_date_str = note.get("date", "")
                try:
                    month, day = map(int, note_date_str.split("/"))
                    note_dt    = date(today.year, month, day)
                    if period_filter == "今天" and note_dt != today:
                        continue
                    elif period_filter == "本週":
                        if note_dt < today - timedelta(days=today.weekday()):
                            continue
                    elif period_filter == "本月" and note_dt.month != today.month:
                        continue
                except (ValueError, AttributeError):
                    pass
            if keyword:
                haystack = " ".join([
                    note.get("subject", ""),
                    note.get("question", note.get("wrong", "")),
                    note.get("answer", ""),
                    note.get("reason", ""),
                ]).lower()
                if keyword not in haystack:
                    continue
            results.append(note)
        self.note_result_label.config(text=f"找到 {len(results)} 筆")
        self.refresh_notes(results)

    def clear_note_search(self):
        self.note_search_var.set("")
        self._filter_subject_dd.set("全部科目")
        self._filter_period_dd.set("全部")
        self.note_result_label.config(text="")
        self.refresh_notes()

    def delete_note(self, note):
        try:
            self.data["notes"].remove(note)
        except ValueError:
            return
        self.save_data()
        if getattr(self, "notes_mode", "add") == "search":
            self.search_notes()
        else:
            self.refresh_notes()
