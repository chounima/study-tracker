# 專案升級計畫

本文件記錄 `study-tracker` 的 UI／資料輸入／顯示可改善項目，作為後續分階段實作的依據。現況是純手刻 Tkinter（未使用 `ttk`），下拉選單、Spinbox、日期選擇器、圖表都是自訂元件（見 [app/widgets.py](app/widgets.py)、[app/tab_todo.py](app/tab_todo.py)、[app/tab_stats.py](app/tab_stats.py)）。

---

## 分級總覽

| 項目 | 分類 | 預估工作量 | 優先度 | 狀態 |
|---|---|---|---|---|
| 1. 新增待辦列支援 Enter/Esc | 資料輸入 | 小 | 高 | ✅ 已完成 |
| 2. `tkcalendar` 改為必要依賴 | 資料輸入 | 小 | 高 | ✅ 已完成 |
| 3. 刪除待辦/錯題加上復原（undo） | 資料輸入 | 小～中 | 中 | ✅ 已完成 |
| 4. 統計「全部詳細項」改用 `ttk.Treeview` | 顯示 | 中 | 高 | ✅ 已完成 |
| 5. 到點提醒通知（`plyer`／`win10toast`） | 顯示／功能 | 中 | 中 | 待做 |
| 6. 讀書時數趨勢圖（`matplotlib` 嵌入） | 顯示 | 中～大 | 低 | 未做（維持計畫建議：先評估再排入） |
| 7. 全面換皮成 `ttkbootstrap`／`sv-ttk` | 視覺風格 | 大 | 低（可選） | 未做（維持計畫建議：先評估再排入） |

### 實作備註（2026-07-04）

- 項目 1、2、4 已實作並通過 `pytest tests/`，另用一支手動驗證腳本（直接呼叫 `app.add_custom_todo()`、`app._open_cal_picker()`、`app.detail_tree` 等）確認邏輯正確；GUI 有正常開出一個原生視窗（Windows 端可辨識標題與可見狀態），但此開發環境的螢幕截圖工具無法擷取到該視窗畫面（環境限制），建議實際使用時再手動確認一次視覺效果。
- 實作項目 1 時，額外發現並修正一個既有 bug：`app/tab_todo.py` 的 `_render_todo_edit_form()`／`_render_note_form()` 內的 `<Escape>` 綁定沒有 `return "break"`，導致按 Esc 取消編輯／備註後，事件會繼續冒泡到 [app/shell.py](app/shell.py) 的全域 `<Escape>`（關閉視窗），變成「取消編輯」會連帶把整個 App 關掉。已一併修正。
- 項目 2 移除 fallback 後，`requirements.txt` 已改標註為必要依賴，`app/app.py` 的 `main()` 會在啟動時檢查 `tkcalendar` 是否安裝，缺少時顯示錯誤訊息並拒絕啟動（而非執行到一半才壞）。
- 項目 3 已實作：`app/storage.py` 新增 `pop_todo_with_index`/`restore_todo_at`/`pop_note_with_index`/`restore_note_at` 純資料操作，`app/widgets.py` 新增 `_show_undo_toast`/`_dismiss_undo_toast`（置底浮動提示列，5 秒後自動消失），`app/tab_todo.py`/`app/tab_notes.py` 的刪除函式改為刪除後顯示可復原提示。`pytest tests/` 新增 8 個測試，全部（18 個）通過。審查階段發現並修正一個真實 bug：`_delete_todo` 的復原原本會用「復原當下」的 `self.todos`（會隨 `_switch_view_date` 換日期而指向不同清單物件），若使用者刪除後、5 秒內切換到別的日期再按復原，項目會被插入錯誤的日期清單；修正為在刪除當下記住該筆資料所屬的清單物件參照，復原時固定寫回同一個物件。UI 部分（toast 視覺、5 秒消失、實際復原互動）尚未手動驗證，建議之後用 `python main.py` 或 `run` skill 檢查一次畫面。

### 視窗大小 / DPI 縮放修正（2026-07-06）

- 使用者回報視窗預設太小、看不到全部功能，且下拉選單只顯示 3 個選項。追查後發現三個各自獨立的問題，皆已修正：
  1. **視窗開窗大小改依螢幕解析度比例計算**（`app/config.py` 新增 `WINDOW_WIDTH_RATIO`/`WINDOW_HEIGHT_RATIO`/`WINDOW_MIN/MAX_WIDTH/HEIGHT`，`app/shell.py` 套用），並讓 `ui_scale`（介面縮放設定）一併影響視窗floor/ceiling，避免使用者調高縮放後視窗仍是原本的固定像素大小。
  2. **`tk scaling` 被錯誤覆蓋成固定值的既有 bug**（`app/theme.py` `define_fonts`）：原本 `self.root.tk.call("tk","scaling", factor)` 會把 Tk 依實際螢幕 DPI 自動算出的縮放值直接覆蓋成 `ui_scale/100`（預設 100% 時等於 1.0），但 Tk 在 96 DPI 下的自然預設值其實是約 1.33；也就是說即使使用者從未動過「介面縮放」設定，文字也會比 Tk 原生預設小上一截，且完全不會隨螢幕實際 DPI 調整。修正為只在第一次呼叫時記錄 Tk 原生的 DPI 縮放值，之後永遠用「原生值 × ui_scale」相乘，而不是直接取代。
  3. **下拉選單彈出視窗只顯示約 3 項的 bug**（`app/widgets.py` `_make_dropdown`）：彈出視窗高度原本是 `min(項目數*28+6, 220)` 這種寫死的像素假設，跟實際字體渲染高度（尤其在 `ui_scale` 調高後）對不上，造成明明有十幾個選項卻只擠得下 3 個還沒有捲軸。改為用目前字體實際量測的行高計算內容高度，優先完整顯示所有項目，只有在超出可用螢幕空間時才裁切並自動加上捲軸；同時讓彈出視窗的座標不會超出螢幕左右/上下邊界。
  4. 另外修正幾處寫死字級（不隨 `ui_scale`縮放）的按鈕/標籤：分頁列主題色點按鈕（`app/shell.py`）、待辦「⚙」選項按鈕（`app/tab_todo.py`）、統計卡片大數字（`app/tab_stats.py`）、下拉選單的展開箭頭（`app/widgets.py`），現在都會跟著 `ui_scale_factor` 一起放大縮小。
  - `pytest tests/` 全部通過；另外用一支手動腳本模擬使用者目前存檔的設定（`ui_scale=200`、螢幕 1280×720）實際跑一次 `ExamPrepApp`，確認：`tk scaling` 從原本會被覆蓋成 `2.0` 改為 `2.656`（= Tk 原生 DPI 值 1.328 × 2.0）、視窗開到 `1240x640`（原本固定是 640x640 左右）、下拉選單在 15 個選項下彈出視窗高度隨字體實際大小算成 711px 完整顯示不截斷。
  - **後續建議**：既有 bug 修正後，「介面縮放」100% 時的文字已經比之前大了（回到 Tk 原生大小），使用者先前存檔的 `ui_scale=200`（很可能是為了補償這個 bug 才調到上限）現在可能會太大，建議之後打開「顯示設定」試著調回較低的百分比，看哪個數值最舒適。

---

## 1. 新增待辦列支援 Enter / Esc

- **現況**：[app/tab_todo.py](app/tab_todo.py) 的「新增」列（`add_strip`）只能滑鼠點「新增」按鈕；編輯表單（`_render_todo_edit_form`）已有綁 `<Return>`/`<Escape>`，新增列沒有。
- **做法**：在 `todo_combo`（下拉選單的 entry-like widget）與時數 Spinbox 綁 `<Return>` → 呼叫 `add_custom_todo()`。
- **影響檔案**：`app/tab_todo.py`
- **風險**：低，純增量行為。

## 2. `tkcalendar` 改為必要依賴

- **現況**：`requirements.txt` 把 `tkcalendar` 標成選用，缺少時退回 `_open_simple_date_picker`（陽春年/月/日 Spinbox），兩套邏輯要同時維護，體驗落差大。
- **做法**：拿掉 fallback 分支，`requirements.txt` 改為必要依賴；或至少在 README 提醒「強烈建議安裝」。
- **影響檔案**：`app/tab_todo.py`（`_open_cal_picker`、`_open_simple_date_picker`）、`requirements.txt`
- **取捨**：拿掉 fallback 後，若某台機器忘記裝套件，日期選擇功能會直接壞掉；需要在 `main()` 啟動時做依賴檢查並提示安裝，而不是靜默失敗。

## 3. 刪除待辦/錯題加上復原（undo）

- **現況**：待辦刪除（`_delete_todo`）與單筆錯題刪除是直接刪除、無確認、無復原；只有「清除全部錯題」有二次確認。
- **做法**：刪除後短暫顯示一個「已刪除，復原」的提示列（例如置底 Frame + 5 秒後消失），復原則把資料塞回原位置。
- **影響檔案**：`app/tab_todo.py`（`_delete_todo`）、`app/tab_notes.py`（`delete_note`）
- **風險**：中，需要額外狀態管理暫存被刪除的項目與其原始索引。

## 4. 統計「全部詳細項」改用 `ttk.Treeview`

- **現況**：[app/tab_stats.py](app/tab_stats.py) 的 `refresh_stats_detail()` 把每天每筆待辦都渲染成一組 `tk.Label`/`tk.Frame`，塞進可捲動 `Canvas`。資料量大時效能會下降，且無排序/篩選能力。
- **做法**：改用 `ttk.Treeview`（欄位：日期、時段、時間、項目、完成、時數、備註），原生支援排序、多選、更順的捲動；可搭配 `ttk.Style` 套用目前主題色。
- **影響檔案**：`app/tab_stats.py`
- **取捨**：`ttk.Treeview` 的樣式客製化不如純 `tk.Label` 自由（例如逐列不同顏色需要用 `tag_configure`），需要重新設計配色方式，但換來的效能與排序能力值得。
- **建議優先做**：這是目前投報率最高的一項。

## 5. 到點提醒通知

- **現況**：待辦有 `time_start`/`time_end`，但沒有主動提醒，使用者得自己盯著看。
- **做法**：`schedule_updates()`（[app/shell.py](app/shell.py)）每秒已經在跑，可以在裡面比對目前時間是否等於某筆未完成待辦的 `time_start`，觸發系統通知（`plyer.notification.notify` 或 Windows 專用 `win10toast`）。
- **影響檔案**：`app/shell.py`、`requirements.txt`（新增 `plyer` 或 `win10toast`）
- **取捨**：`win10toast` 僅支援 Windows（本專案本來就是 Windows 專用 exe，可接受）；`plyer` 跨平台但依賴較重、部分功能在 Windows 上需要額外設定。建議選 `win10toast`。

## 6. 讀書時數趨勢圖

- **現況**：`refresh_study_chart()` 只畫「各科目累積已完成時數」的橫向長條圖，手繪在 `Canvas` 上，無法呈現「每週/每月變化趨勢」。
- **做法**：如果要做趨勢線圖，用 `matplotlib`（`FigureCanvasTkAgg` 嵌入 Tkinter）會比手刻 Canvas 圖表省力很多。
- **影響檔案**：`app/tab_stats.py`、`requirements.txt`（新增 `matplotlib`）
- **取捨**：`matplotlib` 會讓啟動變慢、PyInstaller 打包後的 exe 體積明顯變大（目前僅 22MB）。只有在確定需要「趨勢圖」這種複雜圖表時才值得做；目前的長條圖需求用手繪 Canvas 已經足夠。

## 7. 全面換皮成 `ttkbootstrap` / `sv-ttk`

- **現況**：主題系統靠 [app/theme.py](app/theme.py) + [app/config.py](app/config.py) 的 `THEMES` 字典手動幫每個 `tk.Button`/`tk.Frame` 上色，四套主題（light/dark/coffee/light_coffee）運作正常但維護成本高。
- **做法**：改用 `ttkbootstrap` 或 `sv-ttk` 提供現代化 `ttk` 主題，減少手動配色程式碼。
- **影響檔案**：幾乎所有 `app/*.py`（`_btn`、`_nav_btn`、`_make_dropdown`、`_mk_spin` 等自訂元件全部要重寫成 `ttk` 對應元件）
- **取捨**：改動範圍最大，且會失去目前「四色主題完全自訂」的彈性（`ttkbootstrap` 內建主題較固定，客製要另外寫 style）。只有在想要大改視覺風格時才建議做，且應該獨立成一個分支慢慢做，不要跟功能開發混在一起。

---

## 建議實施順序

1. 第一批（低風險、快速見效）：項目 1、2
2. 第二批（顯示體驗提升）：項目 4
3. 第三批（依需求選做）：項目 3、5
4. 長期／可選：項目 6、7（視覺與圖表大改，建議獨立評估後再排入）

---

## 備註

- 每項改動完成後記得跑 `pytest tests/` 確認 `app/storage.py` 的資料邏輯沒被牽動；UI 變更仍需 `python main.py` 手動驗證。
- 新增外部套件依賴前，先確認會不會影響 `pyinstaller --onefile` 打包後的 exe 體積與啟動速度（尤其是項目 6 的 `matplotlib`）。
