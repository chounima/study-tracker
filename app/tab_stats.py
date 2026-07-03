import tkinter as tk
from datetime import datetime, date


class StatsTabMixin:
    # ── Tab 統計 ──────────────────────────────────────────────────────────────
    def build_tab_stats(self):
        frame = tk.Frame(self.root, bg=self.bg)
        self.tab_frames["stats"] = frame

        mode_bar = tk.Frame(frame, bg=self.card)
        mode_bar.pack(fill="x")
        tk.Frame(frame, bg=self.border, height=1).pack(fill="x")

        self.stats_chart_btn = tk.Button(
            mode_bar, text="📊 讀書統計", font=self.font_sm,
            bd=0, relief="flat", padx=16, pady=10, cursor="hand2",
            command=lambda: self.switch_stats_mode("chart"),
        )
        self.stats_chart_btn.pack(side="left")

        self.stats_detail_btn = tk.Button(
            mode_bar, text="🗓 全部詳細項", font=self.font_sm,
            bd=0, relief="flat", padx=16, pady=10, cursor="hand2",
            command=lambda: self.switch_stats_mode("detail"),
        )
        self.stats_detail_btn.pack(side="left")

        cards = tk.Frame(frame, bg=self.bg)
        cards.pack(fill="x", padx=16, pady=(16, 10))
        for i in range(3):
            cards.grid_columnconfigure(i, weight=1)

        self.stat_today = self._stat_card(cards, "今日完成率", 0, accent=self.success)
        self.stat_week  = self._stat_card(cards, "本週完成率", 1, accent="#3b82f6")
        self.stat_days  = self._stat_card(cards, "累積讀書天數", 2, accent=self.accent)

        tk.Frame(frame, bg=self.border, height=1).pack(fill="x", padx=16)

        self.stats_detail = tk.Label(
            frame, text="", fg=self.muted, bg=self.bg,
            font=self.font_sm, justify="left", anchor="w",
        )
        self.stats_detail.pack(anchor="w", padx=20, pady=(6, 4))

        self.stats_chart_frame = tk.Frame(frame, bg=self.bg)
        chart_card = tk.Frame(self.stats_chart_frame, bg=self.card, bd=1, relief="solid")
        chart_card.pack(fill="both", expand=True, padx=16, pady=(4, 12))
        tk.Label(chart_card, text="根據已完成待辦自動計算",
                 fg=self.muted, bg=self.card, font=self.font_sm,
                 anchor="w", padx=14).pack(fill="x", pady=(8, 0))
        self.study_chart_canvas = tk.Canvas(chart_card, bg=self.card, bd=0, highlightthickness=0)
        self.study_chart_canvas.pack(fill="both", expand=True, pady=(4, 8))
        self.study_chart_canvas.bind("<Configure>", lambda _: self.refresh_study_chart())

        self.stats_detail_frame = tk.Frame(frame, bg=self.bg)
        detail_card = tk.Frame(self.stats_detail_frame, bg=self.card, bd=1, relief="solid")
        detail_card.pack(fill="both", expand=True, padx=16, pady=(4, 12))

        detail_hdr = tk.Frame(detail_card, bg=self.strip_bg)
        detail_hdr.pack(fill="x")
        self.detail_date_lbl = tk.Label(
            detail_hdr, text="全部記錄", fg=self.muted, bg=self.strip_bg, font=self.font_sm,
        )
        self.detail_date_lbl.pack(anchor="w", padx=10, pady=6)

        _dc_outer = tk.Frame(detail_card, bg=self.card)
        _dc_outer.pack(fill="both", expand=True)
        self.detail_canvas = tk.Canvas(_dc_outer, bg=self.card, bd=0, highlightthickness=0)
        _dc_sb = tk.Scrollbar(_dc_outer, orient="vertical", command=self.detail_canvas.yview)
        self.detail_canvas.configure(yscrollcommand=_dc_sb.set)
        _dc_sb.pack(side="right", fill="y")
        self.detail_canvas.pack(side="left", fill="both", expand=True)

        self.detail_items_frame = tk.Frame(self.detail_canvas, bg=self.card)
        self._dc_win = self.detail_canvas.create_window(
            (0, 0), window=self.detail_items_frame, anchor="nw")
        self.detail_items_frame.bind("<Configure>", lambda e: self.detail_canvas.configure(
            scrollregion=self.detail_canvas.bbox("all")))
        self.detail_canvas.bind("<Configure>", lambda e: self.detail_canvas.itemconfig(
            self._dc_win, width=e.width))
        self.detail_canvas.bind("<Enter>", lambda e: self.root.bind_all(
            "<MouseWheel>",
            lambda ev: self.detail_canvas.yview_scroll(-1 * (ev.delta // 120), "units")))
        self.detail_canvas.bind("<Leave>", lambda e: self.root.unbind_all("<MouseWheel>"))

        self.detail_summary_lbl = tk.Label(
            detail_card, text="", fg=self.muted, bg=self.card,
            font=self.font_sm, anchor="e", padx=10, pady=4,
        )
        self.detail_summary_lbl.pack(fill="x")

        self.switch_stats_mode("chart")

    def switch_stats_mode(self, mode):
        self.stats_mode = mode
        if mode == "chart":
            if hasattr(self, "stats_detail_frame"):
                self.stats_detail_frame.pack_forget()
            self.stats_chart_frame.pack(fill="both", expand=True)
            self.stats_chart_btn.config(
                bg=self.card, fg=self.accent,
                font=(self.font_sm[0], self.font_sm[1], "bold"))
            self.stats_detail_btn.config(bg=self.card, fg=self.muted, font=self.font_sm)
            self.root.after(50, self.refresh_study_chart)
        else:
            if hasattr(self, "stats_chart_frame"):
                self.stats_chart_frame.pack_forget()
            self.stats_detail_frame.pack(fill="both", expand=True)
            self.stats_detail_btn.config(
                bg=self.card, fg=self.accent,
                font=(self.font_sm[0], self.font_sm[1], "bold"))
            self.stats_chart_btn.config(bg=self.card, fg=self.muted, font=self.font_sm)
            self.refresh_stats_detail()

    def _stat_card(self, parent, title, col, accent=None):
        accent = accent or self.accent
        c = tk.Frame(parent, bg=self.card, bd=1, relief="solid")
        c.grid(row=0, column=col, padx=(0 if col == 0 else 8, 0), sticky="nsew")
        tk.Frame(c, bg=accent, height=3).pack(fill="x")
        tk.Label(c, text=title, fg=self.muted, bg=self.card, font=self.font_sm).pack(pady=(10, 4))
        lbl = tk.Label(c, text="--", fg=accent, bg=self.card,
                       font=("Microsoft JhengHei UI", 22, "bold"))
        lbl.pack(pady=(0, 12))
        return lbl

    def refresh_stats(self):
        total_today = len(self.todos)
        done_today  = sum(1 for t in self.todos if t.get("done"))
        today_rate  = int((done_today / total_today) * 100) if total_today else 0

        week_start   = date.today().toordinal() - 6
        weekly_total = weekly_done = 0
        for todo_date, items in self.data["todos_by_date"].items():
            try:
                if date.fromisoformat(todo_date).toordinal() < week_start:
                    continue
            except ValueError:
                continue
            weekly_total += len(items)
            weekly_done  += sum(1 for t in items if t.get("done"))

        weekly_rate = int((weekly_done / weekly_total) * 100) if weekly_total else 0
        cum_days    = self.get_study_days()

        self.stat_today.config(text=f"{today_rate}%")
        self.stat_week.config(text=f"{weekly_rate}%")
        self.stat_days.config(text=f"{cum_days} 天")
        self.stats_detail.config(
            text=f"今日完成：{done_today}/{total_today}　本週：{weekly_done}/{weekly_total}")
        self.refresh_stats_detail()

    def refresh_stats_detail(self):
        if not hasattr(self, "detail_items_frame"):
            return
        for child in self.detail_items_frame.winfo_children():
            child.destroy()

        all_dates = sorted(
            (k for k, v in self.data["todos_by_date"].items() if v), reverse=True)

        if not all_dates:
            tk.Label(self.detail_items_frame, text="（尚無任何待辦記錄）",
                     fg=self.muted, bg=self.card, font=self.font_sm).pack(pady=12)
            self.detail_summary_lbl.config(text="")
            self.detail_date_lbl.config(text="全部日期")
            return

        wdays   = ["一", "二", "三", "四", "五", "六", "日"]
        total_h = done_h = 0.0
        total_n = done_n = 0

        for date_key in all_dates:
            items = self.data["todos_by_date"].get(date_key, [])
            try:
                d        = date.fromisoformat(date_key)
                is_today = (date_key == self.today_key)
                dlabel   = f"{d.year}/{d.month:02d}/{d.day:02d}（週{wdays[d.weekday()]}）"
                if is_today:
                    dlabel += "  ◀ 今日"
            except ValueError:
                dlabel   = date_key
                is_today = False

            date_hdr = tk.Frame(self.detail_items_frame, bg=self.strip_bg)
            date_hdr.pack(fill="x", pady=(4, 0))
            tk.Label(
                date_hdr, text=dlabel,
                fg=self.accent if is_today else self.muted,
                bg=self.strip_bg,
                font=(self.font_sm[0], self.font_sm[1], "bold"),
                padx=8, pady=4,
            ).pack(side="left")

            for item in items:
                is_done = item.get("done", False)
                ts, te  = item.get("time_start", ""), item.get("time_end", "")
                note    = item.get("note", "").strip()
                hours   = 0.0
                if ts and te:
                    try:
                        hours = max(0.0, (
                            datetime.strptime(te, "%H:%M") - datetime.strptime(ts, "%H:%M")
                        ).total_seconds() / 3600)
                    except ValueError:
                        pass
                total_h += hours
                total_n += 1
                if is_done:
                    done_h += hours
                    done_n += 1

                row = tk.Frame(self.detail_items_frame, bg=self.card)
                row.pack(fill="x", padx=8, pady=(2, 0))
                tk.Label(row,
                         text="✓" if is_done else "◦",
                         fg=self.success if is_done else self.done_fg,
                         bg=self.card,
                         font=(self.font_sm[0], self.font_sm[1], "bold"), width=2).pack(side="left")
                tk.Label(row,
                         text=f"{ts}–{te}" if ts and te else "―",
                         fg=self.muted if not is_done else self.done_fg,
                         bg=self.card, font=self.font_sm, width=13, anchor="w").pack(side="left", padx=(2, 6))
                tk.Label(row, text=item.get("text", ""),
                         fg=self.done_fg if is_done else self.text,
                         bg=self.card, font=self.font_ui, anchor="w").pack(side="left", fill="x", expand=True)
                if hours > 0:
                    tk.Label(row, text=f"{hours:.1f}h",
                             fg=self.success if is_done else self.muted,
                             bg=self.card, font=self.font_sm, width=5, anchor="e").pack(side="right", padx=(0, 6))
                if note:
                    nr = tk.Frame(self.detail_items_frame, bg=self.card)
                    nr.pack(fill="x", padx=(28, 12), pady=(0, 2))
                    tk.Label(nr, text=note, fg=self.muted, bg=self.card,
                             font=self.font_sm, anchor="w", wraplength=340, justify="left").pack(side="left")

        tk.Frame(self.detail_items_frame, bg=self.border, height=1).pack(fill="x", padx=8, pady=(6, 0))
        parts = []
        if total_h > 0: parts.append(f"完成 {done_h:.1f}h / 共 {total_h:.1f}h")
        if total_n > 0: parts.append(f"事項 {done_n}/{total_n}")
        parts.append(f"共 {len(all_dates)} 天有記錄")
        self.detail_summary_lbl.config(text="   ".join(parts))
        self.detail_date_lbl.config(text=f"全部記錄 ({len(all_dates)} 日)")

        if hasattr(self, "detail_canvas"):
            self.detail_canvas.update_idletasks()
            self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox("all"))

    def refresh_study_chart(self):
        if not hasattr(self, "study_chart_canvas"):
            return
        canvas = self.study_chart_canvas
        totals = {}
        for items in self.data["todos_by_date"].values():
            for item in items:
                if not item.get("done"):
                    continue
                ts = item.get("time_start", item.get("time", ""))
                te = item.get("time_end", "")
                if not ts or not te:
                    continue
                try:
                    hours = (datetime.strptime(te, "%H:%M") - datetime.strptime(ts, "%H:%M")).total_seconds() / 3600
                    if hours <= 0:
                        continue
                except ValueError:
                    continue
                subj = item.get("text", "")
                opts = self._get_todo_options()
                if subj not in opts:
                    subj = next((s for s in opts if s in subj), subj)
                totals[subj] = totals.get(subj, 0.0) + hours

        canvas.delete("all")
        opts = self._get_todo_options()
        w    = canvas.winfo_width()
        if w < 60:
            return

        if not totals:
            canvas.create_text(w // 2, 40,
                               text="尚無讀書記錄（完成待辦後自動計算）",
                               fill=self.muted, font=self.font_sm, anchor="center")
            canvas.configure(height=80)
            return

        label_w = 72
        hours_w = 56
        bar_x0  = label_w + 6
        bar_x1  = w - hours_w - 8
        row_h   = 36
        pad_top = 14
        bar_h   = 14
        max_hrs = max(totals.values()) or 1
        total_h = sum(totals.values())

        for i, subj in enumerate(opts):
            hours   = totals.get(subj, 0.0)
            y_mid   = pad_top + i * row_h + row_h // 2
            y_top   = y_mid - bar_h // 2
            y_bot   = y_mid + bar_h // 2
            color   = self._subject_badge_color(subj)
            has_val = hours > 0

            canvas.create_text(label_w, y_mid, text=subj, anchor="e",
                               fill=self.text if has_val else self.muted,
                               font=(self.font_sm[0], self.font_sm[1], "bold" if has_val else ""))
            canvas.create_rectangle(bar_x0, y_top, bar_x1, y_bot, fill=self.strip_bg, outline="")

            if has_val:
                bw = max(6, int((hours / max_hrs) * (bar_x1 - bar_x0)))
                canvas.create_rectangle(bar_x0, y_top, bar_x0 + bw, y_bot, fill=color, outline="")
                if bw > 28:
                    canvas.create_text(bar_x0 + bw - 4, y_mid,
                                       text=f"{hours:.1f}h", anchor="e",
                                       fill="white",
                                       font=(self.font_sm[0], self.font_sm[1], "bold"))

            canvas.create_text(bar_x1 + 8, y_mid,
                               text=f"{hours:.1f} h", anchor="w",
                               fill=color if has_val else self.muted,
                               font=(self.font_sm[0], self.font_sm[1], "bold" if has_val else ""))

        y_sep = pad_top + len(opts) * row_h + 4
        canvas.create_line(bar_x0, y_sep, bar_x1, y_sep, fill=self.border)
        canvas.create_text(bar_x0, y_sep + 14,
                           text=f"共讀 {total_h:.1f} 小時", anchor="w",
                           fill=self.accent, font=(self.font_md[0], self.font_md[1], "bold"))
        canvas.create_text(bar_x1, y_sep + 14,
                           text=f"{self.get_study_days()} 天有記錄", anchor="e",
                           fill=self.muted, font=self.font_sm)
        canvas.configure(height=y_sep + 34)
