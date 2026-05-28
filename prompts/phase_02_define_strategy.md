# Phase 2: Define Strategy

Goal: collect the strategy contract and write `state/goal.yaml`.

Ask one question at a time and wait after each answer.

1. Asset: what ccxt-style ticker should the worker trade? Default `BTC/USDT`.
2. Target return in 30 days: A `3%`, B `5%` default, C `10%`, or custom.
3. Max drawdown: A `5%`, B `8%` default, C `15%`, or custom.
4. Minimum Sharpe: A `1.0`, B `1.2` default, C `2.0`.
5. Reflection cadence: reflect every how many closed trades? Default `5`.

Read back:
```text
Your strategy: trade {asset}. Success is +{return}% in 30 days with at least Sharpe {sharpe}. Failure is {drawdown}% drawdown. Every {reflection} closed trades, Hermes will review outcomes and change exactly one variable. Confirm to lock it in.
```

Wait for confirmation. Then write `state/goal.yaml`:
```yaml
asset: "{asset}"
target_return_30d: {return_decimal}
max_drawdown: {drawdown_decimal}
min_sharpe: {sharpe}
failure_below: -0.04
reflection_every: {reflection}
one_variable_only: true
```

Finish with:
```text
Strategy locked: state/goal.yaml
```
