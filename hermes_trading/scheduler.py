from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from contextlib import contextmanager
from typing import Any

from .config import load_yaml
from .paths import (
    GOAL_FILE,
    HYPOTHESES_FILE,
    REFLECTION_ERRORS_FILE,
    REFLECTION_LOCK_FILE,
    REFLECTION_STATE_FILE,
    STRATEGY_FILE,
    ensure_state_dirs,
)
from .reflect import RSI_THRESHOLD_MAX, RSI_THRESHOLD_MIN, _read_trades, reflect_once


DEFAULT_INTERVAL_SECONDS = 300
DEFAULT_MIN_REFLECTION_SECONDS = 1800
LOCK_TIMEOUT_SECONDS = 900


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the in-process reflection scheduler")
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    parser.add_argument("--mode", choices=("fallback", "hermes"), default=os.getenv("HERMES_REFLECTION_MODE", "fallback"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(run_scheduler(mode=args.mode, once=args.once))


async def run_scheduler(mode: str = "fallback", once: bool = False) -> None:
    ensure_state_dirs()
    print(f"Booting reflection scheduler in {mode} mode", flush=True)

    while True:
        try:
            result = check_and_reflect(mode)
            if result["reflected"]:
                print(
                    "reflection scheduler: "
                    f"{result['from_version']} -> {result['to_version']} "
                    f"{result['changed_path']}={result['changed_value']} "
                    f"after {result['new_trade_count']} new trades",
                    flush=True,
                )
            else:
                print(
                    "reflection scheduler: not due "
                    f"({result['new_trade_count']}/{result['reflection_every']} new trades)",
                    flush=True,
                )
        except Exception as exc:
            _append_error(exc)
            print(f"reflection scheduler error: {exc}", flush=True)

        if once:
            return

        await asyncio.sleep(_interval_seconds())


def check_and_reflect(mode: str = "fallback") -> dict[str, Any]:
    ensure_state_dirs()
    goal = load_yaml(GOAL_FILE)
    reflection_every = int(goal.get("reflection_every", 5))
    trades = _closed_trades()
    checkpoint = _load_checkpoint(trades)
    repair_due = _strategy_needs_repair()
    cooldown_remaining = _cooldown_remaining(checkpoint)
    new_trades = [trade for trade in trades if _closed_at(trade) > int(checkpoint.get("last_reflected_closed_at", 0))]

    if cooldown_remaining > 0 and not repair_due:
        return {
            "reflected": False,
            "new_trade_count": len(new_trades),
            "reflection_every": reflection_every,
            "cooldown_remaining": cooldown_remaining,
        }

    if len(new_trades) < reflection_every and not repair_due:
        return {"reflected": False, "new_trade_count": len(new_trades), "reflection_every": reflection_every}

    with _reflection_lock():
        trades = _closed_trades()
        checkpoint = _load_checkpoint(trades)
        repair_due = _strategy_needs_repair()
        cooldown_remaining = _cooldown_remaining(checkpoint)
        new_trades = [trade for trade in trades if _closed_at(trade) > int(checkpoint.get("last_reflected_closed_at", 0))]
        if cooldown_remaining > 0 and not repair_due:
            return {
                "reflected": False,
                "new_trade_count": len(new_trades),
                "reflection_every": reflection_every,
                "cooldown_remaining": cooldown_remaining,
            }
        if len(new_trades) < reflection_every and not repair_due:
            return {"reflected": False, "new_trade_count": len(new_trades), "reflection_every": reflection_every}

        reflection_trades = new_trades if new_trades else trades[-reflection_every:]
        result = reflect_once(mode=mode, trades=reflection_trades)
        latest_trade = max((_closed_at(trade) for trade in trades), default=0)
        _write_checkpoint(
            {
                "timestamp": int(time.time()),
                "last_reflected_closed_at": latest_trade,
                "last_reflected_trade_count": len(trades),
                "last_reflected_trade_id": trades[-1].get("trade_id") if trades else None,
                "strategy_version": result.get("to_version"),
                "mode": mode,
            }
        )
        return {
            "reflected": True,
            "new_trade_count": len(new_trades),
            "reflection_every": reflection_every,
            "from_version": result.get("from_version"),
            "to_version": result.get("to_version"),
            "changed_path": result["hypothesis"]["path"],
            "changed_value": result["hypothesis"]["value"],
            "repair_due": repair_due,
        }


def _closed_trades() -> list[dict[str, Any]]:
    return [trade for trade in _read_trades() if trade.get("status") == "closed"]


def _load_checkpoint(trades: list[dict[str, Any]]) -> dict[str, Any]:
    if REFLECTION_STATE_FILE.exists():
        with REFLECTION_STATE_FILE.open("r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return data

    last_reflection_ts = _last_hypothesis_timestamp()
    return {
        "timestamp": last_reflection_ts,
        "last_reflected_closed_at": last_reflection_ts,
        "last_reflected_trade_count": len([trade for trade in trades if _closed_at(trade) <= last_reflection_ts]),
        "last_reflected_trade_id": None,
        "strategy_version": load_yaml(STRATEGY_FILE).get("version"),
        "mode": "bootstrap",
    }


def _write_checkpoint(payload: dict[str, Any]) -> None:
    with REFLECTION_STATE_FILE.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _last_hypothesis_timestamp() -> int:
    if not HYPOTHESES_FILE.exists():
        return 0
    last_timestamp = 0
    for line in HYPOTHESES_FILE.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            last_timestamp = int(json.loads(line).get("timestamp", 0))
    return last_timestamp


@contextmanager
def _reflection_lock():
    now = int(time.time())
    if REFLECTION_LOCK_FILE.exists():
        age = now - int(REFLECTION_LOCK_FILE.stat().st_mtime)
        if age < LOCK_TIMEOUT_SECONDS:
            raise RuntimeError(f"reflection already locked; age={age}s")
        REFLECTION_LOCK_FILE.unlink()

    handle = REFLECTION_LOCK_FILE.open("x", encoding="utf-8")
    try:
        handle.write(json.dumps({"timestamp": now, "pid": os.getpid()}) + "\n")
        handle.close()
        yield
    finally:
        if not handle.closed:
            handle.close()
        REFLECTION_LOCK_FILE.unlink(missing_ok=True)


def _append_error(exc: Exception) -> None:
    payload = {"timestamp": int(time.time()), "error": str(exc), "type": type(exc).__name__}
    with REFLECTION_ERRORS_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _closed_at(trade: dict[str, Any]) -> int:
    return int(trade.get("closed_at", 0))


def _strategy_needs_repair() -> bool:
    strategy = load_yaml(STRATEGY_FILE)
    threshold = float(strategy.get("entry", {}).get("threshold", 30))
    return threshold < RSI_THRESHOLD_MIN or threshold > RSI_THRESHOLD_MAX


def _interval_seconds() -> int:
    try:
        goal = load_yaml(GOAL_FILE)
        return int(os.getenv("HERMES_REFLECTION_INTERVAL_SECONDS", goal.get("reflection_interval_seconds", DEFAULT_INTERVAL_SECONDS)))
    except Exception:
        return DEFAULT_INTERVAL_SECONDS


def _cooldown_remaining(checkpoint: dict[str, Any]) -> int:
    last_reflection = int(checkpoint.get("timestamp", 0))
    if last_reflection <= 0:
        return 0
    remaining = _min_reflection_seconds() - (int(time.time()) - last_reflection)
    return max(0, remaining)


def _min_reflection_seconds() -> int:
    try:
        goal = load_yaml(GOAL_FILE)
        return int(
            os.getenv(
                "HERMES_MIN_REFLECTION_SECONDS",
                goal.get("min_reflection_seconds", DEFAULT_MIN_REFLECTION_SECONDS),
            )
        )
    except Exception:
        return DEFAULT_MIN_REFLECTION_SECONDS


if __name__ == "__main__":
    main()
