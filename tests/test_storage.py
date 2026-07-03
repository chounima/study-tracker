import json

import pytest

from app import storage
from app.config import DEFAULT_EXAM_DATE, DEFAULT_PLAN, DEFAULT_SUBJECTS
from app.storage import DataMixin


class StubApp(DataMixin):
    """Minimal stand-in for ExamPrepApp that only pulls in DataMixin,
    so storage logic can be tested without creating a Tk window."""


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", str(tmp_path / "exam_progress.json"))
    return StubApp()


def test_load_data_missing_file_uses_defaults(app):
    app.load_data()
    assert app.data["settings"]["exam_date"] == DEFAULT_EXAM_DATE
    assert app.data["settings"]["todo_options"] == DEFAULT_SUBJECTS
    assert app.data["todos_by_date"] == {}
    assert app.data["notes"] == []
    assert app.exam_date == DEFAULT_EXAM_DATE


def test_load_data_reads_existing_new_format(app):
    payload = {
        "settings": {"exam_date": "2027-01-01", "theme": "dark", "ui_scale": 150},
        "todos_by_date": {
            "2026-07-01": [
                {"id": "1", "section": "上午", "time_start": "08:30", "time_end": "10:30",
                 "text": "企業管理", "done": True, "date": "2026-07-01"},
            ],
        },
        "notes": [{"date": "7/1", "subject": "法學", "question": "Q1", "answer": "A1", "reason": ""}],
        "study_logs": [],
    }
    with open(storage.DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    app.load_data()

    assert app.exam_date == "2027-01-01"
    assert app.data["settings"]["theme"] == "dark"
    assert app.data["todos_by_date"]["2026-07-01"][0]["text"] == "企業管理"
    assert app.data["notes"][0]["question"] == "Q1"


def test_load_data_migrates_legacy_todos(app):
    payload = {"todos": [{"time": "09:00", "text": "舊格式待辦", "done": True, "date": "2026-01-01"}]}
    with open(storage.DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    app.load_data()
    today = app.get_today_key()

    migrated = app.data["todos_by_date"][today]
    assert len(migrated) == 1
    assert migrated[0]["text"] == "舊格式待辦"
    assert migrated[0]["time_start"] == "09:00"
    assert migrated[0]["time_end"] == "10:00"
    assert migrated[0]["done"] is True
    assert migrated[0]["section"] == "今日"


def test_normalize_notes_converts_wrong_field_to_question(app):
    result = app.normalize_notes([{"date": "7/1", "subject": "法學", "wrong": "舊題目", "answer": "A"}])
    assert result[0]["question"] == "舊題目"


def test_normalize_notes_parses_legacy_string_format(app):
    result = app.normalize_notes(["7/1:\n這是題目內容"])
    assert result[0]["date"] == "7/1"
    assert result[0]["question"] == "這是題目內容"
    assert result[0]["subject"] == ""


def test_normalize_notes_keeps_already_structured_dicts_unchanged(app):
    note = {"date": "7/1", "subject": "國英", "question": "Q", "answer": "A", "reason": "R"}
    result = app.normalize_notes([note])
    assert result[0] == note


def test_fill_missing_todo_times_fills_from_subject_defaults(app):
    app.load_data()
    app.ensure_today_plan()
    todo = {"text": DEFAULT_PLAN[0]["subject"], "section": DEFAULT_PLAN[0]["section"]}
    app.fill_missing_todo_times([todo])
    assert todo["time_start"] == DEFAULT_PLAN[0]["time_start"]
    assert todo["time_end"] == DEFAULT_PLAN[0]["time_end"]


def test_fill_missing_todo_times_converts_legacy_time_field(app):
    app.load_data()
    app.ensure_today_plan()
    todo = {"text": "自訂項目", "section": "今日", "time": "14:00"}
    app.fill_missing_todo_times([todo])
    assert todo["time_start"] == "14:00"
    assert "time" not in todo
    assert todo["time_end"]


def test_ensure_today_plan_seeds_default_plan_for_empty_today(app):
    app.load_data()
    app.ensure_today_plan()
    assert len(app.todos) == len(DEFAULT_PLAN)
    assert {t["text"] for t in app.todos} == {p["subject"] for p in DEFAULT_PLAN}


def test_save_data_roundtrips_through_disk(app):
    app.load_data()
    app.ensure_today_plan()
    app.todos[0]["done"] = True
    app.exam_date = "2028-05-05"
    app.save_data()

    reloaded = StubApp()
    reloaded.load_data()
    assert reloaded.exam_date == "2028-05-05"
    assert reloaded.data["todos_by_date"][app.today_key][0]["done"] is True
