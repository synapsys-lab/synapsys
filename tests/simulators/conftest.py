"""Shared fixtures for simview visual tests.

The QApplication must be created once per process and reused across tests.
All visual tests are skipped automatically when DISPLAY is not available.
"""

from __future__ import annotations

import os
import sys

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "visual: tests that require a Qt display (DISPLAY env var)"
    )


@pytest.fixture(scope="session")
def qt_app():
    """Create (or reuse) the QApplication for the whole test session."""
    if not os.environ.get("DISPLAY"):
        pytest.skip("no DISPLAY — visual tests skipped")

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    yield app


@pytest.fixture
def built_view(qt_app, request):
    """Build the view passed via indirect parametrize and tear it down after."""
    from PySide6.QtWidgets import QMainWindow

    view_cls, kwargs = request.param
    v = view_cls(**kwargs)
    QMainWindow.__init__(v)
    v._build_all()
    yield v
    try:
        v._timer.stop()
        v._pl.close()
    except Exception:
        pass
