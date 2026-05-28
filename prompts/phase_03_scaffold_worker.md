# Phase 3: Scaffold Worker

Goal: ensure the local worker code is complete and runnable from this repository.

Verify or create:
- `.env`
- `pyproject.toml`
- `Dockerfile`
- `hermes_trading/`
- `state/goal.yaml`
- `state/strategy.yaml`
- `state/trades.jsonl`
- `state/hypotheses.jsonl`
- `state/history/`
- `state/heartbeat.json`

Required behavior:
- `python -m hermes_trading.run` starts a paper-mode loop.
- `python -m hermes_trading.reflect --fallback` changes exactly one strategy variable and appends a hypothesis.
- `python -m hermes_trading.reflect --hermes` calls the Railway-installed `hermes` command when available.
- Adapters expose `async def fetch(...) -> dict` and include `schema_version`.
- Schema mismatch halts the loop with `SchemaError`.

Install dependencies if needed:
```bash
uv sync
```

Smoke test:
```bash
uv run python -m hermes_trading.reflect --fallback
uv run python -m hermes_trading.run --once
```

Finish with:
```text
Worker scaffold ready in the current folder.
```
