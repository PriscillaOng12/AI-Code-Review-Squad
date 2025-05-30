# Onboarding Guide

Welcome to ai‑code‑review‑squad!  This guide helps new contributors and operators get up to speed quickly.

## Setting up your local environment

1. **Clone the repo** and install pre‑commit: `pip install pre-commit` then run `pre-commit install`.
2. **Install prerequisites:** Python 3.11, Node 18 and Docker.  A recent version of `make` is also required.
3. **Create your `.env`:** copy `.env.example` to `.env`.  For local work, you may leave all secrets blank and set `MOCK_LLM=true`.
4. **Start the stack:** run `make up`.  This will build images, apply migrations, seed sample data and start services.
5. **Browse the UI:** open http://localhost:5173.  Use the Demo Review button to trigger a review against the sample repository.
6. **Run tests:** execute `make test` to run backend and frontend tests.  All tests should pass.
7. **Review code style:** run `make lint`.  Fix any issues before committing.  Pre‑commit will enforce style automatically.

## Repository layout

Refer to the repository tree in the root `README.md` for an overview of where components live (backend, frontend, docs, infra, etc.).

## Development tips

- Use the `app/demo` directory to explore sample payloads and test the webhook flow.  The `sample_repos/python_small` folder contains a small Python project used for testing.
- The `Makefile` includes helpful targets such as `make migrate` (apply DB migrations), `make seed` (seed demo data), `make lint`, `make k6` (run load tests), and `make analytics-export` (export analytics data).
- When implementing new agents, follow the pattern in `app/services/agents/base.py` and register the agent in `app/services/orchestrator.py`.
- API clients are generated in the frontend at `frontend/src/lib/api.ts`.  Keep models in sync with backend schemas.
- Documentation lives in the `docs/` directory.  Update relevant sections when adding new features.

If you have questions or run into issues, open a discussion or reach out to the maintainers.  Happy hacking!