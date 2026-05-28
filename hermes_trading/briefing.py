from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_yaml
from .paths import GOAL_FILE, PROJECT_ROOT, STATE_DIR, ensure_state_dirs


TEMPLATE = PROJECT_ROOT / "prompts" / "hermes_briefing_template.md"
OUTPUT = STATE_DIR / "hermes_briefing.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the Hermes handoff briefing")
    parser.add_argument("--railway-project-url", default="", help="Optional Railway project URL")
    return parser.parse_args()


def main() -> None:
    ensure_state_dirs()
    args = parse_args()
    goal = load_yaml(GOAL_FILE)
    template = TEMPLATE.read_text(encoding="utf-8")
    rendered = template.format(
        **{
            "asset": goal.get("asset", "BTC/USDT"),
            "return": _pct(goal.get("target_return_30d", 0.05)),
            "drawdown": _pct(goal.get("max_drawdown", 0.08)),
            "sharpe": goal.get("min_sharpe", 1.2),
            "reflection_every": goal.get("reflection_every", 5),
            "railway_project_url": args.railway_project_url,
            "NNNN": "{NNNN}",
        }
    )
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT}")


def _pct(value: object) -> str:
    return f"{float(value) * 100:g}"


if __name__ == "__main__":
    main()
