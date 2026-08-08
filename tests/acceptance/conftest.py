"""Shared fixtures and step definitions for acceptance tests."""

from datetime import date
from typing import Any

import pytest
from pytest_bdd import given, parsers

DEFAULT_TODAY = date(2026, 8, 2)


@pytest.fixture
def context() -> dict[str, Any]:
    return {"today": DEFAULT_TODAY, "fields": {}}


@given(parsers.parse('today is "{value}"'))
def set_today(context: dict[str, Any], value: str) -> None:
    context["today"] = date.fromisoformat(value)
