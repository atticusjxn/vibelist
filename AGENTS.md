# Repository Guidelines

## Project Structure & Module Organization
The application runs through `main.py`, which orchestrates portfolio loading, sentiment analysis, and email delivery. Key directories to know:
- `src/vibelist/` holds the core modules (`config.py`, `stock_data.py`, `sentiment.py`, `analyzer.py`, `email_generator.py`, `email_sender.py`, `utils.py`) and should contain all production logic.
- `templates/` stores `email_template.html`, used by the generator for the retro digest layout.
- `config.json` persists user-specific JSON portfolios; keep example payloads lightweight.
- `logs/` captures runtime output; clean up noisy artifacts before committing.
- `tests/` contains Pytest suites; mirror the package layout when adding new tests.

## Build, Test, and Development Commands
Run `pip install -r requirements.txt` to sync both runtime and dev dependencies. Helpful commands:
- `python main.py --create-sample` — scaffold `config.json` for local runs.
- `python main.py --test` — validate config, API keys, and email delivery via a dry run.
- `python main.py` — produce the daily digest using the active configuration.
- `pytest tests/ -v --cov=src` — execute unit tests with coverage targeting production code.
- `black src/ main.py` and `flake8 src/ main.py` — format and lint prior to review.

## Coding Style & Naming Conventions
Follow Black’s default 88-character line width and 4-space indentation. Modules and functions stay snake_case, classes use PascalCase, constants are SCREAMING_SNAKE_CASE, and environment variables live in `.env`. Keep Jinja templates HTML-first and avoid embedding application logic there.

## Testing Guidelines
Tests belong in `tests/` with files named `test_<module>.py` and functions prefixed `test_`. Use pytest fixtures for API stubs and sample portfolios, and add coverage for xAI (Grok) and Resend integrations via mocked responses. Ensure `pytest ... --cov=src` remains green before opening a pull request.

## Commit & Pull Request Guidelines
With no shared history in this snapshot, default to a conventional, imperative subject line (`type: short summary`) and add focused body bullets when context helps reviewers. Reference issue IDs in the footer (`Refs #123`) and squash fixups locally. Pull requests must describe the change, list validation commands run, and attach screenshots or sample email snippets when UI-facing output changes.

## Configuration & Security Tips
Never commit populated `.env` files or real `config.json` payloads; rely on `.env.example` and `python main.py --create-sample` instead. Rotate API keys promptly if logs expose them, and redact sensitive fields before sharing stack traces. For GitHub Actions, store secrets in repository settings and audit workflow changes that touch credentials. Use `XAI_MODEL`/`XAI_API_BASE_URL` to steer Grok model selection without touching source, and prefer `PORTFOLIO_JSON` for personal holdings in CI.
