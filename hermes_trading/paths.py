from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(os.getenv("HERMES_TRADING_ROOT", Path.cwd())).resolve()
STATE_DIR = Path(os.getenv("HERMES_TRADING_STATE_DIR", PROJECT_ROOT / "state")).resolve()
GOAL_FILE = STATE_DIR / "goal.yaml"
STRATEGY_FILE = STATE_DIR / "strategy.yaml"
TRADES_FILE = STATE_DIR / "trades.jsonl"
HYPOTHESES_FILE = STATE_DIR / "hypotheses.jsonl"
HEARTBEAT_FILE = STATE_DIR / "heartbeat.json"
HISTORY_DIR = STATE_DIR / "history"


def ensure_state_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    TRADES_FILE.touch(exist_ok=True)
    HYPOTHESES_FILE.touch(exist_ok=True)
