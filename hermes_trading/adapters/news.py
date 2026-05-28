from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from .base import SCHEMA_VERSION, require_schema


RSS_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/"


async def fetch(asset: str = "BTC/USDT") -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(RSS_URL)
        response.raise_for_status()

    root = ET.fromstring(response.text)
    items = root.findall("./channel/item")[:5]
    headlines = []
    for item in items:
        title = item.findtext("title")
        if title:
            headlines.append(title)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "coindesk_rss",
        "asset": asset,
        "timestamp": int(time.time()),
        "headline_count": len(headlines),
        "headlines": headlines,
    }
    return require_schema(payload, "news")
