# Phase 1: Environment Check

Goal: verify the local machine can scaffold and deploy the worker from this repository.

Detect OS:
- mac: `uname -s` returns `Darwin`; open command is `open <target>`
- linux: `uname -s` returns `Linux`; open command is `xdg-open <target>`
- windows: `echo $env:OS` returns `Windows_NT`; open command is `start <target>`

Say: `OS detected - you're on {Mac/Linux/Windows}. Let's build your trading agent.`

Run and summarize in one line:
```bash
git --version
node --version
uv --version
```

If Git is missing, open `https://git-scm.com/downloads` and wait for confirmation.
If Node.js is missing, open `https://nodejs.org/en/download` and wait for confirmation.
If uv is missing, install it with the current official Astral command for the detected OS, refresh PATH in the same terminal, and verify `uv --version`.

Finish with:
```text
Environment ready: {OS} / Git / Node.js / uv
```
