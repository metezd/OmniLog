---
name: code-review
description: Review pull requests for OmniLog, a FastAPI, PostgreSQL and Next.js course project. Use when reviewing backend, migration, test, CI, Docker or documentation changes.
---

# OmniLog code review

Review the pull request against the rules below. Report only real problems and give a concrete fix for each one. Do not comment on style choices that match the existing code.

## Project rules

- The tech stack is fixed by `docs/CHARTER.md`. Flag any new framework, service or library that the Charter does not list.
- PostgreSQL is the only database. Flag SQLite usage, including test-only SQLite shortcuts.
- Code comments, docstrings and documentation are written in English.
- Files use LF line endings (see `.gitattributes`).

## Security

- Secrets such as `SECRET_KEY`, passwords and API keys must never be committed or have a public default value.
- Passwords are hashed and never returned in any response or log.
- Protected endpoints must require a valid JWT. The user id comes from the token, never from the request body.
- Check CORS settings, input validation and error responses that could leak internal details.

## Backend and database

- Every model change needs an Alembic migration. `alembic check` must report no differences.
- Migrations must have a working `downgrade`, including PostgreSQL enum types.
- Do not add an index to a primary key column, because it is already indexed.
- Request and response bodies are Pydantic schemas. Endpoints follow the contract in `tests/requirements`.
- Settings are read from environment variables in `app/core/config.py`, not hardcoded in other modules.

## Tests and CI

- Tests must use the separate test database and must not touch development data.
- A new endpoint needs tests for the success case and the main error cases (401, 404, 409 or 422).
- CI changes must keep the backend, frontend and Docker Compose jobs working. Check that new environment variables are set in `ci.yml`.

## Documentation

- The pull request description must match the files that are actually changed.
- Update `README.md` when setup steps, commands or environment variables change.
