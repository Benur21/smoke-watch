# Repository Guidelines

## Project Structure & Module Organization
This repository contains two independent SmokeWatch variants:
- `smokewatch_vCopilot/` uses a `pi/` subfolder, `requirements.txt`, and its own `smokewatch.service`.
- `smokewatch_vClaude/` keeps a flatter layout and has its own `smokewatch.service`.
- `setup_smokewatch.py` lives at the repo root and bootstraps the chosen variant on a Raspberry Pi.
- `assets/` stores dashboard screenshots used by the top-level `README.md`.

Keep changes variant-scoped unless the behavior is intentionally shared.

## Build, Test, and Development Commands
- `python3 setup_smokewatch.py` runs the root bootstrapper, asks which variant to use, rewrites the service file paths, and starts the service.
- `python3 -m py_compile setup_smokewatch.py` checks Python syntax quickly.
- `python3 smokewatch_vCopilot/pi/main.py` or `python3 smokewatch_vClaude/pi/main.py` runs a variant directly for local smoke testing.

There is no formal build system or automated test suite in the repo.

## Coding Style & Naming Conventions
Use Python 3, 4-space indentation, and ASCII text unless a file already depends on Portuguese Unicode content. Prefer small, explicit functions and keep path handling absolute when touching systemd or Raspberry Pi setup code. Name files and folders with the existing pattern: `snake_case.py`, `smokewatch.service`, `vClaude`, `vCopilot`.

## Testing Guidelines
Verify edits with syntax checks and a manual run of the affected variant. When changing startup or service logic, confirm the generated `WorkingDirectory` and `ExecStart` values match the clone path on the Pi. If dashboard output changes, capture a screenshot before merging.

## Commit & Pull Request Guidelines
Commit messages in this repo are short and direct, often lowercase and imperative, such as `fix1 setup_smokewatch.py` or `fix readme root`. Keep commits focused on one change. PRs should state which variant is affected, summarize the behavioral impact, and include screenshots for UI changes or service output where relevant.

## Configuration Notes
Do not hardcode local machine paths in source files unless they are intentionally generated for the Raspberry Pi install flow. Treat `smokewatch_vCopilot/requirements.txt` as a reference file, not as part of the bootstrap install path.
