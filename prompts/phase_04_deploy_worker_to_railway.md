# Phase 4: Deploy Worker To Railway

Goal: deploy the paper trading worker to Railway with persistent state.

Open exactly:
```text
https://railway.com?referralCode=TSXivW
```

Say: `Sign in or sign up if needed. Tell me when you are at the Railway dashboard.`

Wait for confirmation.

Install Railway CLI if missing using the current official Railway instructions for the detected OS. Verify:
```bash
railway --version
```

Login:
```bash
railway login
```

Wait for the prompt to return.

From this repository:
```bash
railway init
railway volume create --name hermes-state --mount /app/state
railway up --detach
railway logs
```

When logs show the worker boot line, stop tailing. If build or boot fails, print the last 30 log lines and stop.

Finish with:
```text
Worker deployed. Service is live on Railway.
```
