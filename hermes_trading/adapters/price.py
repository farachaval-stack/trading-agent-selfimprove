from __future__ import annotations

import time
from typing import Any

import httpx
import numpy as np

from .base import SCHEMA_VERSION, require_schema


BINANCE_URL = "https://api.binance.com/api/v3/klines"
KRAKEN_URL = "https://api.kraken.com/0/public/OHLC"


def _symbol(asset: str) -> str:
    return asset.replace("/", "").replace("-", "").upper()


def _kraken_pair(asset: str) -> str:
    base, _, quote = asset.replace("-", "/").partition("/")
    base = {"BTC": "XBT"}.get(base.upper(), base.upper())
    return f"{base}{quote.upper()}"


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
    try:
        source, closes = await _fetch_binance(asset)
    except httpx.HTTPError:
        source, closes = await _fetch_kraken(asset)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "asset": asset,
        "timestamp": int(time.time()),
        "price": closes[-1],
        "previous_price": closes[-2] if len(closes) > 1 else closes[-1],
        "rsi": _rsi(closes),
        "close_count": len(closes),
    }
    return require_schema(payload, "price")


async def _fetch_binance(asset: str) -> tuple[str, list[float]]:
    params = {"symbol": _symbol(asset), "interval": "1m", "limit": 60}
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        response = await client.get(BINANCE_URL, params=params)
        response.raise_for_status()
        rows = response.json()

    return "binance_public", [float(row[4]) for row in rows]


async def _fetch_kraken(asset: str) -> tuple[str, list[float]]:
    params = {"pair": _kraken_pair(asset), "interval": 1}
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        response = await client.get(KRAKEN_URL, params=params)
        response.raise_for_status()
        data = response.json()

    errors = data.get("error") or []
    if errors:
        raise RuntimeError(f"kraken returned errors: {errors}")

    result = data.get("result") or {}
    pair_key = next((key for key in result if key != "last"), None)
    rows = result.get(pair_key, []) if pair_key else []
    closes = [float(row[4]) for row in rows[-60:]]
    if not closes:
        raise RuntimeError(f"kraken returned no OHLC rows for {asset}")
    return "kraken_public", closes
