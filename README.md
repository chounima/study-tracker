# 國營企管衝刺管理工具說明

這份文件是為了方便之後維護與修改 [study-tracker/exam_tool.py](study-tracker/exam_tool.py) 而整理的。內容包含專案結構、資料格式、主要功能與常見修改點。

---

## 1. 專案概述

這是一個使用 Python + Tkinter 製作的桌面應用程式，主要用途是：

- 管理每日待辦事項
- 紀錄錯題
- 統計讀書完成度
- 顯示考試倒數
- 支援多種主題樣式

---

## 2. 檔案結構

- [study-tracker/exam_tool.py](study-tracker/exam_tool.py)
  - 主程式，包含 UI、資料邏輯、事件處理
- [study-tracker/exam_progress.json](study-tracker/exam_progress.json)
  - 儲存使用者資料的 JSON 檔
- [study-tracker/README.md](study-tracker/README.md)
  - 本說明文件

---

## 3. 主要程式架構

### 3.1 入口與啟動流程

程式最後一段為：

```python
if __name__ == "__main__":
    root = tk.Tk()
    app = ExamPrepApp(root)
    root.mainloop()
```

啟動時會依序進行：

1. 建立 Tkinter 視窗
2. 初始化 `ExamPrepApp`
3. 載入資料
4. 建立 UI
5. 綁定事件
6. 刷新畫面
7. 開始定時更新

### 3.2 主要類別

- `ExamPrepApp`
  - 全部功能都集中在這個類別中
  - 負責建立介面、處理互動、管理資料

---

## 4. 主要資料結構

資料會存到 [study-tracker/exam_progress.json](study-tracker/exam_progress.json) 中，格式大致如下：

```json
{
  "settings": {
    "exam_date": "2026-10-18",
    "todo_options": ["企業管理", "經濟學", "法學", "國英", "歷屆題"],
    "title": "國營企管衝刺管理工具",
    "theme": "light"
  },
  "todos_by_date": {
    "2026-07-01": [
      {
        "id": "...",
        "section": "上午",
        "time_start": "08:30",
        "time_end": "10:30",
        "text": "企業管理",
        "done": false,
        "date": "2026-07-01"
      }
    ]
  },
  "notes": [],
  "study_logs": []
}
```

### 4.1 每一筆待辦項目的欄位

- `id`: 唯一識別碼
- `section`: 時段分類，例如「上午」、「下午」、「晚上」
- `time_start`: 開始時間
- `time_end`: 結束時間
- `text`: 項目名稱
- `done`: 是否完成
- `date`: 所屬日期
- `note`: 備註（可選）

### 4.2 錯題資料欄位

- `date`: 日期
- `subject`: 科目
- `question`: 題目
- `answer`: 答案
- `reason`: 原因

---

## 5. UI 分頁與功能

### 5.1 待辦頁（todo）

主要功能：

- 切換日期
- 查看某日待辦清單
- 勾選完成狀態
- 新增自訂待辦
- 編輯待辦時間與內容
- 新增備註
- 刪除待辦
- 管理待辦選項

關鍵方法：

- `build_tab_todo()`
- `render_todos()`
- `_render_todo_item()`
- `_render_todo_edit_form()`
- `_render_note_form()`
- `add_custom_todo()`
- `_on_todo_check()`
- `open_todo_options_manager()`

### 5.2 錯題頁（notes）

主要功能：

- 新增錯題
- 搜尋錯題
- 依科目或時間篩選
- 刪除錯題

關鍵方法：

- `build_tab_notes()`
- `add_note()`
- `refresh_notes()`
- `search_notes()`
- `delete_note()`
- `switch_notes_mode()`

### 5.3 統計頁（stats）

主要功能：

- 顯示今日完成率
- 顯示本週完成率
- 顯示累積讀書天數
- 顯示完整歷史項目
- 以圖表方式顯示已完成科目時數

關鍵方法：

- `build_tab_stats()`
- `refresh_stats()`
- `refresh_stats_detail()`
- `refresh_study_chart()`
- `switch_stats_mode()`

---

## 6. 重要功能模組

### 6.1 資料載入與儲存

- `load_data()`
  - 讀取 JSON 檔
  - 建立預設資料結構
  - 如果資料格式老舊，會做迁移處理
- `save_data()`
  - 將目前資料寫回 JSON
  - 會同步更新狀態欄位

### 6.2 日期與倒數計時

- `get_today_key()`
- `ensure_today_plan()`
- `update_exam_date()`
- `refresh_countdown()`
- `get_days_left()`

這些方法會管理：

- 今天日期
- 考試日期
- 倒數天數
- 今日預設計畫是否已建立

### 6.3 主題系統

主題設定集中在 `THEMES`，目前包含：

- `light`
- `dark`
- `coffee`
- `light_coffee`

修改主題時，通常要同步更新：

- `THEMES`
- `define_colors()`
- `switch_theme()`

### 6.4 自訂下拉選單與旋轉元件

這個工具沒有使用 ttk 的 Combobox，而是自行實作了：

- `_make_dropdown()`：自定義下拉選單
- `_mk_spin()`：自定義數值調整元件

如果之後要改成更原生的 UI，這兩段是最先要注意的地方。

---

## 7. 預設內容

### 7.1 預設考試日期

- `DEFAULT_EXAM_DATE = "2026-10-18"`

### 7.2 預設科目

- 企業管理
- 經濟學
- 法學
- 國英
- 歷屆題

### 7.3 預設每日計畫

啟動時若今天沒有資料，會自動生成一份預設計畫，內容來自 `DEFAULT_PLAN`。

---

## 8. 常見修改點

### 8.1 新增或修改科目

需要修改：

- `DEFAULT_SUBJECTS`
- `DEFAULT_PLAN`
- `SECTION_COLORS`（如果要配色不同）

### 8.2 改變 UI 版型

通常要修改：

- `build_ui()`
- `build_tab_todo()`
- `build_tab_notes()`
- `build_tab_stats()`

### 8.3 改變資料儲存邏輯

要優先看：

- `load_data()`
- `save_data()`
- `ensure_today_plan()`

### 8.4 改變統計方式

要修改：

- `refresh_stats()`
- `refresh_stats_detail()`
- `refresh_study_chart()`

### 8.5 新增主題

要修改：

- `THEMES`
- `define_colors()`
- `switch_theme()`

---

## 9. 維護建議

- 之後若要新增功能，建議先從 `ExamPrepApp` 的對應區塊開始改，而不是散落在各處。
- 若要加入新的頁籤，建議遵循現有 `build_tab_xxx()` + `switch_tab()` 的模式。
- 資料格式變更時，務必同步更新 `load_data()` / `save_data()`。
- 若要增加新的欄位，建議先確認是否有舊資料兼容問題。

---

## 10. 執行方式

在專案資料夾中執行：

```bash
python exam_tool.py
```

如果環境中缺少 `tkcalendar`，日期選擇器功能可能會受影響，但主流程仍可使用。
