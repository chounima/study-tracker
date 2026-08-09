---
description: Plan → implement → review a new feature or UPGRADE_PLAN.md backlog item for study-tracker
argument-hint: [UPGRADE_PLAN.md 項目編號或功能描述]
---

在 `study-tracker/` 專案中，用「規劃 → 實作 → 審查」三階段完成以下功能：$ARGUMENTS

1. 若輸入是 `UPGRADE_PLAN.md` 裡的項目編號，先讀該檔案取出對應項目的現況、做法、影響檔案、風險描述；若是自由文字描述，直接當作需求使用。
2. 用 Agent 工具呼叫 `planner` subagent（前景執行，因為下一步需要它的結果），附上需求與相關檔案脈絡，取得具體實作計畫。planner 不寫程式碼，只回傳計畫。把計畫簡短呈現給使用者。
3. 用 Agent 工具呼叫 `implementer` subagent（前景執行），把上一步的計畫交給它執行：寫程式碼、補/改測試、跑 `pytest tests/`。
4. 用 Agent 工具呼叫 `reviewer` subagent（前景執行），對這次的 diff 做獨立審查；審查者發現問題會直接修正並重跑測試。
5. 若這次改動牽動 UI（`app/tab_*.py`、`app/shell.py`、`app/widgets.py`、`app/theme.py`），提醒使用者這個環境的截圖工具不可靠，之後要手動用 `run` skill 或 `python main.py` 檢查畫面。
6. 若此功能對應 `UPGRADE_PLAN.md` 的項目，把該列狀態更新為「✅ 已完成」並比照現有格式補一行實作備註。
7. 給使用者一段簡短總結：改了哪些檔案、測試結果、審查發現與處理方式。
