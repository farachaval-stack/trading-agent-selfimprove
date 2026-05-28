from __future__ import annotations

import time
from typing import Any

import httpx

from .base import SCHEMA_VERSION, require_schema


COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "DOGE": "dogecoin",
}


def _base(asset: str) -> str:
    return asset.split("/")[0].split("-")[0].upper()


async def fetch(asset: str = "BTC/USDT") -> dict[str, Any]:
    coin_id = COINGECKO_IDS.get(_base(asset), "bitcoin")
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    market = data.get("market_data", {})
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "coingecko_public",
        "asset": asset,
        "timestamp": int(time.time()),
        "market_cap_usd": market.get("market_cap", {}).get("usd"),
        "volume_24h_usd": market.get("total_volume", {}).get("usd"),
        "price_change_24h_pct": market.get("price_change_percentage_24h"),
    }
    return require_schema(payload, "onchain")
