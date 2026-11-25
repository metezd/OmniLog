# TDD Evidence

Part of the review checklist in #252 (section D), issue #307. Everything here comes from the git history of `main` and can be checked with the commands in section 6.

**Summary for the Software Testing Report (#296):**

- The requirement tests were written on 12.10.2026, before the code of 14 of the 15 user stories. Only US-01 came before its test (section 2).
- Five story groups (six stories) were run again from the real commits: the tests failed on the code before the feature and passed with it (section 3).
- Nine fixes of the testing phase (F1, F3, F4, F5 with deep JSON, F6, F7, D10, and two SonarQube findings) each have a `test:` commit that fails for the expected reason and a `fix:` commit that makes it pass (section 4), in the backend and, where they changed it, in the frontend.

## 1. How the project used test-first

The requirement tests were written before the features, in commit `fa5203b` (12.10.2026). Features that did not exist yet were marked with `not_built(...)` from commit `c67cc8a` (20.10.2026). This made them expected failures (xfail), so the CI stayed green. The pull request that built a story removed its mark, and from then on the test had to pass. The helper was removed in `f4a2dc9` (17.11.2026), when no mark was left.

In the testing phase the team went one step further: each fix is a `test:` commit with only the new tests, followed by a `fix:` commit (section 4). This is now a rule in `CONTRIBUTING.md`.

**How far this goes:** this is test-first at the level of user stories and acceptance tests, plus a strict red then green cycle for the fixes of the testing phase. The history does not show a strict red-green-refactor cycle for every function, and many edge-case tests were added after the code. We do not claim that the whole project was built with TDD.

## 2. First test commit and first code commit of each story

| Story | First test commit | First code commit | Order | Code file |
|---|---|---|---|---|
| US-01 Health check | `fa5203b` 12.10 | `7ead47f` 01.10 | **Code first** | `backend/app/main.py` |
| US-02/03 Accounts | `fa5203b` 12.10 | `f994683` 15.10 | Test first | `backend/app/api/auth.py` |
| US-04 Add to library | `fa5203b` 12.10 | `147079d` 15.10 | Test first | `backend/app/api/library.py` |
| US-05 Rate and update | `fa5203b` 12.10 | `147079d` 15.10 | Test first | `backend/app/api/library.py` |
| US-06 Custom lists | `fa5203b` 12.10 | `bd6e665` 15.10 | Test first | `backend/app/api/journal.py` |
| US-07 Activity diary | `fa5203b` 12.10 | `bd6e665` 15.10 | Test first | `backend/app/api/journal.py` |
| US-08 Catalog | `fa5203b` 12.10 | `29e1e8b` 16.10 | Test first | `backend/app/api/catalog.py` |
| US-09 Title details | `fa5203b` 12.10 | `f059e49` 17.10 | Test first | `backend/app/api/catalog.py` |
| US-10/12 Chapters | `fa5203b` 12.10 | `4222d3d` 17.10 | Test first | `backend/app/api/chapters.py` |
| US-11 Playtime | `fa5203b` 12.10 | `2a8f13e` 20.10 | Test first | `backend/app/api/chapters.py` |
| US-13 Recommendations | `fa5203b` 12.10 | `34ef49f` 07.11 | Test first | `backend/app/api/recommendations.py` |
| US-15 Statistics | `fa5203b` 12.10 | `caf5749` 08.11 | Test first | `backend/app/api/stats.py` |
| US-14 Spoiler reviews | `fa5203b` 12.10 | `8490d67` 10.11 | Test first | `backend/app/services/review_service.py` |

**US-01:** `GET /health` was part of the first backend skeleton (`7ead47f`, 01.10). Its test came eleven days later in `fa5203b`. So for US-01 the code came first.

**US-04 and US-05:** both tests were in `fa5203b`, but the two stories were built in the same commit `147079d`, so the history cannot show which one was made to pass first.

## 3. Red and green, run again from the real commits

Each test was run against the code **before** the feature (red) and **after** it (green). The test files come from the commit that built the feature. In these commits the test files did not change, or only the `not_built` marks changed, so the feature did not change what the tests expect.

| Story | Red: code before the feature | Reason | Green: code with the feature | Run on |
|---|---|---|---|---|
| US-06/07 | `bd6e665^`: 5 failed | `assert 404 == 201`, `assert 404 == 200` | `73de688`: 5 passed | 25.11 |
| US-11 | `2a8f13e^`: 2 failed | `assert 404 in (200, 201)`, `assert 404 == 422` | `2a8f13e`: 2 passed | 25.11 |
| US-15 | `caf5749^`: 2 failed | `assert 404 == 200` | `caf5749`: 2 passed | 23.11 |
| US-13 | `34ef49f^`: 2 failed (US-14 still 2 xfail) | `assert 404 == 200` | `34ef49f`: 2 passed (US-14 still 2 xfail) | 23.11 |
| US-14 | `8490d67^`: 2 failed | `assert 404 in (200, 201)` | `4c932ed`: 4 passed | 23.11 |

The US-06/07 run selects the tests with `-k "us06 or us07"`, and the US-11 run selects them with `-k us11`. The test file is the same in `bd6e665` and `73de688`.

**Two defects the tests caught:**

- **US-14:** the first commit of the feature, `8490d67`, could not be imported. The new `Review.text` column hid the `text()` function of SQLAlchemy (`TypeError: 'Column' object is not callable`). The fix `4c932ed` came the same day, and the tests then passed. This is why the green run for US-14 uses `4c932ed`.
- **US-06/07:** the first commit of the feature, `bd6e665` (20:39), has a broken `backend/app/api/library.py` (a function body without its header at line 166), so the tests cannot start. `73de688` (20:42) replaced it, and the tests passed. It was reverted in `7b10a75` and applied again in `1fe7d50` (21:09), where the tests also pass. This is why the green run for US-06/07 uses `73de688`.

## 4. Red then green cycles of the testing phase fixes

The fixes of the penetration test findings were made as a pair of commits: first `test:` with only the new tests, then `fix:`. Each `test:` commit was run on its own (red) and then the `fix:` commit (green). On 25.11.2026 all red runs failed for the reason the finding describes, not because of a typo or a missing import.

| Finding | Issue / PR | Red: `test:` commit | Failing line | Green: `fix:` commit |
|---|---|---|---|---|
| F1 Login limit bypass | #301 / #340 | `2737be8`: 3 failed, 3 passed | `test_f1_us03_thirty_fake_forwarded_addresses_are_limited`: `assert {401} == {429}` | `b60b09b`: 6 passed |
| F4 NUL bytes and large id | #302 / #341 | `292bf1b`: 9 failed, 3 passed | `test_f4_us08_nul_in_a_new_title_is_refused[title-a\x00b]`: `500: Internal Server Error` | `d43c849`: 12 passed |
| F5/F6 Echoed values | #302 / #341 | `6c9351e`: 2 failed, 16 passed | `test_f5_nfr03_a_rejected_password_is_not_repeated`: `assert 'Sh0rt!' not in '{"detail":[...'` | `179afb3`: 18 passed |
| F3 Poster address | #303 / #342 | `8e388ae`: 10 failed, 15 passed | `test_f3_us08_other_addresses_are_refused[javascript:alert(1)-MediaItemUpdate]`: `DID NOT RAISE ValidationError` | `c07c63f`: 25 passed |
| F7 Headers | #304 / #343 | `fb15646`: 9 failed, 14 passed | `test_f7_the_api_headers_are_on_every_status[200]`: `X-Frame-Options on 200` | `efa6293`: 23 passed |
| F6 Body size | #302 / #341 | `fbd63b5`: 7 failed, 20 passed | `test_f6_us06_a_body_over_one_megabyte_gets_413`: 422 instead of 413; a broken `Content-Length` reached the endpoint (401 instead of 400) | `95d12a0`: 29 passed |
| D10 Duplicate list routes | #305 / #344 | `bbd9465`: 1 failed | `test_no_duplicate_operation_ids_in_openapi`: `Duplicate Operation ID delete_custom_list_lists__list_id__delete` | `e2e8744`: 1 passed |

F5 and F6 are two pairs: `6c9351e`/`179afb3` removed the echoed value (F5 and the deep JSON), and `fbd63b5`/`95d12a0` added the size limit (F6). D10 is on the branch of #344 until it is merged.

### The frontend part of the cycles

Some fixes changed the frontend too. Their `test:` commits hold Vitest tests as well. Run again on 26.11.2026 in Docker (Node 24), only the named test file:

| Fix | Test file | Red: `test:` commit | Failing line | Green |
|---|---|---|---|---|
| F1 (#340) | `tests/lib/server/backend.test.ts` | `2737be8`: 2 failed, 32 passed | `expected null to be '203.0.113.7'` (no `X-Client-IP` sent) | `b60b09b`: 34 passed |
| F3 (#342) | `tests/proxy.test.ts` | `8e388ae`: 6 failed, 7 passed | no `Content-Security-Policy` header | `c07c63f`: 13 passed |
| F7 (#343) | `tests/next-config.test.ts` | `e34a49c`: 2 failed | no browser headers, `X-Powered-By` on | `efa6293`: 2 passed |
| SonarQube S6853 (#349) | `tests/components/title/ChapterProgressCard.test.tsx` | `0a2f138`: 1 failed, 2 passed | the playtime field has no label | `53e8a90`: 3 passed |

F7 therefore has two `test:` commits: `fb15646` for the backend and `e34a49c` for the frontend, both before `efa6293`.

### A second run on another machine

The backend pairs were also run on macOS 27.2.1 with Python 3.12.16 and PostgreSQL 16.16 (Redis off) on 25.11.2026: F1 3 failed then 6 passed, F4 9 failed then 12 passed, F6 7 failed then 29 passed, D10 1 failed then 1 passed. The F5 pair gave **3** failed, 15 passed at `6c9351e`, one more than on Windows: there, the list name nested 3000 levels deep really gave a 500 (`RecursionError` in the old error handler), and the test passed after `179afb3`. So the deep JSON fix is shown on this machine, and the result depends on the recursion limit of the Python build.

The counts are for the whole test file of each fix. The F5 file also holds the F4 tests, which already passed at `6c9351e`. The F7 file also holds the older hardening tests. The frontend tests are in the next table.

### Tests that passed at once

A test that passes before the fix does not prove the fix. Some new tests passed on the red commit:

- **Guards that are meant to pass.** `test_f4_us08_the_largest_external_id_still_works`, `test_f3_us08_tmdb_and_igdb_images_are_accepted` and `test_f3_us08_an_update_without_a_poster_is_fine` check that the fix does not refuse good input. They must pass before and after.
- **`test_f4_us12_nul_in_a_decision_is_refused`** passed at once. NUL in a decision was already refused before the fix, so this test only protects against a regression. It does not show a fix.
- **`test_us06_deeply_nested_json_is_refused_without_a_server_error`** passed at once on Windows with Python 3.13, but failed with a 500 on macOS with Python 3.12 (section "A second run on another machine"). The 50 and 100 000 level cases passed at once on both: the parser already refuses 100 000 levels.
- **Guards of F1 and F6.** A forged `X-Client-IP` without the key, with a wrong key or with a broken value, a review of 5000 characters and a body of exactly 1 MB were already handled before the fix. They protect the fix from refusing good input or trusting bad input.

## 5. Environment of the runs

| | |
|---|---|
| Machine | Windows 11, local, not the CI runner |
| Python | 3.13.9. Production uses 3.15 |
| PostgreSQL | 17.12, without pgvector. The `media_embeddings` table was left out of the test copy, and no test in sections 3 and 4 uses it |
| Redis | Not running. The code falls back to its in-process cache |
| Packages | Current versions from `backend/requirements.in`, because the old commits have no lock file. Runs before November used an older set with `python-jose` and `passlib`, which those commits import |

The results show the behavior of the code at each commit, not the original CI runs.

## 6. Check it yourself

The order of the first test and the first code of a story:

```bash
git log --diff-filter=A --format='%h %ad %s' --date=short -- tests/requirements/test_epic6_analytics.py
```

```bash
git log --diff-filter=A --format='%h %ad %s' --date=short -- backend/app/api/stats.py
```

That the test files of a feature commit did not change what they expect:

```bash
git show caf5749 -- tests/requirements/test_epic6_analytics.py
```

That a fix starts with a commit that holds only tests:

```bash
git show --stat 2737be8
```

```bash
git show --stat b60b09b
```

A red then green run of a fix. It needs the test database of `CONTRIBUTING.md`. Go back to your branch with `git switch -` at the end:

```bash
git switch --detach 2737be8
```

```bash
python -m pytest tests/requirements/test_f1_render_rate_limit.py -q
```

```bash
git switch --detach b60b09b
```

```bash
python -m pytest tests/requirements/test_f1_render_rate_limit.py -q
```
