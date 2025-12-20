from datetime import date

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import repository
from database.models import Base, ServerMetrics


@pytest.fixture
def sqlite_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def patch_repository(monkeypatch, sqlite_session):
    # Repository expects a Servers symbol; alias to ServerMetrics.
    monkeypatch.setattr(repository, "Servers", ServerMetrics)
    # Use in-memory session factory.
    monkeypatch.setattr(repository, "SessionLocal", lambda: sqlite_session)
    yield


def test_insert_and_query_metrics(sqlite_session):
    repo = repository.MetricsRepository(sqlite_session)

    inserted = repo.insert_metric(
        vm="srv-1",
        date=date(2025, 1, 1),
        metric="cpu.usage.average",
        avg_value=42.5,
    )
    assert inserted is True

    df = repo.get_all_metrics(vm="srv-1")
    assert len(df) == 1
    assert df.iloc[0]["avg_value"] == 42.5


def test_upsert_existing_metric(sqlite_session):
    repo = repository.MetricsRepository(sqlite_session)
    initial = repo.insert_metric(
        vm="srv-1",
        date=date(2025, 1, 1),
        metric="mem.usage.average",
        avg_value=10,
    )
    assert initial is True

    # Upsert should update existing row, not create new one.
    updated = repo.insert_metric(
        vm="srv-1",
        date=date(2025, 1, 1),
        metric="mem.usage.average",
        avg_value=55,
    )
    assert updated is True

    df = repo.get_all_metrics(vm="srv-1")
    assert len(df) == 1
    assert df.iloc[0]["avg_value"] == 55


def test_insert_from_dataframe(sqlite_session):
    repo = repository.MetricsRepository(sqlite_session)

    df = pd.DataFrame(
        [
            {"vm": "a", "date": date(2025, 1, 1), "metric": "cpu.usage.average", "avg_value": 10},
            {"vm": "b", "date": date(2025, 1, 2), "metric": "mem.usage.average", "avg_value": 20},
        ]
    )

    result = repo.insert_from_dataframe(df)
    assert result["errors"] == 0
    assert result["success"] == 2

    all_df = repo.get_all_metrics()
    assert len(all_df) == 2


