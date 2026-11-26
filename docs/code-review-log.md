# Code review log

This log shows how the pull requests of OmniLog were reviewed. It is part of #252, section C (Code reviews, Pull requests used), and was made for #293. The rules are in [CONTRIBUTING.md](../CONTRIBUTING.md#code-review).

## How the data was collected

All merged pull requests up to 2026-11-26 (#1 to #358, 180 pull requests), with the reviews that GitHub keeps for them:

```bash
gh pr list --state merged --limit 400 --json number,title,author,mergedAt,mergedBy,reviews
```

- **Human reviewer**: the members other than the author who approved. "(changes requested)", "(comment only)" and "(dismissed)" mark a review without an approval. A dismissed approval was removed by a later push.
- **Copilot**: the Copilot review ran on the pull request. It is an extra reader and never counts as an approval.
- **Changes requested**: a reviewer selected "Request changes" at least once.
- **Outcome**: for a pull request without a human approval, the real reason from the data. No review was added afterwards.

## Summary

| Outcome | Pull requests |
|---|---|
| Approved by another member, then merged | 112 |
| No approval: merged by the author, who is the admin of the repository | 32 |
| No approval: merged by the admin for another member | 12 |
| No approval: Dependabot update, merged by the auto-merge workflow after the checks | 9 |
| No approval: merged before the ruleset of `main` existed (2026-10-05) | 6 |
| No approval: its commits reached `main` through another merge, and GitHub marked it as merged | 6 |
| No approval: the approval was dismissed by a later push, then merged by the admin without a new one | 3 |
| **Total** | **180** |

The Copilot review ran on 15 pull requests, and a reviewer requested changes on 3.

What this shows:

- About 6 in 10 pull requests (112 of 180) had an approval from a member other than the author.
- Most pull requests without an approval (47 of 68) were merged by the admin of the repository. The ruleset of `main` needs one approval, but the admin can still merge. GitHub does not keep the history of a ruleset, so this log does not say for each one whether the rule was off at that time or the admin merged past it. These are not hidden: they are listed below as they are.
- The rule is that every pull request waits for one approval from another member, also those of the admin. The ruleset cannot stop the admin, so the team keeps this rule by hand. The review rota in [CONTRIBUTING.md](../CONTRIBUTING.md#review-rota) says who reviews each area, so no pull request waits for a reviewer.

## Reviews that changed the code

Three pull requests where a review comment led to a change before the merge:

1. **#1, project charter.** Yeşim Yiğitbaşı requested changes: the section names did not follow the charter template, the possible customers were missing from "Stakeholders & Roles", the repository URL was empty and the AI stack did not say which AI tools the team uses. The author changed all of it in `2d7fb4d` ("update charter based on feedback") the same day.
2. **#81, search bar.** Mete Özdoğan asked to delete `frontend/public/kagan.jpg`, a photo that no page used. Later he requested changes again because comments in the code were in Turkish. Kerem Kenet removed the photo in `48132ff` and translated the comments in `08e4cee` eight minutes after the review, then answered "Replaced comments".
3. **#179, design diagrams.** Yeşim Yiğitbaşı requested changes: the report did not explain how the non-functional requirements are handled. She asked for a table that maps each NFR to a design decision, a tool and a place in the repository. Kerem Kenet aligned the diagrams with the code in `6ccdca9` and added the NFR mapping and the sequence walkthroughs to `software-design-report.md` in `70c9f79`.

## All merged pull requests

Newest first.

| PR | Merged | Title | Author | Human reviewer | Copilot | Changes requested | Outcome |
|---|---|---|---|---|---|---|---|
| #358 | 2026-11-26 | feat(igdb): add outgoing request limiter and batched game details query | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #357 | 2026-11-26 | feat: enhance caching mechanism with Redis and PostgreSQL integration | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #352 | 2026-11-26 | docs(tests): write the Software Testing Report | sidarurey | metezd | no | no | Approved, then merged |
| #351 | 2026-11-26 | test(security): retest on the production stack with pgvector and OWASP ZAP | sidarurey | metezd | no | no | Approved, then merged |
| #350 | 2026-11-26 | docs(tests): complete the red then green cycles of the testing phase | sidarurey | metezd | no | no | Approved, then merged |
| #349 | 2026-11-26 | fix: clear the SonarQube findings and write the analysis | sidarurey | metezd | no | no | Approved, then merged |
| #348 | 2026-11-26 | test(security): retest the penetration findings after the fixes | Mhmd77Edrees | metezd | no | no | Approved, then merged |
| #347 | 2026-11-26 | docs: complete AI usage notes for issue 317 | Mhmd77Edrees | - | no | no | No approval: merged by metezd (admin of the repository) |
| #346 | 2026-11-26 | docs(ai): add the register of AI mistakes that were caught | Mhmd77Edrees | metezd | no | no | Approved, then merged |
| #345 | 2026-11-26 | docs(tests): add TDD rows for every story and the red then green fix cycles | Mhmd77Edrees | metezd, sidarurey (comment only) | no | no | Approved, then merged |
| #344 | 2026-11-26 | refactor(api): remove duplicate list delete routes (#305) | KaganKonuk | metezd, sidarurey (comment only) | no | no | Approved, then merged |
| #343 | 2026-11-25 | fix: F7, hide the server software and send the security headers everywhere | sidarurey | metezd | no | no | Approved, then merged |
| #342 | 2026-11-25 | fix: F3, check poster_url on update and add a Content-Security-Policy | sidarurey | metezd | no | no | Approved, then merged |
| #341 | 2026-11-25 | fix: F4, F5, F6 and deep JSON, malformed input gets 4xx and small answers | sidarurey | metezd | yes | no | Approved, then merged |
| #340 | 2026-11-25 | fix: F1, count the address that the proxy of Render writes | sidarurey | metezd | no | no | Approved, then merged |
| #339 | 2026-11-25 | test(requirements): check that every requirement has tests and write the matrix | sidarurey | metezd | no | no | Approved, then merged |
| #338 | 2026-11-25 | test(performance): add an HTTP load test and measure the production stack | sidarurey | metezd | no | no | Approved, then merged |
| #337 | 2026-11-25 | docs: add AI usage notes of Musab Alperen Başol | musabalperenbasol | metezd | no | no | Approved, then merged |
| #335 | 2026-11-25 | test(frontend): add tests for the poster proxy route | KeremKenet | metezd | no | no | Approved, then merged |
| #334 | 2026-11-25 | test(coverage): raise the gate to 90%, add frontend coverage and show it in CI | sidarurey | metezd | no | no | Approved, then merged |
| #333 | 2026-11-25 | chore: remove friends feature and update login page | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #331 | 2026-11-25 | test: freeze the rate limit clock in the client address tests | sidarurey | metezd | no | no | Approved, then merged |
| #330 | 2026-11-25 | feat: add recommendations page, server actions, and types with tests | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #329 | 2026-11-25 | fix(api): count the browser address behind Render and allow an empty REDIS_URL | sidarurey | metezd | no | no | Approved, then merged |
| #328 | 2026-11-25 | fix(api): close open write access to the catalog through /media | sidarurey | - | no | no | No approval: merged by metezd (admin of the repository) |
| #327 | 2026-11-25 | Frontend S06: Add Review box and spoiler  | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #326 | 2026-11-24 | fix(frontend): proxy external catalog posters through /api/poster wit… | KeremKenet | metezd (dismissed) | no | no | No approval: the approval was dismissed by a later push, then merged by metezd (admin of the repository) without a new one |
| #325 | 2026-11-24 | chore: release 0.8.0 | musabalperenbasol | - | no | no | No approval: merged by metezd (admin of the repository) |
| #324 | 2026-11-24 | docs: add the AI assistance convention | sidarurey | - | no | no | No approval: merged by metezd (admin of the repository) |
| #323 | 2026-11-24 | docs(ai): document the AI pipeline of the project | sidarurey | - | no | no | No approval: merged by metezd (admin of the repository) |
| #322 | 2026-11-24 | ci: add a SonarQube scan with the backend coverage | sidarurey | - | no | no | No approval: merged by metezd (admin of the repository) |
| #321 | 2026-11-24 | fix: make the tests pass in a clean clone and update stale docs | sidarurey | - | no | no | No approval: merged by metezd (admin of the repository) |
| #320 | 2026-11-24 | ci: check branch names and pull request titles | sidarurey | - | no | no | No approval: merged by metezd (admin of the repository) |
| #319 | 2026-11-24 | docs(ai): add the AI usage notes of Sidar Ürey | sidarurey | - | no | no | No approval: merged by metezd (admin of the repository) |
| #318 | 2026-11-24 | docs(ai): add the evidence of AI use beyond autocomplete | sidarurey | - | no | no | No approval: merged by metezd (admin of the repository) |
| #260 | 2026-11-23 | fix(deploy): turn off the API docs on Render | Mhmd77Edrees | metezd (dismissed) | no | no | No approval: the approval was dismissed by a later push, then merged by metezd (admin of the repository) without a new one |
| #259 | 2026-11-23 | test(security): add penetration test, TDD evidence and AI usage notes | Mhmd77Edrees | metezd | no | no | Approved, then merged |
| #258 | 2026-11-23 | feat: implement personalized recommendations (US-13) | sidarurey | metezd | no | no | Approved, then merged |
| #257 | 2026-11-25 | chore(deps-dev): bump @testing-library/user-event from 14.6.10 to 14.6.12 in /frontend | Dependabot | metezd | no | no | Approved, then merged |
| #256 | 2026-11-25 | chore(deps): bump lucide-react from 1.72.0 to 1.75.0 in /frontend | Dependabot | metezd | no | no | Approved, then merged |
| #255 | 2026-11-23 | test(frontend): add tests for the statistics screen | KeremKenet | metezd | no | no | Approved, then merged |
| #254 | 2026-11-22 | fix: save review before spoiler check and keep spoiler fields NULL on failure | musabalperenbasol | metezd | no | no | Approved, then merged |
| #253 | 2026-11-22 | Chore/GitHub workflow delivery | KaganKonuk | metezd | no | no | Approved, then merged |
| #249 | 2026-11-21 | Update Python version in workflows and render.yaml | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #248 | 2026-11-21 | Implement database URL normalization for PostgreSQL connections | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #247 | 2026-11-21 | feat: add media title embeddings (#151) | sidarurey | metezd | no | no | Approved, then merged |
| #246 | 2026-11-20 | feat(ui): add 3D Manta ASCII swarm preset and boost liquid-glass contrast | KeremKenet | metezd | no | no | Approved, then merged |
| #245 | 2026-11-20 | style(ui): increase liquid-glass surface opacity and text contrast fo… | KeremKenet | metezd | no | no | Approved, then merged |
| #244 | 2026-11-20 | refactor(frontend): remove draft leftovers, mark /friends as demo, and fix footer links (#124) | KeremKenet | metezd | no | no | Approved, then merged |
| #243 | 2026-11-20 | feat(frontend): implement S-01 landing page and remove mock dashboard (#123) | KeremKenet | metezd | no | no | Approved, then merged |
| #242 | 2026-11-20 | Implement manual sync functionality and update documentation | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #240 | 2026-11-20 | perf(backend): add diary indexes and paging to long lists | musabalperenbasol | metezd | no | no | Approved, then merged |
| #239 | 2026-11-19 | Cap GET /stats playtime histogram at 100+h and 21 buckets (Closes #216) | KaganKonuk | metezd | no | no | Approved, then merged |
| #238 | 2026-11-19 | feat: add library entry reviews endpoint | sidarurey | metezd | no | no | Approved, then merged |
| #237 | 2026-11-19 | chore(deps): replace passlib with bcrypt and pin the backend versions | Mhmd77Edrees | metezd | no | no | Approved, then merged |
| #236 | 2026-11-19 | feat(api): rate limits for login, register, search and review | Mhmd77Edrees | metezd | no | no | Approved, then merged |
| #235 | 2026-11-19 | chore(backend): test the Python version of the production image | Mhmd77Edrees | metezd | no | no | Approved, then merged |
| #233 | 2026-11-19 | Update NODE_VERSION to 26 for frontend compatibility | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #232 | 2026-11-19 | Enhance environment configuration and improve documentation | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #231 | 2026-11-19 | chore(security): API hardening - token claims, security headers, docs switch | Mhmd77Edrees | metezd | no | no | Approved, then merged |
| #230 | 2026-11-20 | feat: add 5x 3D parametric jellyfish/betta swarm, ambient rain/star F… | KeremKenet | metezd, musabalperenbasol | no | no | Approved, then merged |
| #229 | 2026-11-19 | feat: implement custom list deletion and list item removal endpoints … | KaganKonuk | metezd | no | no | Approved, then merged |
| #228 | 2026-11-20 | feat: add catalog search and title details service | metezd | - | yes | no | No approval: merged by the author (admin of the repository) |
| #227 | 2026-11-18 | fix(backend): correct spoiler patterns in the review fallback detector | musabalperenbasol | metezd | no | no | Approved, then merged |
| #226 | 2026-11-18 | NFR-02: Complete the protected-endpoint auth test coverage | metezd | musabalperenbasol | no | no | Approved, then merged |
| #225 | 2026-11-18 | US-15: Add backend services for chapters, journals, library, and stats | metezd | musabalperenbasol | no | no | Approved, then merged |
| #223 | 2026-11-18 | feat: add readiness and health endpoints for Render | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #214 | 2026-11-18 | Feature/ascii background and sqlite fix | KeremKenet | metezd | no | no | Approved, then merged |
| #213 | 2026-11-18 | feat(ui): add global ASCII creature swarm with liquid-glass dashboard… | KeremKenet | metezd | no | no | Approved, then merged |
| #212 | 2026-11-17 | test(nfr): finish NFR-01/02/04 checks and remove not_built helper | musabalperenbasol | metezd | no | no | Approved, then merged |
| #205 | 2026-11-17 | chore(quality): resolve all remaining SonarQube code smells for Issue… | KaganKonuk | metezd | no | no | Approved, then merged |
| #204 | 2026-11-16 | chore(deps): override minimatch in typescript-estree | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #203 | 2026-11-16 | chore(deps): bump actions/labeler from 5.0.0 to 7.0.0 | Dependabot | metezd | no | no | Approved, then merged |
| #202 | 2026-11-16 | chore(deps): bump actions/labeler from 5 to 7 | Dependabot | metezd | no | no | Approved, then merged |
| #201 | 2026-11-16 | feat(security): add security linting with Ruff and Gitleaks workflows | metezd | Mhmd77Edrees (dismissed) | no | no | No approval: the approval was dismissed by a later push, then merged by metezd (admin of the repository) without a new one |
| #199 | 2026-11-15 | chore(deps): bump axios from 1.20.0 to 1.21.1 in /frontend | Dependabot | - | no | no | No approval: Dependabot update merged by the auto-merge workflow after the checks |
| #198 | 2026-11-15 | chore(deps): bump lucide-react from 1.71.0 to 1.72.0 in /frontend | Dependabot | - | no | no | No approval: Dependabot update merged by the auto-merge workflow after the checks |
| #197 | 2026-11-15 | chore(deps): bump react-hook-form from 7.91.0 to 7.92.0 in /frontend | Dependabot | - | no | no | No approval: Dependabot update merged by the auto-merge workflow after the checks |
| #196 | 2026-11-15 | chore(deps-dev): bump @testing-library/user-event from 14.6.9 to 14.6.10 in /frontend | Dependabot | - | no | no | No approval: Dependabot update merged by the auto-merge workflow after the checks |
| #195 | 2026-11-15 | chore(deps): update fastapi requirement from >=0.162.2 to >=0.162.5 in /backend | Dependabot | - | no | no | No approval: Dependabot update merged by the auto-merge workflow after the checks |
| #194 | 2026-11-15 | chore(deps): update openai requirement from >=3.48.0 to >=3.50.0 in /backend | Dependabot | - | no | no | No approval: Dependabot update merged by the auto-merge workflow after the checks |
| #193 | 2026-11-15 | chore(deps): bump node from 24-alpine to 26-alpine in /frontend | Dependabot | - | no | no | No approval: Dependabot update merged by the auto-merge workflow after the checks |
| #192 | 2026-11-15 | chore(deps): bump python from 3.11-slim-bookworm to 3.15-slim-bookworm in /backend | Dependabot | - | no | no | No approval: Dependabot update merged by the auto-merge workflow after the checks |
| #191 | 2026-11-15 | feat(frontend): implement custom list management screens S-07/S-08 wi… | KeremKenet | metezd | no | no | Approved, then merged |
| #190 | 2026-11-15 | feat(frontend): handle missing metadata/chapters and add unit tests f… | KeremKenet | metezd | no | no | Approved, then merged |
| #189 | 2026-11-15 | test(frontend): add unit tests for catalog search screen and navbar s… | KeremKenet | metezd | no | no | Approved, then merged |
| #188 | 2026-11-15 | feat(backend): fill igdb id and decisions for life is strange seed | musabalperenbasol | metezd | no | no | Approved, then merged |
| #187 | 2026-11-14 | feat: add OpenAI integration for embeddings and spoiler detection | sidarurey | metezd | no | no | Approved, then merged |
| #186 | 2026-11-14 | docs: choose text-embedding-3-small with 1536 dimensions (#44) | sidarurey | metezd | no | no | Approved, then merged |
| #184 | 2026-11-15 | chore(deps-dev): bump @testing-library/user-event from 14.6.8 to 14.6.9 in /frontend | Dependabot | metezd | no | no | Approved, then merged |
| #183 | 2026-11-15 | chore(deps): bump lucide-react from 1.68.0 to 1.71.0 in /frontend | Dependabot | metezd | no | no | Approved, then merged |
| #182 | 2026-11-15 | chore(deps-dev): bump @testing-library/jest-dom from 6.9.1 to 7.0.1 in /frontend | Dependabot | metezd | no | no | Approved, then merged |
| #181 | 2026-11-15 | chore(deps): bump the next group in /frontend with 2 updates | Dependabot | metezd | no | no | Approved, then merged |
| #180 | 2026-11-14 | chore(deps): update openai requirement from >=3.45.0 to >=3.48.0 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #179 | 2026-11-15 | docs: add architecture, class and sequence diagrams for design document | KeremKenet | yesimyigitbasi (changes requested) | yes | yes | No approval: merged by metezd (admin of the repository) |
| #178 | 2026-11-11 | chore(deps-dev): bump @tailwindcss/postcss from 4.3.3 to 4.3.5 in /frontend | Dependabot | KeremKenet | no | no | Approved, then merged |
| #177 | 2026-11-11 | chore(deps): bump the react group in /frontend with 2 updates | Dependabot | KeremKenet | no | no | Approved, then merged |
| #176 | 2026-11-11 | chore(deps): update fastapi requirement from >=0.162.0 to >=0.162.2 in /backend | Dependabot | KeremKenet | no | no | Approved, then merged |
| #175 | 2026-11-11 | chore(deps): update pyjwt requirement from >=2.8.0 to >=2.15.1 in /backend | Dependabot | KeremKenet | no | no | Approved, then merged |
| #174 | 2026-11-11 | fix(security): replace python-jose with PyJWT, integrate pip-audit into CI, and add 6.3 security regression suite | KaganKonuk | KeremKenet | no | no | Approved, then merged |
| #172 | 2026-11-11 | Feat/catalog and media colors | KeremKenet | musabalperenbasol | no | no | Approved, then merged |
| #171 | 2026-11-10 | fix: upgrade vitest to v5 | Mhmd77Edrees | metezd | no | no | Approved, then merged |
| #170 | 2026-11-11 | Feat/epic5 and UI screens | KeremKenet | musabalperenbasol | no | no | Approved, then merged |
| #169 | 2026-11-11 | Phase1 1 | KeremKenet | - | no | no | No approval: its commits reached `main` through another merge, so GitHub marked it as merged |
| #168 | 2026-11-11 | fix(docker): use numeric UID 10001 in Dockerfiles for Hadolint DL3066 | KeremKenet | - | no | no | No approval: its commits reached `main` through another merge, so GitHub marked it as merged |
| #167 | 2026-11-11 | Updates have been made to the login and authentication services | KeremKenet | - | no | no | No approval: its commits reached `main` through another merge, so GitHub marked it as merged |
| #159 | 2026-11-09 | feat: personal statistics and docker fix | metezd | - | yes | no | No approval: merged by the author (admin of the repository) |
| #144 | 2026-11-07 | feat(frontend): add search page connected to the catalog API | KeremKenet | metezd | no | no | Approved, then merged |
| #143 | 2026-11-07 | feat(epic5): implement US-13 cross-media recommendations | KaganKonuk | metezd | yes | no | Approved, then merged |
| #141 | 2026-11-07 | chore(deps-dev): bump @types/node from 24.19.2 to 26.6.6 in /frontend | Dependabot | metezd | no | no | Approved, then merged |
| #140 | 2026-11-07 | chore(deps): bump lucide-react from 1.52.0 to 1.68.0 in /frontend | Dependabot | metezd | no | no | Approved, then merged |
| #139 | 2026-11-07 | chore(deps): bump react-hook-form from 7.90.0 to 7.91.0 in /frontend | Dependabot | metezd | no | no | Approved, then merged |
| #137 | 2026-11-07 | chore(deps): update sqlalchemy requirement from >=2.1.6 to >=2.1.8 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #136 | 2026-11-07 | chore(deps): update openai requirement from >=3.42.1 to >=3.45.0 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #135 | 2026-11-08 | chore(deps): bump actions/setup-python from 5 to 7 | Dependabot | metezd | no | no | Approved, then merged |
| #134 | 2026-11-08 | chore(deps): bump hadolint/hadolint-action from 3.1.0 to 3.5.0 | Dependabot | - | no | no | No approval: Dependabot update merged by the auto-merge workflow after the checks |
| #133 | 2026-11-07 | chore(deps): bump actions/checkout from 4 to 7 | Dependabot | metezd | no | no | Approved, then merged |
| #132 | 2026-11-08 | chore(deps): bump actions/upload-artifact from 4 to 7 | Dependabot | metezd | no | no | Approved, then merged |
| #131 | 2026-11-07 | chore(deps): bump actions/setup-node from 4 to 7 | Dependabot | metezd | no | no | Approved, then merged |
| #130 | 2026-11-07 | Project tooling: test setup, dependency security and contribution workflow | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #129 | 2026-11-11 | feat(frontend): add search page with mock TMDB/IGDB catalog | KeremKenet | - | yes | no | No approval: its commits reached `main` through another merge, so GitHub marked it as merged |
| #112 | 2026-11-06 | chore(deps): update openai requirement from >=3.41.0 to >=3.42.1 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #111 | 2026-11-02 | chore(deps): update openai requirement from >=3.37.0 to >=3.41.0 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #110 | 2026-11-02 | chore(deps): update pydantic requirement from >=2.14.1 to >=2.14.2 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #109 | 2026-11-02 | chore(deps): update fastapi requirement from >=0.161.1 to >=0.162.0 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #107 | 2026-10-27 | Feat/backend infrastructure | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #106 | 2026-10-26 | Frontend authentication and library page | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #105 | 2026-10-26 | chore(deps): update alembic requirement from >=1.20.0 to >=1.20.1 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #104 | 2026-10-26 | chore(deps): update openai requirement from >=1.20.0 to >=3.37.0 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #103 | 2026-10-26 | chore(deps): update fastapi requirement from >=0.143.0 to >=0.161.1 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #102 | 2026-10-26 | chore(deps): update sqlalchemy requirement from >=2.1.2 to >=2.1.6 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #97 | 2026-10-22 | feat(frontend): add friends page with add-friend and activity feed | KeremKenet | metezd | no | no | Approved, then merged |
| #96 | 2026-10-25 | Fix/frontend tests | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #94 | 2026-10-22 | Fix/login | metezd | KaganKonuk | no | no | Approved, then merged |
| #93 | 2026-10-20 | Fix pytest test failures and configuration errors | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #92 | 2026-10-20 | Docker configuration and production deployment setup | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #90 | 2026-10-20 | US11-12: Implement playtime logging and chapter progress tracking | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #87 | 2026-10-17 | feat: add testing setup with Vitest and Testing Library | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #86 | 2026-10-18 | Feat/us11 log playtime | metezd | - | yes | no | No approval: merged by the author (admin of the repository) |
| #85 | 2026-10-17 | Feat/us10 chapter rating | metezd | - | yes | no | No approval: merged by the author (admin of the repository) |
| #84 | 2026-10-17 | feat(epic3): implement US-09 title details with seasons and chapters | musabalperenbasol | metezd | no | no | Approved, then merged |
| #83 | 2026-11-11 | feat(frontend): update navbar, logo, layout and media stream | KeremKenet | metezd (dismissed) | no | no | No approval: its commits reached `main` through another merge, so GitHub marked it as merged |
| #82 | 2026-11-11 | Feature/media stream clean | KeremKenet | metezd (dismissed) | no | no | No approval: its commits reached `main` through another merge, so GitHub marked it as merged |
| #81 | 2026-11-11 | Feature/search bar | KeremKenet | metezd | no | yes | Approved, then merged |
| #80 | 2026-10-16 | Review suggestions | metezd | musabalperenbasol | no | no | Approved, then merged |
| #79 | 2026-10-15 | feat: implement custom lists and activity diary features (US-06, US-07) with validation and event logging | metezd | - | yes | no | No approval: merged by the author (admin of the repository) |
| #78 | 2026-10-15 | feat(library): optimize entry listing with joinedload to reduce query count | musabalperenbasol | metezd | no | no | Approved, then merged |
| #77 | 2026-10-15 | feat(semgrep): update Semgrep configuration and rules for enhanced security checks | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #76 | 2026-10-15 | feat(epic2): implement US-06 custom lists and US-07 activity diary | KaganKonuk | metezd | yes | no | Approved, then merged |
| #75 | 2026-10-15 | feat(search): add live search bar to Navbar with SearchContext | KeremKenet | metezd | no | no | Approved, then merged |
| #69 | 2026-10-15 | feat(library, media): implement library and media endpoints with CRUD operations | metezd | KaganKonuk | yes | no | Approved, then merged |
| #68 | 2026-10-15 | fix(imports): resolve path alias errors for SearchContext using relat… | KeremKenet | KaganKonuk | no | no | Approved, then merged |
| #67 | 2026-10-15 | chore(deps): update pydantic requirement from >=2.6.0 to >=2.14.1 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #66 | 2026-10-15 | Step 2 authentication | metezd | KaganKonuk | yes | no | Approved, then merged |
| #41 | 2026-10-14 | Refactor requirement analysis and complete Phase 1 | metezd | - | yes | no | No approval: merged by the author (admin of the repository) |
| #37 | 2026-10-15 | chore(deps): update fastapi requirement from >=0.110.0 to >=0.143.0 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #35 | 2026-10-14 | Update README.md | metezd | musabalperenbasol | no | no | Approved, then merged |
| #34 | 2026-10-14 | Add Semgrep | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #32 | 2026-10-14 | Add CI workflow for backend and frontend testing | metezd | - | yes | no | No approval: merged by the author (admin of the repository) |
| #31 | 2026-10-14 | Add full analysis docs for all project epics | metezd | KeremKenet (comment only), yesimyigitbasi (comment only) | no | no | No approval: merged by the author (admin of the repository) |
| #30 | 2026-10-14 | Revert "Add OmniLog domain model and ER diagram documentation" | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #26 | 2026-10-13 | Add API integration level 0 and level 1 DFD documentation | metezd | KaganKonuk | no | no | Approved, then merged |
| #25 | 2026-10-14 | Feature/theme horizon palette | KeremKenet | - | yes | no | No approval: merged by metezd (admin of the repository) |
| #24 | 2026-10-13 | Analysis work | metezd | KaganKonuk | no | no | Approved, then merged |
| #23 | 2026-10-13 | Add OmniLog domain model and ER diagram documentation | metezd | KaganKonuk | no | no | Approved, then merged |
| #22 | 2026-10-13 | feat(frontend): implement authentication forms and integrate liquid glass logo | KeremKenet | metezd | no | no | Approved, then merged |
| #21 | 2026-10-13 | Feature/frontend layout | KeremKenet | metezd, musabalperenbasol | no | no | Approved, then merged |
| #20 | 2026-10-12 | refactor(backend): read DATABASE_URL from environment and make engine… | KeremKenet | metezd | no | no | Approved, then merged |
| #19 | 2026-10-12 | Added GitHub Actions workflows for backend and frontend CI/CD pipelines | metezd | - | no | no | No approval: merged by the author (admin of the repository) |
| #18 | 2026-10-12 | docs: requirements definition (plan, user stories, tests, specification report) | musabalperenbasol | yesimyigitbasi | no | no | Approved, then merged |
| #14 | 2026-10-06 | chore(deps): update sqlalchemy requirement from >=2.0.0 to >=2.1.2 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #13 | 2026-10-06 | chore(deps): update alembic requirement from >=1.13.0 to >=1.20.0 in /backend | Dependabot | metezd | no | no | Approved, then merged |
| #9 | 2026-10-05 |  add dependabot | metezd | - | no | no | No approval: merged before the ruleset of `main` existed (2026-10-05) |
| #8 | 2026-10-04 | feat(frontend): initialize Next.js app with Tailwind and UI dependencies | KeremKenet | - | no | no | No approval: merged before the ruleset of `main` existed (2026-10-05) |
| #7 | 2026-10-04 | chore(backend): add alembic, httpx and openai dependencies | KeremKenet | - | no | no | No approval: merged before the ruleset of `main` existed (2026-10-05) |
| #6 | 2026-10-04 | feat: add Pydantic v2 schemas (user, media, library) | musabalperenbasol | - | no | no | No approval: merged before the ruleset of `main` existed (2026-10-05) |
| #5 | 2026-10-04 | feat: add MOVIE to MediaType enum | KaganKonuk | metezd | no | no | Approved, then merged |
| #4 | 2026-10-03 | feat: define SQLAlchemy models for User, MediaItem, and UserLibrary | KaganKonuk | - | no | no | No approval: merged before the ruleset of `main` existed (2026-10-05) |
| #2 | 2026-10-01 | feat: initialize backend folder structure and health check endpoint | KaganKonuk | metezd | no | no | Approved, then merged |
| #1 | 2026-10-01 | docs(charter): add project charter | metezd | yesimyigitbasi (changes requested) | no | yes | No approval: merged before the ruleset of `main` existed (2026-10-05) |
