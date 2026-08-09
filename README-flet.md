# study-tracker — Flet 跨平台版

這是 `study-tracker`（原本的 Tkinter 桌面版，見 [README.md](README.md)）的 **Flet 版本**，同一份程式碼可以打包成 Windows / macOS / Linux 桌面應用、Android APK/AAB、iOS IPA、以及網頁版。原本的 Tkinter 版本（`app/`、`main.py`）完全沒有被修改，兩個版本並存於同一個 repo。

---

## 1. 專案結構

```
study-tracker/
├── app/                  ← 原本的 Tkinter 版本（未變動）
├── main.py                ← 原本 Tkinter 版本的進入點（未變動）
├── flet_app/               ← 新的 Flet 版本（本次新增）
│   ├── main.py               ← 進入點：flet run 會執行這個檔案
│   ├── config.py               ← 常數／四色主題色票（直接沿用原本的值）
│   ├── store.py                 ← 資料層：對應原本 app/storage.py 的 DataMixin，
│   │                              改用 Flet 的 SharedPreferences 儲存（見第 4 節）
│   ├── theme.py                  ← 主題/科目配色小工具
│   ├── shell.py                    ← 標題列／倒數列／分頁列／設定對話框
│   ├── tab_todo.py                  ← 待辦分頁
│   ├── tab_notes.py                  ← 錯題分頁
│   ├── tab_stats.py                   ← 統計分頁
│   ├── app_ui.py                       ← 把上面幾個 Mixin 組成 AppUI（架構對應原本的 ExamPrepApp）
│   └── assets/                          ← 圖示等靜態資源（flet build 用）
├── pyproject.toml         ← flet build 設定（[tool.flet] 區塊）
├── requirements-flet.txt   ← Flet 版本的執行期依賴
└── README-flet.md          ← 本文件
```

`flet_app/` 內部彼此用**一般（非套件）匯入**（例如 `import config`、`from store import Store`），因為 `flet run`／`flet build` 是把 `flet_app/main.py` 當成腳本直接執行，而不是當成 Python package 匯入 —— 這是 Flet 專案的標準寫法，不要改成 `from . import config` 之類的相對匯入，否則會直接噴 `ImportError`。

---

## 2. 開發時測試

```bash
cd study-tracker
python -m venv .venv          # 如果還沒建立
.venv\Scripts\activate
pip install -r requirements-flet.txt
```

啟動（桌面原生視窗，支援 hot reload）：

```bash
flet run flet_app/main.py
```

啟動網頁版（本機瀏覽器）：

```bash
flet run -w flet_app/main.py
```

在手機上即時預覽（先在手機上安裝 [Flet app](https://flet.dev/docs/getting-started/testing-on-ios-and-android/) 並和電腦連上同一個網路）：

```bash
flet run --android flet_app/main.py   # 或 --ios
```

---

## 3. 打包成各平台安裝檔

都在 `study-tracker/` 目錄下執行（`pyproject.toml` 的 `[tool.flet.app] path = "flet_app"` 已經指定進入點在哪）：

```bash
flet build windows     # → build/windows
flet build macos       # → build/macos（需在 macOS 上執行）
flet build linux       # → build/linux（需在 Linux 上執行）
flet build web         # → build/web，靜態網站，可部署到任何靜態主機
flet build apk         # → build/apk（Android，需要 Android SDK；第一次執行會引導安裝）
flet build aab         # → build/aab（上架 Google Play 用）
flet build ipa          # → build/ipa（iOS，需要 macOS + Xcode）
```

- 桌面/行動版打包需要 Flutter 建置工具鏈（`flet build` 第一次執行時會自動檢查並引導安裝缺少的部分）。
- iOS 打包（`flet build ipa`）只能在 macOS 上執行，這是 Apple 的限制，跟 Flet 無關。
- 打包前可先跑 `flet doctor` 檢查環境。

原本 Tkinter 版本的 `pyinstaller --onefile --noconsole --name study_tracker main.py` 打包方式不受影響，仍可正常使用。

---

## 4. 資料儲存怎麼從「JSON 檔案」變成跨平台的？

原本 Tkinter 版本把 `exam_progress.json` 存在程式旁邊的資料夾 —— 這在手機上行不通（App 沒有這種可預期、持久的檔案路徑）。Flet 版本改用官方的 **`SharedPreferences`** 服務（[flet_app/store.py](flet_app/store.py) 的 `Store.load()`/`Store.save()`），把整包資料序列化成一個 JSON 字串存在一個 key 底下：

- Windows / macOS / Linux：存在系統的應用程式偏好設定位置
- Android / iOS：存在系統原生的 SharedPreferences / NSUserDefaults
- Web：存在瀏覽器的 localStorage

四個平台各自獨立存檔、互不同步（符合先前談好的方向）——換句話說，同一個人在手機跟電腦上會看到**各自獨立**的讀書紀錄，不會自動同步。以後如果要做多裝置同步，`store.py` 是唯一要動的地方（换成打後端 API）。

舊資料格式的自動遷移（`migrate_legacy_todos`、`normalize_notes`、`fill_missing_todo_times`）都原封不動保留，如果你手動把舊的 `exam_progress.json` 內容貼進去（例如透過瀏覽器開發者工具寫入 localStorage），一樣可以被正確讀取跟升級格式。

---

## 5. 套件差異／哪些原本的相依套件不見了

| 原本 | Flet 版本 | 說明 |
|---|---|---|
| `tkcalendar`（日期選擇器）| Flet 內建 `DatePicker` | 原生跨平台，不需要額外套件 |
| 手繪 `tk.Canvas` 長條圖 | `Container` + `expand` 權重手刻的比例長條 | 沒有引入 `matplotlib`，圖表邏輯在 [tab_stats.py](flet_app/tab_stats.py) 的 `_refresh_study_chart()`；效果類似但非像素級一致 |
| `ttk.Treeview`（統計詳細項）| `ft.DataTable`（可點欄位排序）| 手機上欄位較多，超出畫面寬度時用左右滑動捲動查看，未做響應式欄位隱藏 |
| PyInstaller | `flet build <target>` | 見第 3 節 |
| 自訂下拉選單／spin 元件 | `ft.Dropdown` | 原本手刻的 `_make_dropdown`/`_mk_spin` 不再需要 |
| 無邊框視窗＋標題列拖曳＋永遠置頂 | 標準系統視窗 | 這是 Windows 桌面專屬效果，手機/網頁沒有對應概念，依先前談好的方向改為標準視窗 |

`UPGRADE_PLAN.md` 裡列的「到點提醒通知」（`plyer`/`win10toast`）在 Tkinter 版本本來就還沒做，這次 Flet 版本也還沒實作 —— 如果之後要加，Flet 有自己的跨平台 `flet.audio`/系統通知等 API，屆時再另外評估。

---

## 6. 已知的簡化 / 之後可以再打磨的地方

- 統計頁的長條圖、詳細表格是功能對應但非像素級還原，尤其小螢幕（手機）上 `DataTable` 欄位較擠。
- 尚未針對手機直向/橫向、平板等不同尺寸做響應式版面微調（目前是同一份版面，靠系統捲動應付）。
- 我在此開發環境只能用 `flet run -w`（網頁模式）做到「程式能不能正常啟動、建構完整介面、不噴例外」的驗證，无法實際看到畫面或用滑鼠點擊測試互動效果 —— 強烈建議你實際跑一次 `flet run flet_app/main.py`，把三個分頁、新增/編輯/刪除待辦、新增/搜尋錯題、切換主題、統計頁兩種檢視都手動點過一次，確認視覺與互動符合預期。
