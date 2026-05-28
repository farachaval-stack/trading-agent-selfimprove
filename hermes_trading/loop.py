from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Awaitable, Callable

import aiofiles

from .adapters import macro, news, onchain, price
from .adapters.base import SchemaError
from .config import load_yaml
from .paths import HEARTBEAT_FILE, TRADES_FILE, ensure_state_dirs


FetchFn = Callable[[str], Awaitable[dict[str, Any]]]


class CircuitBreak(RuntimeError):
    pass


async def run_loop(goal_path, strategy_path, asset: str, once: bool = False) -> None:
    ensure_state_dirs()
    print(f"Booting hermes-trading worker for {asset} in {os.getenv('HERMES_TRADING_MODE', 'paper')} mode", flush=True)
    consecutive_failures = 0

    while True:
        try:
            goal = load_yaml(goal_path)
            strategy = load_yaml(strategy_path)
            snapshot = await _fetch_all(asset)
            trade = _evaluate(asset, strategy, snapshot)
            if trade:
                await _append_jsonl(TRADES_FILE, trade)
            await _write_heartbeat(asset, strategy, snapshot, trade)
            consecutive_failures = 0
        except SchemaError:
            raise
        except Exception as exc:
            consecutive_failures += 1
            print(f"worker failure {consecutive_failures}/5: {exc}", flush=True)
            if consecutive_failures >= 5:
                raise CircuitBreak("circuit break after 5 consecutive failures") from exc

        if once:
            return
        await asyncio.sleep(int(goal.get("loop_interval_seconds", 60)) if "goal" in locals() else 60)


async def _fetch_all(asset: str) -> dict[str, Any]:
    adapters: dict[str, FetchFn] = {
        "price": price.fetch,
        "onchain": onchain.fetch,
        "news": news.fetch,
        "macro": macro.fetch,
    }
    results = {}
    for name, fetcher in adapters.items():
        results[name] = await _with_retries(name, fetcher, asset)
    return results


async def _with_retries(name: str, fetcher: FetchFn, asset: str) -> dict[str, Any]:
    delay = 1.0
    for attempt in range(1, 4):
        try:
            return await fetcher(asset)
        except SchemaError:
            raise
        except Exception:
            if attempt == 3:
                raise
            await asyncio.sleep(delay)
            delay *= 2
    raise RuntimeError(f"{name} retries exhausted")


def _evaluate(asset: str, strategy: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any] | None:
    price_payload = snapshot["price"]
    indicator = strategy.get("entry", {}).get("indicator", "rsi")
    threshold = float(strategy.get("entry", {}).get("threshold", 30))
    direction = strategy.get("entry", {}).get("direction", "long")

    if indicator != "rsi" or direction != "long":
        return None

    rsi = float(price_payload["rsi"])
    if rsi > threshold:
        return None

    entry = float(price_payload["previous_price"])
    exit_price = float(price_payload["price"])
    raw_return = ((exit_price - entry) / entry) * 100 if entry else 0.0
    stop_loss = float(strategy.get("stop_loss_pct", 2.0))
    capped_return = max(raw_return, -stop_loss)

    return {
        "trade_id": f"{int(time.time())}-{asset.replace('/', '')}",
        "status": "closed",
        "asset": asset,
        "strategy_version": strategy.get("version", "01"),
        "opened_at": int(time.time()) - 60,
        "closed_at": int(time.time()),
        "entry_price": round(entry, 8),
        "exit_price": round(exit_price, 8),
        "return_pct": round(capped_return, 6),
        "signal": {"indicator": "rsi", "value": round(rsi, 4), "threshold": threshold},
        "mode": os.getenv("HERMES_TRADING_MODE", "paper"),
    }


async def _append_jsonl(path, payload: dict[str, Any]) -> None:
    async with aiofiles.open(path, "a", encoding="utf-8") as handle:
        await handle.write(json.dumps(payload, sort_keys=True) + "\n")


async def _write_heartbeat(asset: str, strategy: dict[str, Any], snapshot: dict[str, Any], trade: dict[str, Any] | None) -> None:
    payload = {
        "timestamp": int(time.time()),
        "asset": asset,
        "strategy_version": strategy.get("version"),
        "last_price": snapshot["price"].get("price"),
        "last_rsi": snapshot["price"].get("rsi"),
        "last_trade_id": trade.get("trade_id") if trade else None,
    }
    async with aiofiles.open(HEARTBEAT_FILE, "w", encoding="utf-8") as handle:
        await handle.write(json.dumps(payload, indent=2, sort_keys=True))
