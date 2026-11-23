# TDD Evidence

Part of the review checklist in #252 (section D). Everything here comes from the git history of `main` and can be checked with the commands in section 4.

## 1. How the project used test-first

The requirement tests were written before the features, in commit `fa5203b` (12.10.2026). Features that did not exist yet were marked with `not_built(...)` from commit `c67cc8a` (20.10.2026). This made them expected failures (xfail), so the CI stayed green. The pull request that built a story removed its mark, and from then on the test had to pass. The helper was removed in `f4a2dc9` (17.11.2026), when no mark was left.

**How far this goes:** this is test-first at the level of user stories and acceptance tests. The history does not show a strict red-green-refactor cycle for every function, and many edge-case tests were added after the code. We do not claim that the whole project was built with TDD.

## 2. Tests came before the code

| Story | First test commit | First code commit | Code file |
|---|---|---|---|
| US-02/03 Accounts | `fa5203b` 12.10 | `f994683` 15.10 | `backend/app/api/auth.py` |
| US-08 Catalog | `fa5203b` 12.10 | `29e1e8b` 16.10 | `backend/app/api/catalog.py` |
| US-10/12 Chapters | `fa5203b` 12.10 | `4222d3d` 17.10 | `backend/app/api/chapters.py` |
| US-13 Recommendations | `fa5203b` 12.10 | `34ef49f` 07.11 | `backend/app/api/recommendations.py` |
| US-15 Statistics | `fa5203b` 12.10 | `caf5749` 08.11 | `backend/app/api/stats.py` |
| US-14 Spoiler reviews | `fa5203b` 12.10 | `8490d67` 10.11 | `backend/app/services/review_service.py` |

## 3. Red and green, run again from the real commits

On 23.11.2026 each test was run against the code **before** the feature (red) and **after** it (green). The test files come from the commit that built the feature. In these commits only the `not_built` marks changed in the test files, so the feature did not change what the tests expect.

| Story | Red: code before the feature | Reason | Green: code with the feature |
|---|---|---|---|
| US-15 | `caf5749^`: 2 failed | `assert 404 == 200` | `caf5749`: 2 passed |
| US-13 | `34ef49f^`: 2 failed (US-14 still 2 xfail) | `assert 404 == 200` | `34ef49f`: 2 passed (US-14 still 2 xfail) |
| US-14 | `8490d67^`: 2 failed | `assert 404 in (200, 201)` | `4c932ed`: 4 passed |

**A defect the tests caught (US-14):** the first commit of the feature, `8490d67`, could not be imported. The new `Review.text` column hid the `text()` function of SQLAlchemy (`TypeError: 'Column' object is not callable`). The fix `4c932ed` came the same day, and the tests then passed. This is why the green run for US-14 uses `4c932ed`.

**Environment:** these runs used Python 3.13, PostgreSQL 17 and current package versions, because the old commits have no lock file. The results show the behavior of the code, not the original CI runs.

## 4. Check it yourself

```bash
git log --diff-filter=A --format='%h %ad %s' --date=short -- tests/requirements/test_epic6_analytics.py
```

```bash
git log --diff-filter=A --format='%h %ad %s' --date=short -- backend/app/api/stats.py
```

```bash
git show caf5749 -- tests/requirements/test_epic6_analytics.py
```
