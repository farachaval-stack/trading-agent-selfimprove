# Phase 6: Install Hermes On Railway

Goal: make the `hermes` command available inside the Railway worker environment. Do not install Hermes locally.

Find the current official Hermes installation method for Linux containers. Use the official source only. Add the install step to `Dockerfile` after uv is installed and before the final command.

Redeploy:
```bash
railway up --detach
```

Verify on Railway:
```bash
railway run hermes --version
railway run python -m hermes_trading.reflect --hermes --dry-run
```

If `hermes` is not found, stop and report the install line that failed. Do not switch to local Hermes.

Finish with:
```text
Hermes is installed on Railway and available to the worker.
```
