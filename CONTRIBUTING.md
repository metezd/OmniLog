# Contributing

This guide explains how a change goes from an idea to the `main` branch. The rules are short on purpose.

## Workflow

1. Start from an issue. Every change has one, so the reason is written down.
2. Create a branch from an up to date `main`.
3. Make small commits. Each commit builds and passes the tests on its own.
4. Open a pull request. Link the issue with `Closes #123` in the description.
5. Wait for the CI checks and the review. Fix what the review finds with new commits.
6. Merge with **Rebase and merge**, so the commits stay as they were written.

Keep a pull request to one topic. A reviewer can read 10 files well and cannot read 80 files well. When a change has a database migration, put it in its own commit.

## Branch names

Use `type/short-description` in lower case with hyphens.

| Type | Use |
|---|---|
| `feat/` | New behavior for users |
| `fix/` | A bug fix |
| `chore/` | Tooling, dependencies, project setup |
| `docs/` | Documentation only |
| `test/` | Tests only |

Examples: `feat/title-description-and-genres`, `fix/login-redirect`, `chore/project-tooling`.

## Commit messages

One line in the form `type(scope): subject`. We follow Conventional Commits.

- **type:** `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`
- **scope:** `backend`, `frontend`, or none when the change is for the whole repository
- **subject:** starts with a lower case verb in the imperative, has no period at the end, and the whole line is at most 72 characters

Good: `feat(backend): add DELETE /library/{id} with a diary event`

Not good: `Fixed some stuff.`

## Pull requests

The pull request template asks for a summary, the linked issues, the list of changes and how the change was tested. Fill all of it in. The description must match the files that changed. Say it clearly when a pull request:

- adds a library or framework that is not in the Charter,
- adds a feature that is not one of the user stories,
- needs a migration or a new environment variable.

Add the labels of the area (`backend`, `frontend`, `ci`, `documentation`) and the milestone of the roadmap step.

## Checks before you push

The CI runs the same checks. Running them first saves a round trip.

```bash
# Backend, from the repository root with the virtual environment active
python -m pytest tests/requirements -v --cov=backend/app --cov-fail-under=70
cd backend && alembic upgrade head && alembic check

# Frontend
cd frontend
npm run lint
npx tsc --noEmit
npm test
npm run build
npm audit --omit=dev --audit-level=high
```

## Code style

- Comments, commit messages and documentation are in English.
- Files use LF line endings (`.gitattributes` enforces this).
- A new endpoint comes with tests for success and for the main errors (401, 404, 409, 422).
- A migration has a working `downgrade`.
- Do not commit secrets. Settings come from environment variables, as in `.env.example`.

## Labels and milestones

- Labels: `backend`, `frontend`, `ci`, `dependencies`, `security`, `documentation`, `tests`, `enhancement`, `bug`, `scope-extension`, `follow-up`.
- Milestones follow the roadmap in the README (Step 0 to Step 9).
