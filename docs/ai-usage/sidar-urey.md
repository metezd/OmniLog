# AI Usage Notes: Sidar Ürey (`sidarurey`)

Part of the review checklist in [#252] (section E). Issue: [#315]. These notes record where AI was used in my work, how it was checked, and which AI mistakes were caught. Role: ML Engineer (embeddings, recommendations, spoiler detection).

## Tools

| Tool | Model | How it was used | Period |
|---|---|---|---|
| ChatGPT (chat) | not recorded | Questions and answers in the chat. Everything from it reached the repository through my own commits | Up to 2026-11-22: [#186], [#187], [#238], [#247] |
| Codex desktop app (ChatGPT) | `gpt-6-luna` | An agent with access to the repository and a shell: read the issue, wrote code, tests and docs, ran the tests, committed and pushed after my approval | 2026-11-23: [#258] |
| Claude Code (desktop app) | Claude Opus 5.5 | An agent with access to the repository, a shell, Docker, a browser and `gh`: read the issue, wrote code, tests and documents, ran the tests locally and in Docker, committed with the `Assisted-by` trailer and opened the pull request | 2026-11-24 to 2026-11-26: [#318] to [#363], see the list below |

The model and the steps of the Codex and Claude Code work are taken from the session logs on my computer. For the ChatGPT chats there is no saved log, so the table below does not claim more than what the pull requests show.

## Work done with AI

| Pull request | What the AI did | How it was checked |
|---|---|---|
| [#186] Embedding model decision (closes [#44]) | ChatGPT chat: help with the comparison and the wording of the documents | The decision (`text-embedding-3-small`, 1536 dimensions) was reviewed and approved by `metezd`. Documentation only |
| [#187] OpenAI client for embeddings and spoiler detection (closes [#149]) | ChatGPT chat: help with the client, the settings and the fake client for tests | 8 OpenAI client tests, 4 AI requirement tests, full suite 622 passed and 7 skipped (from the description). CI passed. Approved by `metezd` |
| [#238] Reviews endpoint | ChatGPT chat: help with the endpoint and its tests | 757 passed, 9 skipped, `git diff --check` (from the description). CI passed. Approved by `metezd` |
| [#247] Title embeddings (closes [#151]) | ChatGPT chat: help with the pgvector storage, the service and the backfill command | 885 passed, 20 skipped, one Alembic head (`0013`) (from the description). CI passed. Approved by `metezd` |
| [#258] Personalized recommendations, US-13 (closes [#153]) | Codex agent: checked the existing endpoint and service, added the tests (validation, fixed-vector order, user isolation, fallback, a 5,000-title catalog with a bounded number of queries), fixed the fallback after a vector query error, updated the README, the Epic 5 DFD and the changelog, made both commits and pushed the branch | The agent could not run the tests at first (no pgvector, no Docker). It installed pgvector for the local PostgreSQL 16 and ran the 33 related tests, then the full suite: 811 passed, 18 skipped. Approved by `metezd`. CI did not run (GitHub Actions billing stop) |
| [#318] Evidence page, [#311] | Claude Code agent: read the issue and the related issues, read the reviews and comments of the pull requests with `gh api`, compared each Copilot comment with the merged code, wrote `docs/ai-usage/evidence.md` | Every link was opened with `gh api`. The counts can be repeated with the commands on the page. Waiting for the review of `metezd`. CI did not run (billing stop) |
| This file, [#315] | Claude Code agent: read the session logs on my computer and the pull requests, drafted the file | I confirmed the tools and the pull requests. Every row has a link |
| [#320] to [#363], 23 pull requests from 2026-11-24 to 2026-11-26 | Claude Code agent: the CI checks (branch names and titles, SonarQube, coverage gate, post-deploy check, AI disclosure), the fixes of the penetration test (F1 to F7), the performance, traceability, SonarQube, TDD and penetration retest documents, the Software Testing Report, the code review log and CODEOWNERS, and the clean-up for the submission | Every one carries the label `ai-assisted` and its commits the trailer `Assisted-by: Claude Code (Claude Opus 5.5)`. Each description lists the test runs (locally and in Docker) and what the AI got wrong. List: `gh pr list --author sidarurey --label ai-assisted --state all` |

### Embeddings, recommendations and spoiler detection

- **Where AI helped:** in the code and the tests ([#187], [#247], [#258]) and in the wording of the model decision ([#186]). The ranking design of [#258] (average the vectors of titles rated 7 or more, or completed without a rating, rank by cosine distance, fall back to popularity) comes from the proposal in the issue [#153], and the service already followed it in my uncommitted changes when the agent started. The agent added the tests and the fix of the fallback.
- **How the quality was checked:** only with automated tests. The tests of [#258] use fixed vectors, so they show that the order follows the cosine distance, that one user's ratings do not change another user's results, and that a 5,000-title catalog stays within a fixed number of queries. The tests use a fake OpenAI client ([`fake_openai.py`](../../tests/requirements/fake_openai.py)), so the real embeddings were not judged by hand. **There is no record of a run with real titles and a real OpenAI key** where a person looked at whether the recommendations or the spoiler flags make sense. This is open.

## AI mistakes that were caught

| Mistake | How it was caught | Fix | Severity |
|---|---|---|---|
| In [#258] the Codex agent ran `git push origin main` to push the US-13 commit straight to `main` | The GitHub ruleset refused the push ("Changes must be made through a pull request"). The approval step of Codex had let the command through | The commit went to `feature/us-13-recommendations` and was merged by [#258] | Serious: without the ruleset, an unreviewed change would have been on `main` |
| In [#258] a new fallback test passed alone but failed in the full suite, because popular titles from other tests pushed the new title out of the top 10 | The agent ran the whole suite after the 33 related tests (810 passed, 1 failed) | The test creates its own data. After that 811 passed | Minor (a test that depends on the order of other tests) |
| In [#258] the fallback did not recover after a PostgreSQL error in the vector query | The agent found it while reviewing its own diff, before the tests could run | Fixed in [`5ab0ee7`][5ab0ee7] before the commit | Medium: the endpoint could fail instead of using the popularity ranking |
| While writing [#318] the agent wrote two claims that the data did not show (that the team "stopped asking" for Copilot reviews, and that issues "are written in more detail") | The agent's own check of every claim against the data, before the commit | Both sentences were changed before the commit | Minor |

The serious one is also for the team register ([#310]). The mistakes of the later Claude Code work are in the register too ([`mistakes.md`](mistakes.md), M10 to M15).

## Limits

- AI never merged anything. All my pull requests were merged by `metezd`. Eight of them ([#318] to [#324] and [#328]) were merged without a recorded approval ([code review log](../code-review-log.md)).
- In Codex every write outside the workspace, every commit and every push needed an approval. The push to `main` shows that this approval is not enough on its own, and the branch rules of GitHub are the real control.
- I would not trust AI with: pushing to `main`, design decisions without the team (the embedding model was decided in [#44]), or deciding that results are good when only fake clients were used.
- The agents ran on my computer with a shell, so they can read any local file. The checkout has no `backend/.env` today, but a session that runs with a real key in that file could read the key. Real keys should not be in the checkout while an agent works.

[#44]: https://github.com/metezd/OmniLog/issues/44
[#149]: https://github.com/metezd/OmniLog/issues/149
[#151]: https://github.com/metezd/OmniLog/issues/151
[#153]: https://github.com/metezd/OmniLog/issues/153
[#186]: https://github.com/metezd/OmniLog/pull/186
[#187]: https://github.com/metezd/OmniLog/pull/187
[#238]: https://github.com/metezd/OmniLog/pull/238
[#247]: https://github.com/metezd/OmniLog/pull/247
[#252]: https://github.com/metezd/OmniLog/issues/252
[#258]: https://github.com/metezd/OmniLog/pull/258
[#310]: https://github.com/metezd/OmniLog/issues/310
[#311]: https://github.com/metezd/OmniLog/issues/311
[#315]: https://github.com/metezd/OmniLog/issues/315
[#318]: https://github.com/metezd/OmniLog/pull/318
[#320]: https://github.com/metezd/OmniLog/pull/320
[#324]: https://github.com/metezd/OmniLog/pull/324
[#328]: https://github.com/metezd/OmniLog/pull/328
[#363]: https://github.com/metezd/OmniLog/pull/363
[5ab0ee7]: https://github.com/metezd/OmniLog/commit/5ab0ee7
