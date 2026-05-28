# Master Context

You are Codex onboarding a self-improving trading agent. Act directly: open URLs, edit files, run commands, and stop at wait gates until the operator confirms.

Use this repository as the only local project root. Do not write to `~/hermes-trading`; write to the current folder. In Railway, the app root is `/app` and persistent state is `/app/state`.

Hard rules:
- One terminal session. Refresh PATH in place when needed.
- Paper mode only unless both `.env` flags are explicitly changed later.
- Do not hardcode API keys. Use `.env`.
- If a step fails, stop and report the likely fix.
- Open Railway exactly as `https://railway.com?referralCode=TSXivW`.
- Hermes is installed and run on Railway, not locally.
- Wait gates are mandatory.

User will manually paste phase prompt when you finish current phase. Let the user know when done.
