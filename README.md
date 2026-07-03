# 國營企管衝刺管理工具說明

這份文件整理了整個 `study-tracker` 專案的目錄結構、資料格式與程式功能，方便之後維護與修改。程式碼已拆分為 [app/](app/) 底下的多個模組，取代原本單一巨檔的寫法。

---

## 1. 專案概述

這是一個使用 **Python + Tkinter** 製作的桌面應用程式（無外部 UI 框架），主要用途是：

- 管理每日讀書待辦事項（依時段：上午／下午／晚上）
- 紀錄與查詢錯題
- 統計讀書完成度與科目時數分布
- 顯示考試倒數計時
- 支援多種主題樣式與介面縮放
- 可打包成 Windows 執行檔（`.exe`）獨立發布

程式邏輯全部集中在單一類別 `ExamPrepApp`，但拆成多個 **mixin 模組**分檔存放（UI 建構、主題、資料存取、三個分頁各自獨立），最後在 [app/app.py](app/app.py) 用多重繼承組合成完整類別。這樣拆分不影響任何執行期行為，純粹是把原本 2200+ 行的單一檔案依職責分開，方便之後找程式碼、review diff。

---

## 2. 專案目錄結構

```
TestApp/
└── study-tracker/                  ← 專案根目錄（git repo）
    ├── main.py                     ← 程式進入點：python main.py 啟動
    ├── exam_tool.py                ← 相容轉接殼（舊的啟動方式仍可用，內容只是 import app.app.main）
    ├── app/                        ← 主程式套件
    │   ├── __init__.py
    │   ├── config.py                ← 常數：DEFAULT_EXAM_DATE / DEFAULT_PLAN / DEFAULT_SUBJECTS /
    │   │                              SECTION_COLORS / THEMES / 資料檔路徑
    │   ├── storage.py                ← DataMixin：資料讀寫、格式遷移、日期/倒數計算
    │   ├── theme.py                   ← ThemeMixin：主題色票套用、UI 縮放、重建介面
    │   ├── widgets.py                  ← WidgetHelpersMixin：自訂下拉選單、數值調整元件、按鈕樣式
    │   ├── shell.py                     ← ShellMixin：視窗骨架、標題列、倒數列、分頁列、生命週期
    │   ├── tab_todo.py                   ← TodoTabMixin：待辦分頁的建構與所有互動邏輯
    │   ├── tab_notes.py                   ← NotesTabMixin：錯題分頁的建構與所有互動邏輯
    │   ├── tab_stats.py                    ← StatsTabMixin：統計分頁的建構與所有互動邏輯
    │   └── app.py                           ← 組合上述所有 mixin 成 `ExamPrepApp`，程式主 entry `main()`
    ├── tests/
    │   └── test_storage.py          ← `storage.py` 資料邏輯的單元測試（不依賴 tkinter GUI）
    ├── exam_progress.json          ← 使用者資料存檔（已 gitignore，內含個人讀書紀錄）
    ├── requirements.txt             ← 執行期相依套件（tkcalendar，選用）
    ├── requirements-dev.txt          ← 開發期相依套件（pytest、pyinstaller）
    ├── README.md                   ← 本說明文件
    ├── .gitignore
    ├── dist/
    │   └── study_tracker.exe       ← PyInstaller 打包出的 Windows 執行檔（約 22MB）
    └── .venv/                      ← 虛擬環境
```

### 備註

- `exam_progress.json` 已被 `.gitignore` 排除（因為是個人讀書資料），首次執行若檔案不存在，程式會自動建立預設結構。
- `dist/study_tracker.exe` 是已打包好的獨立執行檔（透過 PyInstaller，`build/` 與 `*.spec` 已被 gitignore，不會進版控）。之後重新打包請以 `main.py` 為進入點。
- git 歷史顯示此專案原名為「國考衝刺管理工具」，目前功能已擴充至含 DPI／UI 縮放設定等。
- 原本重複的 `venv/` 虛擬環境（與 `.venv/` 內容重複、皆為空環境）已移除，統一使用 `.venv/`。

---

## 3. 開發環境建置與執行方式

### 建立虛擬環境並安裝相依套件

```bash
cd study-tracker
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt -r requirements-dev.txt
```

- `requirements.txt`：執行程式所需（目前只有 `tkcalendar`，屬選用套件；若環境中缺少，日期選擇器會自動退回內建的簡易年/月/日選擇視窗 `_open_simple_date_picker`，主流程仍可正常使用）。
- `requirements-dev.txt`：額外開發用（`pytest` 跑測試、`pyinstaller` 打包 exe），已內含 `-r requirements.txt`。

### 執行程式

```bash
python main.py        # 建議方式
python exam_tool.py   # 舊路徑仍可用（相容轉接殼）
```

### 執行打包好的 exe

```
study-tracker/dist/study_tracker.exe
```

### 重新打包 exe

```bash
pyinstaller --onefile --noconsole --name study_tracker main.py
```

### 執行測試

```bash
pytest tests/
```

測試涵蓋 `app/storage.py` 的資料讀寫、舊格式遷移（`migrate_legacy_todos`／`normalize_notes`）、時間欄位補值（`fill_missing_todo_times`）等邏輯，不需要開啟 GUI 視窗即可執行。UI（tkinter 互動）部分目前不在自動化測試範圍內，仍需手動啟動程式驗證。

---

## 4. 程式架構

### 4.1 入口與啟動流程

[main.py](main.py)：

```python
from app.app import main

if __name__ == "__main__":
    main()
```

[app/app.py](app/app.py) 的 `main()`：

```python
def main():
    # DPI awareness 設定 ...
    root = tk.Tk()
    app = ExamPrepApp(root)
    root.mainloop()
```

`ExamPrepApp.__init__`（定義在 [app/shell.py](app/shell.py) 的 `ShellMixin` 中）依序執行：

1. 設定視窗（無邊框標題列、置頂、DPI 感知、依螢幕大小置中）
2. `load_data()` 讀取 `exam_progress.json`（或建立預設資料）
3. `ensure_today_plan()` 確保今天有預設待辦
4. `define_colors()` 依主題設定顏色與字型
5. `build_ui()` 建立標題列／倒數列／分頁列／三個分頁內容
6. `bind_window_events()` 綁定拖曳視窗、Esc 關閉
7. `refresh_all()` 刷新所有畫面資料
8. `schedule_updates()` 啟動每秒一次的計時器（更新倒數、偵測跨日）

### 4.2 唯一類別：`ExamPrepApp`（由多個 mixin 組成）

所有功能仍集中在同一個類別 `ExamPrepApp` 中（沒有其他自訂類別），但依職責拆到不同檔案，最後在 [app/app.py](app/app.py) 用多重繼承組合：

```python
class ExamPrepApp(
    ShellMixin,          # app/shell.py   — 視窗骨架、標題列、倒數列、分頁列、生命週期
    ThemeMixin,          # app/theme.py   — 主題色票、UI 縮放、重建介面
    DataMixin,           # app/storage.py — 資料讀寫、格式遷移、日期/倒數計算
    WidgetHelpersMixin,  # app/widgets.py — 自訂下拉選單、數值調整元件、按鈕樣式
    TodoTabMixin,        # app/tab_todo.py  — 待辦分頁
    NotesTabMixin,       # app/tab_notes.py — 錯題分頁
    StatsTabMixin,       # app/tab_stats.py — 統計分頁
):
    def build_ui(self):
        ...
```

所有 mixin 方法都透過 `self.xxx`（顏色、字型、各種 widget 參照、`self.data`）互相共用狀態，跟原本單一類別時完全一樣，只是搬到不同檔案，方法名稱與行為都沒有改變。

---

## 5. 資料結構（`exam_progress.json`）

```json
{
  "settings": {
    "exam_date": "2026-10-18",
    "todo_options": ["企業管理", "經濟學", "法學", "國英", "歷屆題"],
    "title": "國營企管衝刺管理工具",
    "theme": "light",
    "ui_scale": 100
  },
  "todos_by_date": {
    "2026-07-01": [
      {
        "id": "1234567890企業管理",
        "section": "上午",
        "time_start": "08:30",
        "time_end": "10:30",
        "text": "企業管理",
        "done": false,
        "date": "2026-07-01",
        "note": ""
      }
    ]
  },
  "notes": [],
  "study_logs": []
}
```

### 5.1 `settings`

| 欄位 | 說明 |
|---|---|
| `exam_date` | 考試日期，`YYYY-MM-DD`，預設為 `DEFAULT_EXAM_DATE = "2026-10-18"` |
| `todo_options` | 待辦「項目」下拉選單的可選科目清單，可在「⚙ 管理待辦選項」中新增/刪除 |
| `title` | 標題列文字，可點 ✎ 編輯 |
| `theme` | `light` / `dark` / `coffee` / `light_coffee` 其中之一 |
| `ui_scale` | 介面縮放百分比，60–200，可在「設定」對話框調整 |

### 5.2 `todos_by_date`

以日期字串（`YYYY-MM-DD`）為 key，值是當天的待辦事項陣列。每一筆待辦欄位：

| 欄位 | 說明 |
|---|---|
| `id` | 唯一識別碼（`time.time_ns()` 產生） |
| `section` | 時段分類：`上午` / `下午` / `晚上` / `今日`（依開始時間自動推算，見 `_infer_section`） |
| `time_start` / `time_end` | 開始／結束時間，`HH:MM` |
| `text` | 項目名稱（通常對應某個科目） |
| `done` | 是否完成 |
| `date` | 所屬日期（與外層 key 相同） |
| `note` | 完成後可附加的備註（選填） |

舊版資料格式（單一 `time` 欄位、無 `todos_by_date` 分日期）會由 `migrate_legacy_todos()` 自動轉換；缺少 `time_start`/`time_end` 的舊資料會由 `fill_missing_todo_times()` 補齊。

### 5.3 `notes`（錯題本）

| 欄位 | 說明 |
|---|---|
| `date` | `M/D` 格式的新增日期 |
| `subject` | 科目 |
| `question` | 題目 |
| `answer` | 答案 |
| `reason` | 錯誤原因（選填） |

舊格式（純字串、或使用 `wrong` 欄位而非 `question`）會由 `normalize_notes()` 自動轉換相容。

### 5.4 `study_logs`

資料結構中預留的欄位，目前程式**沒有任何地方寫入或讀取其內容**（僅在 `load_data`/`save_data` 中原樣保存），是尚未使用的保留欄位。

---

## 6. UI 分頁與功能

程式視窗由上到下為：標題列 → 考試倒數列 → 分頁列（待辦／錯題／統計）→ 對應分頁內容。

### 6.1 待辦頁（`todo`）

功能：
- 依日期切換檢視（上一天／下一天／回今日／日曆選取），切換到未來且該日無資料時，會自動帶入前一天的項目作為範本（`_switch_view_date(carry_forward=True)`）
- 依時段分組顯示（上午／下午／晚上／今日），並有顏色標示（`SECTION_COLORS`）
- 勾選完成狀態，即時更新完成率進度條
- 新增自訂待辦（起始時間 + 時數 → 自動算結束時間、自動推斷時段）
- 就地編輯待辦時間／項目（`_render_todo_edit_form`）
- 幫已完成事項加註備註（📝，`_render_note_form`）
- 刪除待辦
- 「⚙」管理待辦選項清單（新增／刪除科目選項）

關鍵方法：`build_tab_todo()`、`render_todos()`、`_render_todo_item()`、`_render_todo_edit_form()`、`_render_note_form()`、`add_custom_todo()`、`_on_todo_check()`、`_delete_todo()`、`open_todo_options_manager()`、`_switch_view_date()`、`_infer_section()`

### 6.2 錯題頁（`notes`）

功能：
- 「＋ 新增」模式：填科目／題目／答案／原因，新增錯題卡片
- 「🔍 查詢」模式：關鍵字搜尋 + 依科目 / 時段（今天／本週／本月）篩選
- 清除全部錯題（需二次確認）
- 刪除單筆錯題

關鍵方法：`build_tab_notes()`、`add_note()`、`refresh_notes()`、`search_notes()`、`clear_note_search()`、`delete_note()`、`switch_notes_mode()`、`_render_note_card()`、`_subject_badge_color()`

### 6.3 統計頁（`stats`）

兩種檢視模式：

- **📊 讀書統計**：三張卡片（今日完成率／本週完成率／累積讀書天數）+ 依科目加總「已完成」時數的橫向長條圖（`refresh_study_chart`，只計算 `done=true` 且有 `time_start`/`time_end` 的項目）
- **🗓 全部詳細項**：依日期列出所有歷史待辦（含完成狀態、時段、時數、備註），並在底部彙總總時數與總天數（`refresh_stats_detail`）

關鍵方法：`build_tab_stats()`、`switch_stats_mode()`、`refresh_stats()`、`refresh_stats_detail()`、`refresh_study_chart()`、`get_study_days()`

---

## 7. 其他重要模組

### 7.1 資料載入與儲存（[app/storage.py](app/storage.py)）

- `load_data()`：讀取 JSON，補上預設結構，並對舊格式做遷移（`migrate_legacy_todos`／`normalize_notes`）
- `save_data()`：以「寫暫存檔 + `os.replace()`」方式原子性寫回 JSON，避免中途寫壞資料；同時更新標題列的「已儲存 HH:MM:SS」狀態文字
- `ensure_today_plan()`：確保今天存在待辦清單，若當天為空則帶入 `DEFAULT_PLAN` 作為預設排程
- `fill_missing_todo_times()`：補齊舊資料缺少的 `time_start`/`time_end`

### 7.2 日期與倒數計時（[app/storage.py](app/storage.py) ＋ [app/shell.py](app/shell.py)）

- `get_today_key()` / `refresh_day_state()`：偵測系統日期是否跨天，跨天時自動重建今日待辦
- `update_exam_date()` / `get_days_left()` / `format_countdown()` / `refresh_countdown()`：考試日期輸入驗證與倒數天數/時分秒顯示
- `schedule_updates()`：每 1000ms 呼叫一次自己，驅動倒數與跨日偵測（`root.after`）

### 7.3 主題系統（[app/theme.py](app/theme.py) ＋ [app/config.py](app/config.py)）

主題設定集中在模組層級的 `THEMES` 字典，目前包含四種：`light`（淺色）／`dark`（深色）／`coffee`（咖啡）／`light_coffee`（淺咖啡）。每個主題定義背景、卡片、邊框、文字、強調色等一整組色票。

切換主題（標題列右側色點按鈕）會呼叫 `switch_theme()` → 更新設定並整個 `rebuild_ui()`（銷毀所有 widget 後依新主題重建，並保留目前所在分頁與檢視日期）。

新增主題只需在 `THEMES` 增加一組 key，UI 會自動產生對應的色點按鈕（`build_titlebar` 中以迴圈產生）。

### 7.4 自訂下拉選單與數值調整元件（[app/widgets.py](app/widgets.py)）

沒有使用 `ttk.Combobox`／`ttk.Spinbox`，而是自行以 `Toplevel` + `Listbox` 實作：

- `_make_dropdown()`：點擊後彈出浮動清單視窗，選取後關閉並回填文字（供「項目」欄位、篩選器等使用）
- `_mk_spin()`：左右按鈕 + 可輸入框，在固定選項清單中前後移動（供時／分／時數欄位使用）

若之後要換成原生 `ttk` 元件，這兩段是最先要處理的地方。

### 7.5 顯示設定（[app/shell.py](app/shell.py)）

「設定」按鈕開啟的對話框可調整介面縮放（60%–200%），對應 `define_fonts()`（依比例縮放各字級）與 `open_display_settings()`；套用後同樣會觸發 `rebuild_ui()`。

---

## 8. 預設內容（模組層級常數）

| 常數 | 內容 |
|---|---|
| `DEFAULT_EXAM_DATE` | `"2026-10-18"` |
| `DEFAULT_SUBJECTS` | 企業管理／經濟學／法學／國英／歷屆題 |
| `DEFAULT_PLAN` | 5 筆預設排程（上午企業管理、下午經濟學、晚上歷屆題／法學／國英），首次開啟或當天無資料時自動帶入 |
| `SECTION_COLORS` | 上午／下午／晚上／今日 各自的標示色 |
| `THEMES` | 四組主題色票（見 7.3） |

---

## 9. 常見修改點速查

| 想改什麼 | 要動的檔案 / 方法 |
|---|---|
| 新增／修改科目 | [app/config.py](app/config.py) 的 `DEFAULT_SUBJECTS`、`DEFAULT_PLAN`；[app/tab_notes.py](app/tab_notes.py) 的 `_subject_badge_color()`（若要對應顏色） |
| 改變時段配色 | [app/config.py](app/config.py) 的 `SECTION_COLORS` |
| 改變 UI 版型 | [app/app.py](app/app.py) 的 `build_ui()`；各分頁的 `build_tab_todo()` / `build_tab_notes()` / `build_tab_stats()` |
| 改變資料儲存邏輯 | [app/storage.py](app/storage.py) 的 `load_data()`、`save_data()`、`ensure_today_plan()` |
| 改變統計／圖表方式 | [app/tab_stats.py](app/tab_stats.py) 的 `refresh_stats()`、`refresh_stats_detail()`、`refresh_study_chart()` |
| 新增主題 | [app/config.py](app/config.py) 的 `THEMES`；[app/theme.py](app/theme.py) 的 `define_colors()`、`switch_theme()` |
| 調整介面縮放邏輯 | [app/theme.py](app/theme.py) 的 `define_fonts()`；[app/shell.py](app/shell.py) 的 `open_display_settings()` |
| 新增資料邏輯的測試 | [tests/test_storage.py](tests/test_storage.py)，用 `StubApp(DataMixin)` 不啟動 GUI 直接測試 |
| 重新打包 exe | `pyinstaller --onefile --noconsole --name study_tracker main.py`，輸出到 `dist/`（`build/`、`*.spec` 不會進版控） |

---

## 10. 維護建議

- 新增功能建議先找到對應的 mixin 檔案（見第 2 節目錄結構）再改，不要跨檔案散落邏輯；如果新功能同時牽涉多個分頁，才考慮要不要新增獨立模組。
- 新增頁籤請遵循現有 `build_tab_xxx()` + `tab_frames` + `switch_tab()` 的模式，並在 [app/app.py](app/app.py) 把新的 Mixin 加進 `ExamPrepApp` 的繼承列表、在 `build_ui()` 裡呼叫。
- 資料格式變更時，務必同步更新 [app/storage.py](app/storage.py) 的 `load_data()` / `save_data()`，並考慮舊資料相容性（參考 `migrate_legacy_todos()` / `normalize_notes()` / `fill_missing_todo_times()` 的寫法），同時補上對應的 `tests/test_storage.py` 測試案例。
- 修改 `app/storage.py` 後，跑一次 `pytest tests/` 確認資料邏輯沒有壞掉；修改 UI 部分則用 `python main.py` 手動驗證。
