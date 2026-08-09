---
description: Pre-commit gate for study-tracker — run tests plus an independent review before committing
argument-hint: [可選：想特別提醒審查者注意的地方]
---

在 `study-tracker/` 專案中，對目前尚未 commit 的變更做出貨前檢查。

1. 執行 `git status` 與 `git diff`（在 `study-tracker` repo 內）確認目前改動範圍。
2. 執行 `.venv/Scripts/python -m pytest tests/ -q`（沒有 venv 就用 `python -m pytest tests/ -q`），記錄結果。
3. 用 Agent 工具呼叫 `reviewer` subagent（前景執行），對目前的 diff 做獨立審查；若使用者有附加提醒事項請一併附上：$ARGUMENTS。審查者發現問題會直接修正並重跑測試。
4. 若改動牽動 UI 檔案（`app/tab_*.py`、`app/shell.py`、`app/widgets.py`、`app/theme.py`），提醒使用者仍需手動用 `run` skill 或 `python main.py` 確認畫面，不能只靠測試。
5. 給出「是否可以 commit」的結論：測試是否全過、審查是否有未解決的疑慮或已修正的問題清單。
