---
description: Plan → implement → review a bug fix for study-tracker, with a regression test
argument-hint: [bug 描述或重現步驟]
---

在 `study-tracker/` 專案中，用「規劃 → 實作 → 審查」三階段修這個 bug：$ARGUMENTS

1. 用 Agent 工具呼叫 `planner` subagent（前景執行），請它讀相關程式碼、找出根因，並提出最小修正方案（不寫程式碼，只回傳根因分析與修正計畫）。把根因與計畫簡短呈現給使用者。
2. 用 Agent 工具呼叫 `implementer` subagent（前景執行），依計畫修正，並在 `tests/` 補一個能重現此 bug 的迴歸測試（regression test），跑 `pytest tests/` 確認通過。
3. 用 Agent 工具呼叫 `reviewer` subagent（前景執行），對這次的 diff 做獨立審查，確認修正沒有引入新問題、迴歸測試確實涵蓋原本的 bug 情境；發現問題會直接修正並重跑測試。
4. 若改動牽動 UI 檔案，提醒使用者之後要手動用 `run` skill 或 `python main.py` 確認畫面。
5. 給使用者一段簡短總結：根因、修正內容、新增的迴歸測試、最終測試結果。
