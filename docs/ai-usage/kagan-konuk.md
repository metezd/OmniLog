# AI Usage Notes: Kaðan Konuk (`KaganKonuk`)

Part of the review checklist in [#252] (section E). Issue: [#314]. These notes record where AI was used in my work, how it was checked, and which AI mistakes were caught. Role: Backend Engineer.

## Tools

| Tool | Model | How it was used | Period / Work |
|---|---|---|---|
| Gemini (chat / assistant) | Gemini | Interactive assistance for code refactoring, test verification, debugging environment/test setup, and drafting documentation; all repository changes, commands, and commits were reviewed and run by me | 2026: [#305], [#216], [#156], PyJWT migration (`21650d1`, `991d11a`), catalog tests (`b374e8f`), and this file ([#314]) |

Only facts backed by repository commits, issues, and test/CI runs are listed below.

## Work done with AI

| Work | What the AI did | How it was checked |
|---|---|---|
| [#305] Remove duplicate list routes (`fix/d10-remove-duplicate-list-routes`) | Helped design the OpenAPI duplicate `operation_id` guard test (`tests/test_route_registration.py`, commit `bbd9465`), verify that `journal_service` already handled list deletion and item removal diary/cache logic, and remove dead `backend/app/api/lists.py` and `backend/app/services/list_service.py` plus router wiring in `backend/app/main.py` (commit `e2e8744`) | Ran Red/Green `pytest` checks (`tests/test_route_registration.py`, `tests/requirements/test_epic2_removal.py`, and all 974 tests in `tests/requirements`), inspected `git diff` / `git status`, and verified PR checks |
| [#216] Cap `GET /stats` playtime histogram (`9cf04d6`) | Helped structure the histogram cap logic (`100+h` and `21` buckets) and edge cases | Inspected the diff and ran stats/requirements tests |
| [#156] SonarQube quality gate cleanup (`df87429`) | Helped identify and clean up flagged code smells across backend code | Inspected `git diff` and ran quality/test checks |
| PyJWT migration (`21650d1`, `991d11a`) | Helped migrate authentication tokens from `python-jose` to `PyJWT`, update test imports, and add CI `pip-audit` | Ran requirement and auth test suites and verified CI checks |
| Catalog search/details tests (`b374e8f`) | Helped write test cases for library add sync and backfill | Ran catalog requirement tests and inspected test assertions |
| This file, [#314] (`docs/ai-usage/kagan-konuk.md`) | Helped inspect `docs/ai-usage/` conventions and commit history and draft a factual, traceable AI usage document | Checked every linked commit and issue against local `git log` and `docs/ai-usage/README.md` |

## AI mistakes that were caught

| Mistake | How it was caught | Fix | Severity |
|---|---|---|---|
| Initial test runs in `.venv` failed or hit setup gaps due to missing environment variables (`DATABASE_URL`, `SECRET_KEY`), missing `pgvector` in local runs, or `--cov` (`pytest-cov`) not installed in `.venv` | Running `pytest` directly in local `.venv` and inspecting error output | Set up the test environment/commands explicitly and ran `pytest tests/requirements -v` (974 passed) without assuming optional plugins | Minor |
| Duplicate list deletion / item-removal paths existed across `lists.py` / `list_service.py` and `journal.py` / `journal_service.py` after earlier list work (`0d7c833`, `bd6e665`) | Code inspection of `backend/app/main.py`, `backend/app/api/journal.py`, `backend/app/services/journal_service.py`, and running the OpenAPI guard test | Removed `lists.py` and `list_service.py` and unwired `lists.router` in `e2e8744`, keeping `journal_service` as the single path | Medium |
| PR title for `#305` initially used `Fix/d10 remove duplicate list routes`, failing the `Pull request names / PR title` Conventional Commits check | CI check `Pull request names / PR title` failed with exit code 1 | Renamed PR title to `refactor(api): remove duplicate list delete routes (#305)`, after which CI checks passed | Minor |

## Limits

- AI never merges pull requests or bypasses branch protection and CI checks; every commit is reviewed and pushed by me.
- I do not trust AI with unverified claims, secrets/credentials, or skipping test/CI verification—every suggested change is checked against actual code, tests, and `git diff`.
- I must be able to explain every line of code and test added in my pull requests during code review ([#309]).

[#216]: https://github.com/metezd/OmniLog/issues/216
[#252]: https://github.com/metezd/OmniLog/issues/252
[#305]: https://github.com/metezd/OmniLog/issues/305
[#309]: https://github.com/metezd/OmniLog/issues/309
[#314]: https://github.com/metezd/OmniLog/issues/314