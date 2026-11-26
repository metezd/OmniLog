# Register of AI Mistakes That Were Caught

Part of the review checklist in [#252] (section E, "Serious AI mistakes caught"). Issue: [#310]. Related: [#308] (AI pipeline, [`README.md`](README.md)).

## How this register was made

- Every entry is a real event with a link. It comes from the notes of a member ([`mhmd-edrees.md`](mhmd-edrees.md), [`sidar-urey.md`][sidar]) or from a pull request. Nothing was added from memory alone.
- An entry is here only if AI made the mistake. A mistake that AI **found** in human code (for example the Copilot review comments in [`evidence.md`][evidence]) is not an AI mistake.
- **Serious** means: it would have shipped a bug, a security hole, a wrong decision or a broken deploy if nobody had caught it. The others are **medium** or **minor**.
- Made on 2026-11-25 from `main` at `74f1f3a`. The notes of `metezd`, `KeremKenet` and `KaganKonuk` are still pending ([#312], [#313], [#314]). Their entries are added by pull request when they exist.

## Register

| ID | Tool and model | What the AI did wrong | How it was caught | Impact if not caught | Fix | Severity | Lesson |
|---|---|---|---|---|---|---|---|
| M1 | Codex desktop app (`gpt-6-luna`) | Ran `git push origin main` to push the US-13 commit straight to `main` ([#258]) | **Ruleset:** GitHub refused the push ("Changes must be made through a pull request"). The approval step of Codex had let the command through | An unreviewed change on `main`, without CI | The commit went to a branch and was merged by [#258] | **Serious** | The ruleset on `main` is the control that works when the agent and its approval step fail |
| M2 | Claude Code (Claude Opus 5.5) | Set `ENABLE_DOCS=false` in `docker-compose.prod.yml` but not in `render.yaml` ([#231]), so `/docs`, `/redoc` and `/openapi.json` stayed public on Render | **Penetration test**, finding F2 ([#259]) | The full list of endpoints public in production | [`a247f0b`][a247f0b] in [#260], with a test that checks both files | **Serious** | A setting for production must be checked in every deployment file. A test now does it |
| M3 | Claude Code (Claude Opus 5.5) | In the first penetration run, read the `X-Forwarded-For` result (`RATE-02`) as a bug of the local setup only. It came from the fact that uvicorn trusts `127.0.0.1`, and missed the real risk ([#259]) | **Manual check:** reading `render.yaml` and a second local run with its start options | A wrong reason in the report, and the High finding F1 would not have been found | The report explains the real risk (F1). Fixed in [#340] | Medium | Read a security result against the real deployment settings, not only the local run |
| M4 | Codex desktop app (`gpt-6-luna`) | The recommendation fallback did not recover after a PostgreSQL error in the vector query ([#258]) | **Self-review** of the agent's own diff, before the tests could run | `GET /recommendations` could fail instead of using the popularity ranking | [`5ab0ee7`][5ab0ee7], before the commit | Medium | Ask the agent to review its diff for error paths before it runs the tests |
| M5 | Claude Code (Claude Opus 5.5) | Added `iat` to the token but ran only part of the tests, so `test_epic2_token_lifetime.py` broke ([#231]) | **CI** failed on the pull request | None for users. The pull request could not be merged | [`c841987`][c841987] | Minor | Run the whole suite, not only the new tests |
| M6 | Codex desktop app (`gpt-6-luna`) | A new fallback test passed alone but failed in the full suite, because titles from other tests pushed it out of the top 10 ([#258]) | **Full test run** (810 passed, 1 failed) | A flaky test in CI | The test creates its own data. 811 passed | Minor | A test must create the data it depends on |
| M7 | Claude Code (Claude Opus 5.5) | Wrote two claims in the evidence page that the data did not show ("stopped asking" for Copilot reviews, issues "written in more detail") ([#318]) | **Self-check** of every claim against the data, before the commit | A false statement in a graded document | Both sentences changed before the commit | Minor | Every sentence in a report needs a source |
| M8 | Claude Code (Claude Opus 5.5) | Wrote in the TDD evidence that the US-06/07 red run had 4 failed and 1 passed ([#345]) | **Re-run** with the full pytest output: 5 failed | A wrong number in the TDD evidence | Corrected in [#345] before the commit | Minor | Copy numbers from the full output, not from a cut summary |
| M9 | Claude Code (Claude Opus 5.5) | The first replay of the F1 and F7 fix cycles copied only `backend/` and `tests/`, so the tests could not find `render.yaml` and the Caddyfile. That gave errors, not the real red result ([#345]) | **Reading the errors:** `FileNotFoundError`, not an assertion | A "red" run that failed for the wrong reason, written as TDD evidence | The runs were repeated with the whole repository ([#345]) | Minor | Check that a red test fails for the expected reason |

## Summary

**9 entries:** 2 serious, 2 medium, 5 minor. Two tools: Claude Code (6) and the Codex desktop app (3). ChatGPT and claude.ai chat have no recorded mistake ([`sidar-urey.md`][sidar], [`musab-alperen-basol.md`](musab-alperen-basol.md)).

**How they were caught:**

| Control | Count | Entries |
|---|---|---|
| The agent's own check (self-review, self-check, reading the errors) | 3 | M4, M7, M9 |
| Running the tests again (CI, full suite, re-run) | 3 | M5, M6, M8 |
| Ruleset on `main` | 1 | M1 |
| Penetration test | 1 | M2 |
| Manual check of the deployment files | 1 | M3 |

Both serious mistakes were caught by a control outside the agent: the ruleset (M1) and the penetration test (M2). M2 was merged before it was found, so review and CI alone did not catch it.

**What the team changed because of them:**

- A test now checks that the API docs are off in every production file ([#260]).
- The test-first rule for fixes, with a check that the red test fails for the right reason ([#345], from M9).
- The AI assistance convention: the `ai-assisted` label, the `Assisted-by` trailer and the AI section of the pull request template ([#324]). Before it, M2 and M5 had no AI line in the commits ([#231]).

## Not added

These leads from [#310] were checked and not added, because the record does not show that AI wrote the code:

- The `Review.text` column that hid the SQLAlchemy `text()` function (`8490d67`, found by the tests in [`tdd-evidence.md`](../tests/tdd-evidence.md)). The notes of its author are pending ([#313]).
- The broken `backend/app/api/library.py` in `bd6e665`. The notes of its author are pending ([#314]).
- The default `SECRET_KEY` and the open Redis port in [#41]. Copilot **found** these in human code ([`evidence.md`][evidence]), so they are AI catches, not AI mistakes.

[#41]: https://github.com/metezd/OmniLog/pull/41
[#231]: https://github.com/metezd/OmniLog/pull/231
[#252]: https://github.com/metezd/OmniLog/issues/252
[#258]: https://github.com/metezd/OmniLog/pull/258
[#259]: https://github.com/metezd/OmniLog/pull/259
[#260]: https://github.com/metezd/OmniLog/pull/260
[#308]: https://github.com/metezd/OmniLog/issues/308
[#310]: https://github.com/metezd/OmniLog/issues/310
[#312]: https://github.com/metezd/OmniLog/issues/312
[#313]: https://github.com/metezd/OmniLog/issues/313
[#314]: https://github.com/metezd/OmniLog/issues/314
[#318]: https://github.com/metezd/OmniLog/pull/318
[#324]: https://github.com/metezd/OmniLog/pull/324
[#340]: https://github.com/metezd/OmniLog/pull/340
[#345]: https://github.com/metezd/OmniLog/pull/345
[a247f0b]: https://github.com/metezd/OmniLog/commit/a247f0b
[c841987]: https://github.com/metezd/OmniLog/commit/c841987
[5ab0ee7]: https://github.com/metezd/OmniLog/commit/5ab0ee7
[sidar]: sidar-urey.md
[evidence]: evidence.md
