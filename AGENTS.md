# AGENTS Instructions

This repository contains the Expeta architecture reasoning system written in Python. The following guidelines apply to all code and documentation in this project.

## Setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `env.example` to `.env` and fill in your API keys (OpenAI, Qdrant, etc.).

## Running

Use `tools/system/run_expeta.py` as the main entry point:
```bash
# run the full pipeline
python tools/system/run_expeta.py full -i data/input -o data/output/architecture_full

# global reasoning only
python tools/system/run_expeta.py global -i data/input -o data/output/architecture

# local reasoning for one entity
python tools/system/run_expeta.py local -e "UserService" -i data/input -o data/output/entity
```

Logging is centralised via `common.print_log`. Avoid using `print` directly.

## Testing

The project uses `pytest`. Run tests with:
```bash
pytest          # run all tests
pytest tests/unit/          # unit tests
pytest tests/integration/   # integration tests
```
Alternatively, use the helper script:
```bash
./scripts/testing/run_tests.sh
```
Some integration tests require network access and valid API keys.

## Code Style

- Follow PEP8 with 4‑space indentation.
- Use descriptive variable and function names.
- Keep functions small and focused.
- Document public functions and modules with docstrings.
- Use the logging utilities from `common` instead of direct prints.

## Contribution

- Commit messages should be short and use the imperative mood, optionally prefixed with `feat:`, `fix:`, `docs:`, etc.
- All Pull Requests should describe what changed and mention any tests run.
- Run `pytest` before submitting a PR.


