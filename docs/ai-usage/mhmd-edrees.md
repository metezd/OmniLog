# AI Usage Notes: Mhmd77Edrees

Part of the review checklist in #252 (section E). These notes record where AI was used in this member's work, what was checked by hand, and which AI mistakes were caught.

**Tool:** Claude Code (model Claude Opus 5.5), working as an agent with access to the repository, a shell and the browser.

## Work done with AI

| Work | What the AI did | How it was checked |
|---|---|---|
| #231 API hardening (closes #220) | Read the issue, wrote the code, tests and docs, opened the PR | CI, and approval by `metezd` |
| Penetration test (`docs/tests/penetration`, `tests/pentest`) | Wrote and ran the attack script, reviewed the deployment files, drafted the report | Each finding checked against the config. F1 has a local proof |
| TDD evidence (`docs/tests/tdd-evidence.md`) | Searched the git history and ran the tests again from old commits | The commands in the document can be repeated |

<!-- TODO(Mhmd77Edrees): add your other PRs here if AI helped with them, for example the rate limits, the Python version and the passlib replacement. Only you know this. -->

## AI mistakes that were caught

| Mistake | How it was caught | Fix | Severity |
|---|---|---|---|
| In #231 the AI added `iat` to the token but ran only part of the tests, so `test_epic2_token_lifetime.py` broke | CI failed on the PR | `c841987` updated the test | Minor |
| In #231 the AI set `ENABLE_DOCS=false` in `docker-compose.prod.yml` but missed `render.yaml`, so the docs stay public on Render | The penetration test (finding F2) | Open | Medium |
| In the penetration test, the first result for `X-Forwarded-For` (RATE-02) came from the local setup, because uvicorn trusts `127.0.0.1` | Reading the deployment files and a second run with the options of `render.yaml` | The report explains the real risk (F1) | Would have given a wrong reason |

## Limits

- The commits of #231 have no AI attribution line, so this file is the record of AI use for that PR.
- The member reviews and must be able to explain all AI output before it is merged.
