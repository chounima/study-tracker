import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "exam_progress.json")
DEFAULT_EXAM_DATE = "2026-10-18"
DEFAULT_PLAN = [
    {"section": "上午", "time_start": "08:30", "time_end": "10:30", "subject": "企業管理"},
    {"section": "下午", "time_start": "13:30", "time_end": "15:30", "subject": "經濟學"},
    {"section": "晚上", "time_start": "19:00", "time_end": "20:00", "subject": "歷屆題"},
    {"section": "晚上", "time_start": "20:00", "time_end": "21:00", "subject": "法學"},
    {"section": "晚上", "time_start": "21:00", "time_end": "22:30", "subject": "國英"},
]
DEFAULT_SUBJECTS = ["企業管理", "經濟學", "法學", "國英", "歷屆題"]
SECTION_COLORS = {"上午": "#f59e0b", "下午": "#3b82f6", "晚上": "#8b5cf6", "今日": "#10b981"}

THEMES = {
    "light": {
        "bg": "#f1f5f9", "titlebar_bg": "#0f172a", "strip_bg": "#e2e8f0",
        "card": "#ffffff", "border": "#cbd5e1", "text": "#1e293b",
        "muted": "#64748b", "accent": "#6366f1", "accent_lt": "#818cf8",
        "success": "#22c55e", "warn": "#ef4444", "done_fg": "#94a3b8",
        "input_bg": "#ffffff",
        "_dot": "#6366f1", "_label": "淺色",
    },
    "dark": {
        "bg": "#0f172a", "titlebar_bg": "#020617", "strip_bg": "#1e293b",
        "card": "#1e293b", "border": "#334155", "text": "#e2e8f0",
        "muted": "#94a3b8", "accent": "#818cf8", "accent_lt": "#a5b4fc",
        "success": "#4ade80", "warn": "#f87171", "done_fg": "#475569",
        "input_bg": "#334155",
        "_dot": "#818cf8", "_label": "深色",
    },
    "coffee": {
        "bg": "#2c1810", "titlebar_bg": "#180d08", "strip_bg": "#3d2418",
        "card": "#3d2418", "border": "#5c3820", "text": "#f5e6d3",
        "muted": "#b08060", "accent": "#e8944a", "accent_lt": "#f0aa70",
        "success": "#6abf6a", "warn": "#f08070", "done_fg": "#7a5040",
        "input_bg": "#4a2e1c",
        "_dot": "#e8944a", "_label": "咖啡",
    },
    "light_coffee": {
        "bg": "#fdf6ee", "titlebar_bg": "#3d2412", "strip_bg": "#f0e0cc",
        "card": "#ffffff", "border": "#d4b896", "text": "#3d2412",
        "muted": "#8b6040", "accent": "#b8581a", "accent_lt": "#d4784a",
        "success": "#2e7d32", "warn": "#c62828", "done_fg": "#b09878",
        "input_bg": "#ffffff",
        "_dot": "#b8581a", "_label": "淺咖啡",
    },
}
