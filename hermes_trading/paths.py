from __future__ import annotations

import os
import shutil
from pathlib import Path


PROJECT_ROOT = Path(os.getenv("HERMES_TRADING_ROOT", Path.cwd())).resolve()
STATE_DIR = Path(os.getenv("HERMES_TRADING_STATE_DIR", PROJECT_ROOT / "state")).resolve()
DEFAULT_STATE_DIR = Path(os.getenv("HERMES_TRADING_DEFAULT_STATE_DIR", PROJECT_ROOT / "state.defaults")).resolve()
GOAL_FILE = STATE_DIR / "goal.yaml"
STRATEGY_FILE = STATE_DIR / "strategy.yaml"
TRADES_FILE = STATE_DIR / "trades.jsonl"
HYPOTHESES_FILE = STATE_DIR / "hypotheses.jsonl"
HEARTBEAT_FILE = STATE_DIR / "heartbeat.json"
HISTORY_DIR = STATE_DIR / "history"
REFLECTION_STATE_FILE = STATE_DIR / "reflection_state.json"
REFLECTION_LOCK_FILE = STATE_DIR / "reflection.lock"
REFLECTION_ERRORS_FILE = STATE_DIR / "reflection_errors.jsonl"

SEEDED_FILES = (
    "goal.yaml",
    "strategy.yaml",
    "heartbeat.json",
    "trades.jsonl",
    "hypotheses.jsonl",
    "hermes_briefing.md",
)


def ensure_state_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    _seed_missing_state_files()
    TRADES_FILE.touch(exist_ok=True)
    HYPOTHESES_FILE.touch(exist_ok=True)


def _seed_missing_state_files() -> None:
    if not DEFAULT_STATE_DIR.exists():
        return

    for filename in SEEDED_FILES:
        source = DEFAULT_STATE_DIR / filename
        target = STATE_DIR / filename
        if source.exists() and not target.exists():
            shutil.copy2(source, target)

    default_history = DEFAULT_STATE_DIR / "history"
    if not default_history.exists():
        return

    for source in default_history.glob("*.yaml"):
        target = HISTORY_DIR / source.name
        if not target.exists():
            shutil.copy2(source, target)
