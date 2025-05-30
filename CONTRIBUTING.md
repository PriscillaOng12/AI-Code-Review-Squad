# Contributing to ai‑code‑review‑squad

Thanks for taking the time to contribute!  We welcome bug reports, feature requests, documentation improvements and pull requests from the community.  This document describes how to get set up for local development and our guidelines for contributions.

## Development environment

1. Clone the repository and copy `.env.example` to `.env`.  No secrets are required to run locally in mock mode.
2. Install Python 3.11 and Node 18 on your machine.  Alternatively, use the provided `docker-compose.yml` for an isolated environment.
3. Install pre‑commit hooks by running `pre-commit install`.  This will automatically run linters and type checkers on each commit.
4. Run `make up` to start the full stack (PostgreSQL, Redis, backend, frontend) and apply database migrations.

## Pull request process

* Always open an issue or discuss proposed changes before beginning significant work.
* Write unit and integration tests for any new features or bug fixes.  All tests must pass (`make test`).
* Run the linter and formatter before pushing: `make lint`.
* Update documentation as appropriate in `docs/` and the README.
* Sign your commits with a clear message describing your change.  We use semantic‑release style commit messages (feat:, fix:, chore: etc.) to automatically generate the CHANGELOG.
* Submit your pull request to the `main` branch.  CI will run automatically.

Thank you for contributing!