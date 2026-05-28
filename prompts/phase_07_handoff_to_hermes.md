# Phase 7: Hand Off To Hermes

Goal: start Railway-hosted Hermes as the brain for the deployed worker.

Render `state/hermes_briefing.md` from `prompts/hermes_briefing_template.md`, replacing all placeholders with real values from `state/goal.yaml` and Railway project metadata.

Start Hermes on Railway using the verified Phase 6 command path. Feed it `state/hermes_briefing.md` as the initial briefing. Prefer a persistent Railway service/process for Hermes; use `railway run` only if that is the verified Hermes hosting mode.

Hermes must:
- watch Railway logs every 30 minutes,
- reflect after `reflection_every` new closed trades,
- read `/app/state/trades.jsonl` and `/app/state/strategy.yaml`,
- change exactly one variable,
- save prior versions to `/app/state/history/`,
- append hypotheses to `/app/state/hypotheses.jsonl`,
- redeploy with `railway up --detach` when needed.

After Hermes accepts the briefing, print:
```text
Self-improving trading agent - deployed.

Worker: Railway paper mode
Strategy: {asset} / +{return}% target per 30d / max DD {drawdown}% / min Sharpe {sharpe}
Brain: Hermes on Railway, reflecting every {reflection_every} trades
Restart: Railway restarts the worker on crash and after deploys

Day-after check-in:
  railway logs
  railway run cat /app/state/strategy.yaml
  railway run ls /app/state/history/

Go live later:
  set Railway variable HERMES_TRADING_MODE=live
  set Railway variable HERMES_TRADING_I_ACCEPT_RISK=true
  railway up --detach

Hermes is watching. The agent is running.
```
