"""Theme helpers — the four palettes from the Tkinter version's THEMES dict
are reused as-is; this module just adapts them for Flet controls."""
import config

SUBJECT_COLORS = {
    "企業管理": "#6366f1",
    "經濟學": "#3b82f6",
    "法學": "#8b5cf6",
    "國英": "#22c55e",
    "歷屆題": "#f59e0b",
}


def get_palette(theme_name: str) -> dict:
    return config.THEMES.get(theme_name, config.THEMES["light"])


def subject_color(subject: str, muted: str) -> str:
    return SUBJECT_COLORS.get(subject, muted)


def scale(base: int, factor: float) -> int:
    return max(1, round(base * factor))
