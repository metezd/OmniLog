# AI Usage Notes: Musab Alperen Başol (`musabalperenbasol`)

Part of the review checklist in [#252] (section E). Issue: [#316]. These notes record where AI was used in my work, how it was checked, and which AI mistakes were caught. Role: API Integration and Backend Engineer.

## Tools

| Tool | Model | How it was used | Pull requests |
|---|---|---|---|
| Claude (chat on claude.ai) | Claude Opus (exact version not recorded) | Questions and answers in the chat. The AI had no access to the repository, a shell or GitHub. I read the answers, changed them where needed and made every commit myself | [#6], [#78], [#84], [#240], [#254] |
| Claude (Cowork in the desktop app) | Claude Opus 5.5 | An agent with access to the repository, a shell and the browser: read the issue and my pull requests on GitHub, drafted this file, updated the README of this folder, made the commit and opened the pull request | 2026-11-25: this file ([#316]) |

Before this file I did not use an agent (Claude Code, Codex), GitHub Copilot autocomplete or any other AI tool. There is no saved log of the chats, so the table below does not claim more than what the pull requests show. The commits have no AI attribution line, so this file is the record of AI use for these pull requests.

## Work done with AI

| Pull request | What the AI did | How it was checked |
|---|---|---|
| [#6] Pydantic v2 schemas | Chat: help with the code of the schemas (user, media, library) | Manual validation in the description (valid input, invalid email, empty title, rating out of range). No automated tests in the pull request. CI had no checks yet. Merged by `KaganKonuk` |
| [#78] Library listing with `joinedload` (refs [#49]) | Chat: help with the eager loading in `library_service.py` and the edge-case tests | New tests in `test_epic3_library_edge_cases.py`. The description does not record a local run. The `Backend tests` check was red on the last commit ([`36c4a3a`][36c4a3a]) when it was merged. Approved by `metezd` |
| [#84] US-09 title details, seasons and chapters (closes [#54]) | Chat: help with the TMDB season and episode loading, the tables of migration `0005`, the Redis cache and the fallback when TMDB is down | US-09 requirement tests, 68 edge-case tests (`test_epic3_title_details_edge_cases.py`), a fake TMDB in `fake_external_apis.py`. The `Backend tests` check was red on the last commit ([`d97f3f3`][d97f3f3]) when it was merged. Approved by `metezd` |
| [#240] Diary indexes and paging (part of [#145]) | Chat: help with migration `0013`, `limit` and `offset` on `GET /diary`, `GET /library`, `GET /lists`, and the tests | 26 tests in `test_epic2_pagination.py`, local suite 680 passed and 7 skipped, coverage 90%, `alembic check`, `alembic downgrade 0011` and up again, `ruff check` (from the description). CI passed. Approved by `metezd` |
| [#254] Save the review before the spoiler check (fixes [#152], part of [#145]) | Chat: help with moving the OpenAI call out of the transaction and with the tests | Tests for an OpenAI failure (review saved, fields NULL, 201) and for no pool connection during the call (`engine.pool.checkedout() == 0`). Full suite against PostgreSQL 16 with pgvector: 897 passed, 18 skipped (from the description). Every CI check on the last commit ([`6ef2769`][6ef2769]) reports a failure, so the local run is the only test record. Approved by `metezd` |
| This file, [#316] | Cowork agent: read the pull requests, their commits and CI checks on GitHub, asked me which tools and pull requests used AI, drafted the file | I answered the questions and confirmed the tools and the pull requests. Every row has a link |

Work without AI:

- **Code:** [#188] (Life is Strange IGDB seed), [#227] (spoiler pattern fix), [#325] (release 0.8.0). No AI was used.
- **Tests:** [#212] (NFR-01/02/04 tests), [#234] (Software Test Document). No AI was used.
- **Documents:** [#18] (requirements definition), the Epic 3 analysis ([`48a22cf`][48a22cf], [`b58fc9e`][b58fc9e]). No AI was used.
- **Review:** I did not use AI to review pull requests.

### IGDB and TMDB integrations

- **Where AI helped:** only in [#84], in the TMDB code for seasons and episodes (`backend/app/integrations/tmdb.py`, `catalog_service.py`). The base IGDB and TMDB clients were written by `metezd` ([`678160a`][678160a]). The IGDB id of Life is Strange (7599) in [#188] was done without AI.
- **How it was checked:** only with fakes. The 68 edge-case tests of [#84] use the fake TMDB in [`fake_external_apis.py`](../../tests/requirements/fake_external_apis.py). [#84] also added `test_live_tmdb_series_details_have_seasons_and_episodes` to [`test_epic3_catalog_live.py`](../../tests/requirements/test_epic3_catalog_live.py), but this test is skipped without a real `TMDB_API_KEY`, and **I did not run it with a real key**. So there is no record that the season code matches the real TMDB answers. This is open: run `RUN_LIVE_API_TESTS=1 python -m pytest tests/requirements/test_epic3_catalog_live.py -v` with real keys and add the result here.

## AI mistakes that were caught

No AI mistake is recorded. I do not remember a case where an answer of the chat was wrong and had to be fixed, and there is no log to check it. Nothing is added to the team register ([#310]).

The red `Backend tests` check on [#78] and [#84] and the failed checks on [#254] are facts of CI. This file does not say that AI caused them, because that is not known.

## Limits

- For the code pull requests the AI never had access to the repository, the shell, GitHub or the `.env` files. Everything it wrote reached the repository through my own commits, and all of my pull requests were merged after a review by a teammate. Only the agent that drafted this file had access to the repository, and it did not read `.env` files.
- I did not use AI for the requirements, the analysis documents, the test document, the release or for reviews.
- I would not trust AI to confirm that the code matches the real IGDB or TMDB API. Only a live run can show that, and this is still open for [#84].
- I must be able to explain every line of these pull requests when the reviewer asks ([#309]).

[#6]: https://github.com/metezd/OmniLog/pull/6
[#18]: https://github.com/metezd/OmniLog/pull/18
[#49]: https://github.com/metezd/OmniLog/issues/49
[#54]: https://github.com/metezd/OmniLog/issues/54
[#78]: https://github.com/metezd/OmniLog/pull/78
[#84]: https://github.com/metezd/OmniLog/pull/84
[#145]: https://github.com/metezd/OmniLog/issues/145
[#152]: https://github.com/metezd/OmniLog/issues/152
[#188]: https://github.com/metezd/OmniLog/pull/188
[#212]: https://github.com/metezd/OmniLog/pull/212
[#227]: https://github.com/metezd/OmniLog/pull/227
[#234]: https://github.com/metezd/OmniLog/pull/234
[#240]: https://github.com/metezd/OmniLog/pull/240
[#252]: https://github.com/metezd/OmniLog/issues/252
[#254]: https://github.com/metezd/OmniLog/pull/254
[#309]: https://github.com/metezd/OmniLog/issues/309
[#310]: https://github.com/metezd/OmniLog/issues/310
[#316]: https://github.com/metezd/OmniLog/issues/316
[#325]: https://github.com/metezd/OmniLog/pull/325
[36c4a3a]: https://github.com/metezd/OmniLog/commit/36c4a3a
[d97f3f3]: https://github.com/metezd/OmniLog/commit/d97f3f3
[6ef2769]: https://github.com/metezd/OmniLog/commit/6ef2769
[48a22cf]: https://github.com/metezd/OmniLog/commit/48a22cf
[b58fc9e]: https://github.com/metezd/OmniLog/commit/b58fc9e
[678160a]: https://github.com/metezd/OmniLog/commit/678160a
