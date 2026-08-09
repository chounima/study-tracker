"""Flet entry point — cross-platform replacement for the Tkinter app's
main.py / app/app.py. Run with `flet run` (see README-flet.md), or package
with `flet build <target>` for Windows/macOS/Linux/Android/iOS/Web.
"""
import flet as ft

from app_ui import AppUI
from store import Store


async def main(page: ft.Page):
    prefs = ft.SharedPreferences()
    page.services.append(prefs)

    store = Store(prefs)
    await store.load()
    await store.ensure_today_plan()

    app = AppUI(page, store)
    await app.start()


if __name__ == "__main__":
    ft.run(main)
