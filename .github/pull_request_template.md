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

## AI assistance

<!-- See "AI assistance" in CONTRIBUTING.md. Add the label `ai-assisted` when AI helped. -->

- [ ] None
- [ ] AI helped
- [ ] AI wrote most of it

Tool and model:

What I checked by hand:

What the AI got wrong and I fixed:

## Checklist

- [ ] The description matches the files that changed
- [ ] `CHANGELOG.md` has a line under `[Unreleased]` when users or teammates can notice the change
- [ ] README and docs are updated when setup, commands, environment variables, endpoints or the data model change
- [ ] New endpoints have tests for success and for the main errors (401, 404, 409, 422)
- [ ] Migrations have a working `downgrade`
- [ ] No new library or framework outside the Charter, or the reason is written above
- [ ] No secrets or personal data, and comments are in English
- [ ] The change is one of the Charter user stories, or it is named as an extension above
- [ ] I can explain every line of this change, including the parts that AI wrote
