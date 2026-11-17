"""The spare monitor must not promote Redis or start bots."""

import importlib
import importlib.util
import sys
from pathlib import Path


def _monitor_module():
    # The equity executor test installs a structlog stub for the process.
    sys.modules.pop("structlog", None)
    importlib.import_module("structlog")
    path = Path(__file__).resolve().parents[3] / "infrastructure" / "scripts" / "failover_monitor.py"
    spec = importlib.util.spec_from_file_location("failover_monitor_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_monitor_refuses_promotion(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monitor = _monitor_module().FailoverMonitor()

    assert monitor.promote_redis_to_master() is False
    assert monitor.start_bot_service("quantshift-equity") is False
    assert monitor.perform_failover() is False
