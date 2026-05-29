from __future__ import annotations

import argparse
import asyncio
import os

from .config import load_yaml
from .loop import run_loop
from .paths import GOAL_FILE, STRATEGY_FILE, ensure_state_dirs
from .scheduler import run_scheduler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the paper trading worker")
    parser.add_argument("--asset", help="Override the asset in state/goal.yaml")
    parser.add_argument("--once", action="store_true", help="Run one loop iteration and exit")
    parser.add_argument("--no-scheduler", action="store_true", help="Disable the in-process reflection scheduler")
    return parser.parse_args()


def main() -> None:
    ensure_state_dirs()
    args = parse_args()
    goal = load_yaml(GOAL_FILE)
    asset = args.asset or str(goal.get("asset", "BTC/USDT"))
    if args.once or args.no_scheduler or os.getenv("HERMES_REFLECTION_SCHEDULER_ENABLED", "true").lower() == "false":
        asyncio.run(run_loop(GOAL_FILE, STRATEGY_FILE, asset, once=args.once))
        return

    asyncio.run(_run_worker_with_scheduler(asset))


async def _run_worker_with_scheduler(asset: str) -> None:
    await asyncio.gather(
        run_loop(GOAL_FILE, STRATEGY_FILE, asset),
        run_scheduler(mode=os.getenv("HERMES_REFLECTION_MODE", "fallback")),
    )


if __name__ == "__main__":
    main()
