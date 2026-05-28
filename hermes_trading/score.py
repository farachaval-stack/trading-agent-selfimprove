from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np


def score(trades: Iterable[dict[str, Any]], goal: dict[str, Any]) -> float:
    closed = [trade for trade in trades if trade.get("status") == "closed"]
    if not closed:
        return 0.0

    returns = np.array([float(trade.get("return_pct", 0.0)) / 100 for trade in closed])
    realised = float(np.prod(1 + returns) - 1)
    drawdown = _max_drawdown(returns)
    sharpe = _sharpe(returns)

    target = float(goal.get("target_return_30d", 0.05))
    max_dd = float(goal.get("max_drawdown", 0.08))
    min_sharpe = float(goal.get("min_sharpe", 1.2))

    return_component = _clip(realised / target if target else 0.0)
    drawdown_component = _clip(1.0 - (drawdown / max_dd if max_dd else 1.0))
    sharpe_component = _clip(sharpe / min_sharpe if min_sharpe else 0.0)

    composite = (0.45 * return_component) + (0.35 * drawdown_component) + (0.20 * sharpe_component)
    return round(_clip(composite), 4)


def metrics(trades: Iterable[dict[str, Any]]) -> dict[str, float]:
    closed = [trade for trade in trades if trade.get("status") == "closed"]
    if not closed:
        return {"realised_return": 0.0, "max_drawdown": 0.0, "sharpe": 0.0}
    returns = np.array([float(trade.get("return_pct", 0.0)) / 100 for trade in closed])
    return {
        "realised_return": round(float(np.prod(1 + returns) - 1), 6),
        "max_drawdown": round(_max_drawdown(returns), 6),
        "sharpe": round(_sharpe(returns), 6),
    }


def _max_drawdown(returns: np.ndarray) -> float:
    equity = np.cumprod(1 + returns)
    peaks = np.maximum.accumulate(equity)
    drawdowns = (peaks - equity) / peaks
    return float(drawdowns.max()) if len(drawdowns) else 0.0


def _sharpe(returns: np.ndarray) -> float:
    if len(returns) < 2:
        return 0.0
    std = float(returns.std(ddof=1))
    if math.isclose(std, 0.0):
        return 0.0
    return float((returns.mean() / std) * math.sqrt(365 * 24 * 60))


def _clip(value: float) -> float:
    return max(-1.0, min(1.0, value))
