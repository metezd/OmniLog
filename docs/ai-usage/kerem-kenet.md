# AI Usage Notes: Kerem Kenet (`KeremKenet`)

Part of the review checklist in [#252] (section E). Issue: [#313]. These notes record where AI was used in my work, how it was checked, and how the frontend instruction files worked. Role: Frontend Lead.

## 1. Tools

| Tool | Model | How it was used | Pull requests |
|---|---|---|---|
| Claude (chat on claude.ai) | Claude Opus / Sonnet (version not recorded) | Chat for UI styling ideas, HTML5 Canvas math for the 3D parametric ASCII background, and component refactoring. I reviewed and tested the code in the browser before committing | [#213], [#214], [#230] |
| Claude Code (desktop agent) | Claude Sonnet 5.5 / Claude Opus 5.5 | An agent with access to the repository and a shell: read the linked issues and codebase, drafted unit tests, frontend pages, design report updates, and this document, and ran ESLint/Vitest checks | [#179], [#189], [#190], [#191], [#243], [#244], [#245], [#246], [#255], [#326], [#335], and this file ([#313]) |

## 2. Work done with AI

| Pull request | What the AI did | How it was checked |
|---|---|---|
| [#179] Software Design Report diagrams and NFR mapping | Assisted with aligning PlantUML architecture, class, and sequence diagrams with the repository files and adding the NFR mapping table and sequence walkthroughs ([`6ccdca9`][6ccdca9], [`70c9f79`][70c9f79]) after `yesimyigitbasi`'s review | Verified every referenced file path, class, field, and route in `backend/app/` and `frontend/src/`, rendered all 17 `.puml` diagrams with zero syntax errors, inspected the generated PDF, and checked CI |
| [#189] Catalog search and Navbar search unit tests (closes [#119]) | Assisted with Vitest and Testing Library unit tests for the catalog search screen (`S-05`) and Navbar search bar | Ran `npm run lint`, `npx tsc --noEmit`, and `npm test` locally; CI (`Frontend checks`) passed. Approved by `metezd` |
| [#190] Title details S-06 missing metadata/chapters handling and unit tests (closes [#120]) | Assisted with fallback UI states for missing metadata/chapters on `/title/[id]` and unit tests (`TitleDetailPage.test.tsx`, `LibraryControls.test.tsx`, `ChapterProgressCard.test.tsx`) | Ran `npm run lint`, `npx tsc --noEmit`, and `npm test`; CI passed. Approved by `metezd` |
| [#191] Custom list management screens S-07/S-08 and unit tests (closes [#121]) | Assisted with the `DeleteListButton` confirmation component and unit tests (`CreateListForm.test.tsx`, `DeleteListButton.test.tsx`) | Ran `npm run lint`, `npx tsc --noEmit`, and `npm test`; CI passed. Approved by `metezd` |
| [#213], [#214], [#230], [#245], [#246] Global 3D parametric ASCII creature swarm and liquid-glass contrast | Assisted with the HTML5 Canvas 3D parametric ASCII creature swarm (`GlobalAsciiBackground.tsx` — Jellyfish, Betta, and Manta presets, ambient rain/star FX) and high-contrast `.liquid-glass` styles in `globals.css` | Checked visually in the browser across all routes (`/`, `/library`, `/diary`, `/search`), and ran `npm run lint`, `npx tsc --noEmit`, and `npm run build`. Approved by `metezd` and `musabalperenbasol` |
| [#243] S-01 Landing page and removal of mock dashboard (closes [#123]) | Assisted with updating `frontend/src/app/page.tsx` and `AtmosphericHero.tsx` to render the S-01 Landing Page for visitors and real library data for logged-in users, removing `PaletteTool.tsx` and `MediaStream.tsx`, and adding `LandingPage.test.tsx` | Ran `npm run lint`, `npx tsc --noEmit`, and `npm test`; CI passed. Approved by `metezd` |
| [#244] Remove first-draft leftovers and fix footer links (closes [#124]) | Assisted with removing the unused Axios client (`src/lib/api.ts`), mock catalog service, and non-functional `Forgot?` / `GoogleSignInButton` placeholders, marking `/friends` as a demo, fixing the `/dashboard` footer link, and adding `Footer.test.tsx` | Ran `npm run lint`, `npx tsc --noEmit`, and `npm test`; CI passed. Approved by `metezd` |
| [#255] Tests for the statistics screen (closes [#209]) | Agent (`Co-Authored-By: Claude Sonnet 5.5` on [`8335c9d`][8335c9d]) wrote 14 unit tests in `frontend/tests/app/stats/page.test.tsx` covering the summary cards, four Recharts sections, empty state, and error/redirect handling | Ran `npx vitest run tests/app/stats` (14 passed), `npm run lint`, and `npx tsc --noEmit` locally. Approved by `metezd` |
| [#326] Proxy external catalog posters through `/api/poster` and [#335] poster proxy tests | Assisted with the `/api/poster` image proxy route handler (`frontend/src/app/api/poster/route.ts`) and its unit test suite (`frontend/tests/app/api/poster.test.ts`) | Ran Vitest, `npm run lint`, and `npx tsc --noEmit`, and verified poster rendering in the browser; CI passed. Approved by `metezd` |
| This file, [#313] | Claude Code agent (Claude Opus 5.5) drafted `docs/ai-usage/kerem-kenet.md` and updated `docs/ai-usage/README.md` from my pull requests and commit history | I reviewed every row and link and confirmed that the tools, checks, and scope match my work |

Work done without AI:

- **Code:** Initial Next.js 16 and Tailwind CSS v4 frontend setup ([#8]), backend environment config and dependencies ([#7], [#20]), base layout and authentication forms ([#21], [#22]), Horizon color palette ([#25]), Navbar live search context ([#68], [#75], [#81]), media stream and navbar updates ([#82], [#83]), friends page ([#97]), and initial catalog search page ([#129], [#144]).
- **Reviews:** I did not use AI to review teammates' or Dependabot pull requests ([#31], [#174], [#175], [#176], [#177], [#178]).

## 3. AI mistakes that were caught

No AI mistake is recorded. Every AI-assisted change was checked locally with ESLint (`npm run lint`), TypeScript (`npx tsc --noEmit`), Vitest (`npm test`), and visual inspection in the browser before merge, and no functional or security mistake made by AI was introduced into the repository. Nothing is added to the team register ([#310]).

## 4. Instruction files: `frontend/AGENTS.md` and `frontend/CLAUDE.md`

- **Who wrote them:** [`frontend/AGENTS.md`](../../frontend/AGENTS.md) and [`frontend/CLAUDE.md`](../../frontend/CLAUDE.md) (which contains `@AGENTS.md`) were automatically generated by Next.js 16 (`next dev`, via `node_modules/next/dist/server/lib/generate-agent-files.js`) and committed by me in [`7a1082d`][7a1082d] when initializing the frontend ([#8]). They warn AI agents that Next.js 16 introduces breaking changes compared to older training data and instruct the agent to read `node_modules/next/dist/docs/` and heed deprecation notices.
- **Whether the agent followed them:** Yes, in our App Router pages and component tests ([#189], [#190], [#191], [#243], [#255], [#326], [#335]) the agent followed Next.js 16 and React 19 conventions—such as awaiting `params` and `searchParams` Promises in async Server Components, using `useActionState` from `react` instead of the deprecated `useFormState`, and keeping backend calls inside `server-only` modules.
- **One example where it did not:** When generating UI code via chat without reading `node_modules/next/dist/docs/` from a local install (for example in the early card components and dashboard drafts), the AI used plain HTML `<img>` tags for external poster URLs rather than configuring Next.js image optimization, which triggered `@next/next/no-img-element` lint warnings until we routed external catalog posters through the `/api/poster` proxy endpoint ([#326]).

## 5. Limits

- **What I did not use AI for:** Choosing tasks, designing the Horizon visual identity and color palette ([#25]), building the initial Next.js application structure and auth forms ([#8], [#21], [#22]), or reviewing pull requests.
- **What I would not trust AI with:** Merging pull requests or pushing directly to `main`, adding packages outside the Charter technology stack, accessing real secrets or `.env` files, or judging visual contrast and UI usability without testing the rendered pages in a real browser.
- I am responsible for understanding and explaining every line of code in the pull requests submitted under my account ([#309]).

[#7]: https://github.com/metezd/OmniLog/pull/7
[#8]: https://github.com/metezd/OmniLog/pull/8
[#20]: https://github.com/metezd/OmniLog/pull/20
[#21]: https://github.com/metezd/OmniLog/pull/21
[#22]: https://github.com/metezd/OmniLog/pull/22
[#25]: https://github.com/metezd/OmniLog/pull/25
[#31]: https://github.com/metezd/OmniLog/pull/31
[#68]: https://github.com/metezd/OmniLog/pull/68
[#75]: https://github.com/metezd/OmniLog/pull/75
[#81]: https://github.com/metezd/OmniLog/pull/81
[#82]: https://github.com/metezd/OmniLog/pull/82
[#83]: https://github.com/metezd/OmniLog/pull/83
[#97]: https://github.com/metezd/OmniLog/pull/97
[#119]: https://github.com/metezd/OmniLog/issues/119
[#120]: https://github.com/metezd/OmniLog/issues/120
[#121]: https://github.com/metezd/OmniLog/issues/121
[#123]: https://github.com/metezd/OmniLog/issues/123
[#124]: https://github.com/metezd/OmniLog/issues/124
[#129]: https://github.com/metezd/OmniLog/pull/129
[#144]: https://github.com/metezd/OmniLog/pull/144
[#174]: https://github.com/metezd/OmniLog/pull/174
[#175]: https://github.com/metezd/OmniLog/pull/175
[#176]: https://github.com/metezd/OmniLog/pull/176
[#177]: https://github.com/metezd/OmniLog/pull/177
[#178]: https://github.com/metezd/OmniLog/pull/178
[#179]: https://github.com/metezd/OmniLog/pull/179
[#189]: https://github.com/metezd/OmniLog/pull/189
[#190]: https://github.com/metezd/OmniLog/pull/190
[#191]: https://github.com/metezd/OmniLog/pull/191
[#209]: https://github.com/metezd/OmniLog/issues/209
[#213]: https://github.com/metezd/OmniLog/pull/213
[#214]: https://github.com/metezd/OmniLog/pull/214
[#230]: https://github.com/metezd/OmniLog/pull/230
[#243]: https://github.com/metezd/OmniLog/pull/243
[#244]: https://github.com/metezd/OmniLog/pull/244
[#245]: https://github.com/metezd/OmniLog/pull/245
[#246]: https://github.com/metezd/OmniLog/pull/246
[#252]: https://github.com/metezd/OmniLog/issues/252
[#255]: https://github.com/metezd/OmniLog/pull/255
[#309]: https://github.com/metezd/OmniLog/issues/309
[#310]: https://github.com/metezd/OmniLog/issues/310
[#313]: https://github.com/metezd/OmniLog/issues/313
[#326]: https://github.com/metezd/OmniLog/pull/326
[#335]: https://github.com/metezd/OmniLog/pull/335
[7a1082d]: https://github.com/metezd/OmniLog/commit/7a1082d
[6ccdca9]: https://github.com/metezd/OmniLog/commit/6ccdca9
[70c9f79]: https://github.com/metezd/OmniLog/commit/70c9f79
[8335c9d]: https://github.com/metezd/OmniLog/commit/8335c9d
