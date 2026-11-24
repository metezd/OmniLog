# Evidence of AI Use Beyond Autocomplete

Part of the review checklist in [#252] (section E, "Beyond autocomplete"). Issue: [#311]. Related: [#308] (AI pipeline), [#310] (mistakes register), [#312] to [#317] (notes of each member).

This page collects the proof that the team used AI as an **agent** and as a **reviewer**, not only for code completion, and what this use did not do well. Every row has a link. The page does not claim more than the repository and the notes of the members show.

## How this page was made

- The data was read on 2026-11-24 from GitHub with `gh pr view`, `gh api repos/metezd/OmniLog/pulls/<n>/comments` and `gh api repos/metezd/OmniLog/pulls/<n>/reviews`, and from the git history with `git log --grep "Co-Authored-By"`.
- A pull request counts as **agent work** when its commits carry a `Co-Authored-By: Claude` line, its description says "Generated with Claude Code", or the notes of its author say that an agent made it.
- On that day only one member file exists: [`mhmd-edrees.md`](mhmd-edrees.md). The notes of the other five members ([#312] to [#316]) are not written yet. Their parts on this page say "pending" and must be filled from those notes, not guessed.

## 1. Agent work

In each case the issue was the specification. The agent read it, worked on a branch, ran tests and opened the pull request. The member checked the result and is the author of record.

| Pull request | Issue (specification) | Agent and proof | Commits | What the human changed in review | CI |
|---|---|---|---|---|---|
| [#231] API hardening | [#220] | Claude Code, Claude Opus 5.5 (from [`mhmd-edrees.md`](mhmd-edrees.md). The commits have no AI line) | 4 and a merge | Nothing. `metezd` approved ("Nice work") with no inline comment. The fix [`c841987`][c841987] came after CI failed, not from the review | 11 passed |
| [#235] Python version of the production image | [#221] | `Co-Authored-By: Claude Opus 5.5` on both commits, "Generated with Claude Code" in the description | 2 | Nothing. Approved without a comment. The second commit [`78fc6c3`][78fc6c3] came from a `DeprecationWarning` in the first CI run on Python 3.15 | 11 passed |
| [#236] Rate limits | [#217] | `Co-Authored-By: Claude Opus 5.5` on [`5ac28cb`][5ac28cb], "Generated with Claude Code" | 1 and a merge | Nothing. Approved ("Nice work") | 11 passed |
| [#237] Replace passlib, pin the backend versions | [#222] | `Co-Authored-By: Claude Opus 5.5` on [`d2d3b8f`][d2d3b8f], "Generated with Claude Code" | 1 and a merge | Nothing. Approved without a comment | 11 passed |
| [#255] Tests for the statistics screen | [#209] | `Co-Authored-By: Claude Sonnet 5.5` on [`8335c9d`][8335c9d] | 1 | Nothing. Approved without a comment | **Not run**: every job stopped with "recent account payments have failed or your spending limit needs to be increased" ([run][run255]) |
| [#259] Penetration test, TDD evidence, AI notes | none (part of [#252]) | Claude Code, Claude Opus 5.5 (from [`mhmd-edrees.md`](mhmd-edrees.md) and the description) | 5 | Nothing. Approved without a comment | **Not run** (same billing stop, [run][run259]) |
| [#260] Turn off the API docs on Render | none (finding F2 of the penetration test) | The description says AI was used and points to [`mhmd-edrees.md`](mhmd-edrees.md) | 1 and a merge | Nothing. The approval of `metezd` shows as `DISMISSED` | **Not run** (same billing stop, [run][run260]) |
| Work of `metezd`, `KeremKenet`, `KaganKonuk`, `sidarurey`, `musabalperenbasol` | [#312] to [#316] | pending | | | |

What the table shows:

- The agents worked from the issue: every agent pull request with an issue closes it, and the description follows the pull request template.
- **No human review changed the code** of an agent pull request. Every review was an approval without an inline comment. The corrections came from CI ([#231], [#235]) and from the penetration test ([#260]). This is a weak point, see [#293] for the review rules.
- Three agent pull requests were merged while CI did not run at all (GitHub Actions billing). For those, the only checks are the local runs written in the description and the review.

## 2. AI review (Copilot)

**The last 20 merged pull requests** ([#235] to [#260]) **have no Copilot review**: 0 comments accepted, 0 rejected. All their reviews are by `metezd`. Copilot code review was used only earlier. It reviewed 14 pull requests ([#25], [#32], [#41], [#66], [#69], [#76], [#79], [#85], [#86], [#129], [#143], [#159], [#179], [#228]) and wrote 23 inline comments on 5 of them. Those 23 comments were counted instead: for each one, the merged code was compared with the comment.

| Pull request | Comments | Accepted | Not acted on | No longer relevant |
|---|---|---|---|---|
| [#41] Phase 1 | 7 | 5 (secret key, CORS trimming, primary key indexes, test `.env` loading, Redis on `127.0.0.1`) | 2 (test database on an old volume, narrower description) | |
| [#66] Authentication | 5 | 4 (both password length comments, `ACCESS_TOKEN_EXPIRE_MINUTES` in the README, the stale project status) | 1 (bcrypt not in the Charter) | |
| [#129] Search page | 6 | | 3 (mock library `Set`, the `kind` note, tests for the page) | 3 (raw `<img>`, `aria-pressed`, label of the field: the page was replaced by the version on `main` in the merge [`ab25d20`][ab25d20]) |
| [#143] Recommendations | 4 | 1 (`target` typed as `MediaType`) | 3 (taste profile, `response_model`, tests for 401 and 422) | |
| [#159] Statistics | 1 | | 1 (description says no frontend file changed, but `frontend/Dockerfile` changed) | |
| **Total** | **23** | **10** | **10** | **3** |

"Not acted on" means the merged code does not follow the comment. In none of these cases did the author write a reason in the thread, so the reason below is what the history shows, not what the author said.

### Accepted: two examples

1. **Redis open on the network** ([#41], [comment][c-redis]). Copilot said that `docker-compose.yml` published Redis without a password on every interface. The fix [`13370d0`][13370d0] binds PostgreSQL and Redis to `127.0.0.1`. The comment is still true in today's `docker-compose.yml`.
2. **Free text `target`** ([#143], [comment][c-target]). Copilot said that `target` was a free string, so an unknown value reached the PostgreSQL enum instead of giving 422. The fix [`e97895e`][e97895e] types it as `MediaType`. This commit and [`fa01da5`][fa01da5] in [#41] carry `Co-authored-by: Copilot Autofix`, so here AI found the problem and also wrote the fix, and a member committed it.

### Not acted on: two examples

1. **bcrypt not in the Charter** ([#66], [comment][c-bcrypt]). Copilot asked to update the Charter or drop the new dependency. [#66] was merged without a Charter change. The reason was not written. Five weeks later [#237] (issue [#222]) removed passlib and added bcrypt to [`docs/CHARTER.md`](../CHARTER.md), so the comment was right and was acted on late.
2. **Recommendations that are only a catalog filter** ([#143], [comment][c-taste]). Copilot said that the endpoint returned the same unowned titles to every user and did not use the user's ratings, so it was not US-13 yet. [#143] was merged as it was, as a first step. The personalized ranking came later in [#247] (embeddings) and [#258] (recommendations). In the same review `metezd` answered the `response_model` comment with a suggestion that keeps the line unchanged ([thread][c-response-model]), so that comment was turned down on purpose.

What this shows: Copilot found real problems (a guessable secret key, an open Redis port, a password check that could be bypassed with a long suffix in [#66]). About half of its comments were not acted on, and none of those has a written reason. No pull request after [#228] has a Copilot review.

## 3. Repository skills and instructions

| File | What it tells the AI | Evidence that it was followed |
|---|---|---|
| [`.github/skills/code-review/SKILL.md`](../../.github/skills/code-review/SKILL.md) (added in [#41] by `metezd`) | Review rules: the stack is fixed by the Charter, PostgreSQL only, no index on a primary key, Pydantic schemas for every body, no secrets with a public default, tests for 401, 404, 409 and 422, the description must match the files | Copilot comments that match these rules: the primary key indexes ([#41], [comment][c-pk], accepted), the guessable `SECRET_KEY` ([#41], [comment][c-secret], accepted), bcrypt outside the Charter ([#66], [comment][c-bcrypt]), the missing `response_model` and the missing 401 and 422 tests ([#143]), and the description that does not match the files ([#159], [comment][c-desc]). **Limit:** GitHub does not show which instruction file the reviewer read, so this is a match between a rule and a comment, not a proof that the reviewer used the file |
| [`frontend/AGENTS.md`](../../frontend/AGENTS.md) and [`frontend/CLAUDE.md`](../../frontend/CLAUDE.md) (committed in [`7a1082d`][7a1082d] by `KeremKenet`) | This Next.js version differs from what the model learned, so read the guide in `node_modules/next/dist/docs/` before writing code. `CLAUDE.md` only imports `AGENTS.md`. The text is the block that `next dev` writes, not a rule written by the team | pending [#313]: only the frontend lead can say whether the agent read the guide, for example in [#255] |
| [`.github/pull_request_template.md`](../../.github/pull_request_template.md) | The sections and the checklist of every pull request | The agent pull requests [#235], [#236], [#237] and [#255] use every section and fill "How it was tested" with the commands and the numbers |

## 4. AI for tests and documents

| File | Drafted in | How it was checked |
|---|---|---|
| `tests/requirements/test_rate_limits.py` | [#236] | Local `pytest tests` on PostgreSQL 17: 768 passed, 16 skipped, coverage 91%. The Redis variants ran only in CI. CI passed |
| `tests/requirements/test_password_hashing.py` | [#237] | Real passlib hashes from passlib 1.7.4 still verify. Local `pytest tests`: 784 passed, 16 skipped, coverage 91%, `security.py` 100%. CI passed |
| [`frontend/tests/app/stats/page.test.tsx`](../../frontend/tests/app/stats/page.test.tsx) | [#255] | Local `npx vitest run tests/app/stats` (14 tests), `npm run lint` and `npx tsc --noEmit`. CI did not run (billing) |
| [`tests/pentest/run_pentest.py`](../../tests/pentest/run_pentest.py) and [`docs/tests/penetration`](../tests/penetration) | [#259] | Each finding was checked against the configuration, F1 has a local proof. A wrong first result for `X-Forwarded-For` was caught by a second run (see [`mhmd-edrees.md`](mhmd-edrees.md)) |
| [`docs/tests/tdd-evidence.md`](../tests/tdd-evidence.md) | [#259] | The tests were run again from old commits. The commands are in the document |
| Tests and documents of the other members | [#312] to [#316] | pending |

## 5. Two real sessions

Secrets, tokens, local paths and e-mail addresses are removed. Nothing else is changed.

### Session 1: an agent reads an issue and opens a pull request

pending: a transcript of an agent session that starts from an issue, for example the session behind [#235], [#236] or [#237]. It must come from the member who ran it ([#317]), with secrets, tokens, local paths and e-mail addresses removed.

### Session 2: a review conversation

The review of [#143] (US-13 recommendations, author `KaganKonuk`) by Copilot and `metezd`:

1. Copilot ([comment][c-taste]): the query returns every unowned title of the type and does not use the user's ratings, so this is a catalog filter, not a recommendation.
2. Copilot ([comment][c-response-model]): the route has no `response_model`, unlike the other routes.
3. `metezd` answers comment 2 with a suggestion that keeps `@router.get("", status_code=status.HTTP_200_OK)` as it is.
4. Copilot ([comment][c-target]): `target` is a free string, use `MediaType` and add a test for an invalid value.
5. `metezd` applies the Copilot Autofix for comment 4 ([`e97895e`][e97895e]) and merges.
6. Comments 1 and 3 stay open. Comment 1 is done later in [#247] and [#258].

## 6. Reflection

**Team** (from the evidence above, to be confirmed by the members):

- **Saved time.** Agents turned a well written issue into a complete pull request with tests, documents and a filled template in one or two commits ([#235], [#236], [#237]). The test files of [#236] and [#237] cover cases that are slow to write by hand (Redis down, real passlib hashes, every package of the lock has hashes).
- **Cost time.** Agent pull requests are long ([#236] changes 18 files, [#237] adds about 2000 lines of lock files), and a reviewer must read all of it. In practice the reviews were approvals without comments, so the time was not spent where it should be.
- **What AI got wrong.** It ran only part of the tests and broke one ([#231]). It fixed one file and missed the same setting in `render.yaml` ([#231], fixed in [#260]). It gave a wrong reason for a penetration test result. Copilot wrote advice that was ignored without a reason. The full list is in the mistakes register ([#310]).
- **How the way of working changed.** For agent work the issue is the specification and the pull request template is the report. CI and the security tools became the main safety net, which is why the billing stop of CI ([#255], [#259], [#260]) matters more than before.

**Each member:**

| Member | Notes | Reflection |
|---|---|---|
| Mohammed Edris (`Mhmd77Edrees`) | [`mhmd-edrees.md`](mhmd-edrees.md), [#317] | AI did the code, the tests and the documents of the security work. CI and the penetration test caught its mistakes. The member reviews all output and must be able to explain it |
| Mete Özdoğan (`metezd`) | [#312] | pending |
| Kerem Kenet (`KeremKenet`) | [#313] | pending |
| Kağan Konuk (`KaganKonuk`) | [#314] | pending |
| Sidar Ürey (`sidarurey`) | [#315] | pending |
| Musab Alperen Başol (`musabalperenbasol`) | [#316] | pending |

## Open points

- Fill the "pending" rows when [#312] to [#316] are merged, and add every agent pull request that those notes name to the table of section 1.
- Fix the GitHub Actions billing, then run CI again on `main`, because [#255], [#259] and [#260] were merged without it.
- Decide whether Copilot review is used again (none after [#228]). If yes, a "not acted on" comment needs a short written reason.

[#25]: https://github.com/metezd/OmniLog/pull/25
[#32]: https://github.com/metezd/OmniLog/pull/32
[#41]: https://github.com/metezd/OmniLog/pull/41
[#66]: https://github.com/metezd/OmniLog/pull/66
[#69]: https://github.com/metezd/OmniLog/pull/69
[#76]: https://github.com/metezd/OmniLog/pull/76
[#79]: https://github.com/metezd/OmniLog/pull/79
[#85]: https://github.com/metezd/OmniLog/pull/85
[#86]: https://github.com/metezd/OmniLog/pull/86
[#129]: https://github.com/metezd/OmniLog/pull/129
[#143]: https://github.com/metezd/OmniLog/pull/143
[#159]: https://github.com/metezd/OmniLog/pull/159
[#179]: https://github.com/metezd/OmniLog/pull/179
[#209]: https://github.com/metezd/OmniLog/issues/209
[#217]: https://github.com/metezd/OmniLog/issues/217
[#220]: https://github.com/metezd/OmniLog/issues/220
[#221]: https://github.com/metezd/OmniLog/issues/221
[#222]: https://github.com/metezd/OmniLog/issues/222
[#228]: https://github.com/metezd/OmniLog/pull/228
[#231]: https://github.com/metezd/OmniLog/pull/231
[#235]: https://github.com/metezd/OmniLog/pull/235
[#236]: https://github.com/metezd/OmniLog/pull/236
[#237]: https://github.com/metezd/OmniLog/pull/237
[#247]: https://github.com/metezd/OmniLog/pull/247
[#252]: https://github.com/metezd/OmniLog/issues/252
[#255]: https://github.com/metezd/OmniLog/pull/255
[#258]: https://github.com/metezd/OmniLog/pull/258
[#259]: https://github.com/metezd/OmniLog/pull/259
[#260]: https://github.com/metezd/OmniLog/pull/260
[#293]: https://github.com/metezd/OmniLog/issues/293
[#308]: https://github.com/metezd/OmniLog/issues/308
[#310]: https://github.com/metezd/OmniLog/issues/310
[#311]: https://github.com/metezd/OmniLog/issues/311
[#312]: https://github.com/metezd/OmniLog/issues/312
[#313]: https://github.com/metezd/OmniLog/issues/313
[#314]: https://github.com/metezd/OmniLog/issues/314
[#315]: https://github.com/metezd/OmniLog/issues/315
[#316]: https://github.com/metezd/OmniLog/issues/316
[#317]: https://github.com/metezd/OmniLog/issues/317
[c841987]: https://github.com/metezd/OmniLog/commit/c841987
[78fc6c3]: https://github.com/metezd/OmniLog/commit/78fc6c3
[5ac28cb]: https://github.com/metezd/OmniLog/commit/5ac28cb
[d2d3b8f]: https://github.com/metezd/OmniLog/commit/d2d3b8f
[8335c9d]: https://github.com/metezd/OmniLog/commit/8335c9d
[13370d0]: https://github.com/metezd/OmniLog/commit/13370d0
[e97895e]: https://github.com/metezd/OmniLog/commit/e97895e
[fa01da5]: https://github.com/metezd/OmniLog/commit/fa01da5
[ab25d20]: https://github.com/metezd/OmniLog/commit/ab25d20
[7a1082d]: https://github.com/metezd/OmniLog/commit/7a1082d
[run255]: https://github.com/metezd/OmniLog/actions/runs/45014663136/job/137184292625
[run259]: https://github.com/metezd/OmniLog/actions/runs/45211608139/job/137821619649
[run260]: https://github.com/metezd/OmniLog/actions/runs/45217961326/job/137844136630
[c-redis]: https://github.com/metezd/OmniLog/pull/41#discussion_r4275210483
[c-pk]: https://github.com/metezd/OmniLog/pull/41#discussion_r4274879314
[c-secret]: https://github.com/metezd/OmniLog/pull/41#discussion_r4274879166
[c-bcrypt]: https://github.com/metezd/OmniLog/pull/66#discussion_r4280001874
[c-target]: https://github.com/metezd/OmniLog/pull/143#discussion_r4502052741
[c-taste]: https://github.com/metezd/OmniLog/pull/143#discussion_r4502052690
[c-response-model]: https://github.com/metezd/OmniLog/pull/143#discussion_r4502052718
[c-desc]: https://github.com/metezd/OmniLog/pull/159#discussion_r4507454137
