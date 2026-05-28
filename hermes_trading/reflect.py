from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from .config import load_yaml, write_yaml
from .paths import GOAL_FILE, HYPOTHESES_FILE, HISTORY_DIR, STRATEGY_FILE, TRADES_FILE, ensure_state_dirs
from .score import metrics, score


ALLOWED_PATHS = {"entry.threshold", "stop_loss_pct", "position_size_r"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reflect on closed trades and evolve strategy")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fallback", action="store_true", help="Use deterministic reflection")
    mode.add_argument("--hermes", action="store_true", help="Use the hermes command")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and print intended action only")
    return parser.parse_args()


def main() -> None:
    ensure_state_dirs()
    args = parse_args()
    trades = _read_trades()
    goal = load_yaml(GOAL_FILE)
    strategy = load_yaml(STRATEGY_FILE)

    if args.hermes and args.dry_run:
        print(_hermes_prompt(trades[-25:], goal, strategy))
        print(f"hermes_command_found={bool(shutil.which('hermes'))}")
        return

    if args.fallback:
        hypothesis = _fallback_hypothesis(trades, goal, strategy)
    else:
        hypothesis = _hermes_hypothesis(trades[-25:], goal, strategy)

    if args.dry_run:
        print(json.dumps(hypothesis, indent=2, sort_keys=True))
        return

    updated = _apply_hypothesis(strategy, hypothesis)
    _persist(strategy, updated, hypothesis, trades, goal, "fallback" if args.fallback else "hermes")
    print(f"reflected {strategy.get('version')} -> {updated.get('version')}: {hypothesis['path']}={hypothesis['value']}")


def _read_trades() -> list[dict[str, Any]]:
    if not TRADES_FILE.exists():
        return []
    trades = []
    for line in TRADES_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            trades.append(json.loads(line))
    return trades


def _fallback_hypothesis(trades: list[dict[str, Any]], goal: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
    observed = metrics(trades)
    target = float(goal.get("target_return_30d", 0.05))
    max_dd = float(goal.get("max_drawdown", 0.08))

    if observed["max_drawdown"] > max_dd:
        current = float(strategy.get("stop_loss_pct", 2.0))
        return {
            "path": "stop_loss_pct",
            "value": round(max(0.2, current - 0.2), 2),
            "reason": "drawdown exceeded max_drawdown, so tighten risk first",
            "confidence": 0.62,
        }

    if observed["realised_return"] < target:
        current = float(strategy.get("entry", {}).get("threshold", 30))
        return {
            "path": "entry.threshold",
            "value": round(current + 2, 2),
            "reason": "realised return is below target, so loosen RSI entry by 2",
            "confidence": 0.58,
        }

    current = float(strategy.get("position_size_r", 0.5))
    return {
        "path": "position_size_r",
        "value": round(min(2.0, current + 0.1), 2),
        "reason": "goals are currently met, so test a small position-size increase",
        "confidence": 0.51,
    }


def _hermes_hypothesis(trades: list[dict[str, Any]], goal: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
    if not shutil.which("hermes"):
        raise RuntimeError("hermes command not found in this environment")

    prompt = _hermes_prompt(trades, goal, strategy)
    result = subprocess.run(
        ["hermes"],
        input=prompt,
        text=True,
        capture_output=True,
        check=True,
        timeout=300,
    )
    return _parse_hypothesis(result.stdout)


def _hermes_prompt(trades: list[dict[str, Any]], goal: dict[str, Any], strategy: dict[str, Any]) -> str:
    return (
        "You are improving a paper trading strategy. Return only JSON with keys "
        "path, value, reason, confidence. The path must be one of "
        f"{sorted(ALLOWED_PATHS)} and exactly one variable may change.\n\n"
        f"Goal:\n{json.dumps(goal, indent=2, sort_keys=True)}\n\n"
        f"Current strategy:\n{json.dumps(strategy, indent=2, sort_keys=True)}\n\n"
        f"Latest trades:\n{json.dumps(trades, indent=2, sort_keys=True)}\n"
    )


def _parse_hypothesis(output: str) -> dict[str, Any]:
    start = output.find("{")
    end = output.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Hermes output did not contain a JSON object")
    data = json.loads(output[start : end + 1])
    if data.get("path") not in ALLOWED_PATHS:
        raise ValueError(f"unsupported hypothesis path: {data.get('path')}")
    for key in ("value", "reason"):
        if key not in data:
            raise ValueError(f"hypothesis missing {key}")
    data.setdefault("confidence", 0.5)
    return data


def _apply_hypothesis(strategy: dict[str, Any], hypothesis: dict[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(strategy))
    path = hypothesis["path"]
    if path == "entry.threshold":
        updated.setdefault("entry", {})["threshold"] = hypothesis["value"]
    elif path == "stop_loss_pct":
        updated["stop_loss_pct"] = hypothesis["value"]
    elif path == "position_size_r":
        updated["position_size_r"] = hypothesis["value"]
    else:
        raise ValueError(f"unsupported hypothesis path: {path}")
    updated["version"] = _next_version(str(strategy.get("version", "01")))
    return updated


def _persist(
    previous: dict[str, Any],
    updated: dict[str, Any],
    hypothesis: dict[str, Any],
    trades: list[dict[str, Any]],
    goal: dict[str, Any],
    mode: str,
) -> None:
    old_version = str(previous.get("version", "01"))
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    write_yaml(HISTORY_DIR / f"v{old_version}.yaml", previous)
    write_yaml(STRATEGY_FILE, updated)

    record = {
        "timestamp": int(time.time()),
        "mode": mode,
        "from_version": old_version,
        "to_version": updated.get("version"),
        "score": score(trades, goal),
        "metrics": metrics(trades),
        "hypothesis": hypothesis,
    }
    with HYPOTHESES_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _next_version(version: str) -> str:
    return f"{int(version) + 1:02d}"


if __name__ == "__main__":
    main()
