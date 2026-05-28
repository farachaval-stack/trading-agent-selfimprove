from __future__ import annotations

import argparse
import asyncio

from .config import load_yaml
from .loop import run_loop
from .paths import GOAL_FILE, STRATEGY_FILE, ensure_state_dirs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the paper trading worker")
    parser.add_argument("--asset", help="Override the asset in state/goal.yaml")
    parser.add_argument("--once", action="store_true", help="Run one loop iteration and exit")
    return parser.parse_args()


def main() -> None:
    ensure_state_dirs()
    args = parse_args()
    goal = load_yaml(GOAL_FILE)
    asset = args.asset or str(goal.get("asset", "BTC/USDT"))
    asyncio.run(run_loop(GOAL_FILE, STRATEGY_FILE, asset, once=args.once))


if __name__ == "__main__":
    main()
