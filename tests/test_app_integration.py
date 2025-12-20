import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app" / "app.py"


@pytest.fixture
def sample_metrics() -> pd.DataFrame:
    """Minimal dataset to render dashboard without hitting a real DB."""
    dates = pd.date_range(datetime(2025, 1, 1), periods=3, freq="D")
    records = [
        {"vm": "srv-1", "date": dates[0], "metric": "cpu.usage.average", "avg_value": 15.0},
        {"vm": "srv-1", "date": dates[0], "metric": "mem.usage.average", "avg_value": 25.0},
        {"vm": "srv-2", "date": dates[1], "metric": "cpu.usage.average", "avg_value": 75.0},
        {"vm": "srv-2", "date": dates[1], "metric": "mem.usage.average", "avg_value": 85.0},
        {"vm": "srv-3", "date": dates[2], "metric": "cpu.usage.average", "avg_value": 55.0},
        {"vm": "srv-3", "date": dates[2], "metric": "mem.usage.average", "avg_value": 60.0},
    ]
    return pd.DataFrame.from_records(records)


@pytest.fixture(autouse=True)
def stub_external_dependencies(monkeypatch, sample_metrics):
    """Stub auth and data loading so the app renders in tests."""
    monkeypatch.setattr("database.repository.get_metrics_from_db", lambda **_: sample_metrics.copy())
    monkeypatch.setattr("app.auth.check_auth", lambda: True)
    monkeypatch.setattr("app.auth.has_role", lambda roles: True)
    monkeypatch.setattr(
        "app.auth.get_current_user",
        lambda: {"name": "Test Admin", "role": "admin", "email": "admin@example.com"},
    )
    yield


def test_dashboard_renders_classification_table():
    at = AppTest.from_file(str(APP_PATH)).run()

    assert at.exception is None
    assert at.dataframe, "Expected classification table to render"

    classification_df = at.dataframe[0].value
    assert not classification_df.empty
    assert {"Сервер", "Средний CPU %", "Средняя Memory %"} <= set(classification_df.columns)


def test_dashboard_shows_summary_cards_and_controls():
    at = AppTest.from_file(str(APP_PATH)).run()

    assert at.exception is None

    text_blocks = " ".join(md.value for md in at.markdown)
    assert "Дашборд мониторинга нагрузки серверов" in text_blocks
    assert "Всего серверов" in text_blocks
    assert any(btn.label == "Запустить" for btn in at.button), "Anomaly analysis trigger missing"


