from __future__ import annotations

import time
from typing import Any

import httpx
import numpy as np

from .base import SCHEMA_VERSION, require_schema


BINANCE_URL = "https://api.binance.com/api/v3/klines"


def _symbol(asset: str) -> str:
    return asset.replace("/", "").replace("-", "").upper()


def _rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) <= period:
        return 50.0
    deltas = np.diff(np.array(closes, dtype=float))
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = gains[-period:].mean()
    avg_loss = losses[-period:].mean()
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


async def fetch(asset: str = "BTC/USDT") -> dict[str, Any]:
    params = {"symbol": _symbol(asset), "interval": "1m", "limit": 60}
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        response = await client.get(BINANCE_URL, params=params)
        response.raise_for_status()
        rows = response.json()

    closes = [float(row[4]) for row in rows]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "binance_public",
        "asset": asset,
        "timestamp": int(time.time()),
        "price": closes[-1],
        "previous_price": closes[-2] if len(closes) > 1 else closes[-1],
        "rsi": _rsi(closes),
        "close_count": len(closes),
    }
    return require_schema(payload, "price")
