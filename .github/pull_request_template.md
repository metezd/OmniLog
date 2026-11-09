## Summary

<!-- What changes and why, in a few short sentences. -->

## Linked issues

Closes #

## Changes

<!-- Group the changes by area. The list must match the files in this pull request. -->

-

## How it was tested

- [ ] Backend: `python -m pytest tests/requirements -v --cov=backend/app --cov-fail-under=70`
- [ ] Database: `alembic upgrade head` and `alembic check` (when models or migrations changed)
- [ ] Frontend: `npm run lint`, `npx tsc --noEmit`, `npm test` and `npm run build`
- [ ] Not run locally (write which checks and why)

## Checklist

- [ ] The description matches the files that changed
- [ ] README and docs are updated when setup, commands, environment variables, endpoints or the data model change
- [ ] New endpoints have tests for success and for the main errors (401, 404, 409, 422)
- [ ] Migrations have a working `downgrade`
- [ ] No new library or framework outside the Charter, or the reason is written above
- [ ] No secrets or personal data, and comments are in English
- [ ] The change is one of the Charter user stories, or it is named as an extension above
