# AI Usage Notes: Mohammed Edris (@Mhmd77Edrees)

Part of the review checklist in #252 (section E).

## Tools

- Claude Code (Claude Opus 5.5): repository analysis, code changes, tests and documentation.
- ChatGPT: coding assistance, Git guidance and documentation updates.

## Work done with AI

| Work | What the AI did | How it was checked |
|---|---|---|
| [#171](https://github.com/metezd/OmniLog/pull/171) - Vitest upgrade | Assisted with dependency updates and troubleshooting | PR reports 209 passing tests and a successful production build |
| [#231](https://github.com/metezd/OmniLog/pull/231) - API hardening | Code, tests and documentation | CI and approval by metezd |
| [#235](https://github.com/metezd/OmniLog/pull/235) - Python version | Assisted with CI configuration and deprecated API replacements | PR reports 95 passing local tests and successful CI |
| [#236](https://github.com/metezd/OmniLog/pull/236) - Rate limits | Assisted with implementation, tests and documentation | PR reports 768 passing backend tests and 187 passing frontend tests |
| [#237](https://github.com/metezd/OmniLog/pull/237) - Passlib replacement | Assisted with bcrypt migration, dependency locking and tests | PR reports 784 passing tests and 91% coverage |
| [#259](https://github.com/metezd/OmniLog/pull/259) - Penetration testing and TDD evidence | Assisted with local testing, git history analysis and documentation | Findings checked against configuration and recorded test results |
| [#260](https://github.com/metezd/OmniLog/pull/260) - Render configuration | Assisted with disabling API documentation and adding regression tests | PR reports 93 passing tests |
| [#345](https://github.com/metezd/OmniLog/pull/345) - TDD evidence | Assisted with test history analysis and documentation | PR reports 17 passing tests and repeated red/green runs |
| [#346](https://github.com/metezd/OmniLog/pull/346) - AI mistakes register | Assisted with collecting and documenting AI mistakes | PR reports 9 passing tests and reference checks |

## AI mistakes that were caught

| Mistake | How it was caught | Fix | Severity |
|---|---|---|---|
| The token change in #231 broke an existing token lifetime test | CI failure | Fixed in [c841987](https://github.com/metezd/OmniLog/commit/c841987) | Minor |
| ENABLE_DOCS was missing from render.yaml | Penetration test finding F2 | Fixed in [a247f0b](https://github.com/metezd/OmniLog/commit/a247f0b) | Medium |
| The initial RATE-02 result was affected by the local test configuration | Configuration review and repeated local testing | Corrected in the penetration test report | Incorrect initial explanation |
| Incorrect failed/passed test counts in the first TDD draft | Review of the complete test output | Corrected in #345 | Minor |
| An existing warning was incorrectly considered an AI mistake | Review of the original PR | Removed from the register in #346 | Minor |

## Limits

- AI-generated changes require human review before merging.
- AI output is not a substitute for test results, CI or reviewer approval.
- Test results must not be reported as successful without supporting evidence.
- Local security test results do not establish that the deployed service has been verified.
- The commits of #231 have no AI attribution line, so this file records AI use for that PR.
- I am responsible for understanding and explaining the changes submitted under my account.