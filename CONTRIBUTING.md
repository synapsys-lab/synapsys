# Contributing to Synapsys

Thank you for your interest in contributing. This document covers the workflow
for reporting issues, proposing features, and submitting pull requests.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Reporting Issues](#reporting-issues)
- [Development Setup](#development-setup)
- [Branch Policy](#branch-policy)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
By participating you agree to abide by its terms.

---

## Reporting Issues

Before opening a new issue, search the
[issue tracker](https://github.com/synapsys-lab/synapsys/issues) to avoid
duplicates. Include:

- A minimal reproducible example
- The Python and synapsys versions (`python --version`, `pip show synapsys`)
- The full traceback if applicable

---

## Development Setup

We use [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
git clone https://github.com/synapsys-lab/synapsys.git
cd synapsys
uv sync --extra dev
```

Verify the setup:

```bash
uv run pytest          # all tests must pass
uv run ruff check .    # no lint errors
uv run mypy synapsys   # no type errors
```

---

## Branch Policy

| Branch | Created from | Merges into | Purpose |
|--------|-------------|-------------|---------|
| `main` | — | — | Always releasable — no direct pushes |
| `develop` | `main` | — | Integration buffer — default PR target |
| `feat/<name>` | `develop` | `develop` (PR) | New features |
| `fix/<name>` | `develop` | `develop` (PR) | Non-urgent bug fixes |
| `docs/<name>` | `develop` | `develop` (PR) | Documentation changes |
| `chore/<name>` / `ci/<name>` | `develop` | `develop` (PR) | Tooling, deps, CI |
| `release/vX.Y.Z` | `develop` | `main` + back-merge `develop` | Release stabilisation |
| `hotfix/vX.Y.Z` | tag on `main` | `main` + back-merge `develop` | Urgent production fix |

**All topic branches must be created from `develop`, not `main`.**
Pull requests from external contributors must target `develop`.

---

## Submitting a Pull Request

1. Fork the repository and create your branch from `main`.
2. Make your changes with tests covering new behaviour.
3. Ensure `pytest`, `ruff check`, and `mypy` all pass locally.
4. Open a PR with a clear description of **what** and **why**.
5. Link any related issues with `Closes #<number>`.

PRs that reduce test coverage or introduce `mypy` strict errors will not be
merged.

---

## Code Style

- Formatter / linter: **Ruff** (`ruff check --fix` and `ruff format`)
- Type hints: **required** for all public APIs
- Docstrings: **Google style**
- Line length: **88** characters

---

## Testing

```bash
uv run pytest                          # full suite
uv run pytest tests/core/ -v          # single module
uv run pytest --cov=synapsys          # with coverage
```

New features must include unit tests. Bug fixes must include a regression test.

---

## Documentation

Documentation lives in `website/docs/`. The site is built with
[Docusaurus 3](https://docusaurus.io/).

```bash
cd website
npm install
npm run start   # live preview at http://localhost:3000/synapsys/
```

API reference pages are in `website/docs/api/`. If you add a new public class
or function, update the corresponding API doc and the module overview table
in the homepage (`website/src/pages/index.tsx`).
