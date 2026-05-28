from __future__ import annotations

import csv
import io
import time
from typing import Any

import httpx

from .base import SCHEMA_VERSION, require_schema


STOOQ_SPY_URL = "https://stooq.com/q/l/?s=spy.us&i=d"
STOOQ_VIX_URL = "https://stooq.com/q/l/?s=vix&i=d"


async def _quote(url: str) -> dict[str, str]:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(response.text)))
    return rows[0] if rows else {}


async def fetch(asset: str = "BTC/USDT") -> dict[str, Any]:
    spy = await _quote(STOOQ_SPY_URL)
    vix = await _quote(STOOQ_VIX_URL)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "stooq_public",
        "asset": asset,
        "timestamp": int(time.time()),
        "spy_close": _to_float(spy.get("Close")),
        "vix_close": _to_float(vix.get("Close")),
    }
    return require_schema(payload, "macro")


def _to_float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "N/D") else None
    except ValueError:
        return None
