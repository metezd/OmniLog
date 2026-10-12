# OmniLog - Requirement Specification Report

**Course:** CMPE 331 Software Engineering Concepts, Fall 2026-2027
**Deliverable:** Requirements Definition Report (deadline 11.10.2026 23:59)
**Version:** 1.0
**Repository branch:** `requirements_work`

| Team member | Role |
|---|---|
| Mete Özdoğan | Product Owner, Full-Stack Architect |
| Kerem Kenet | Frontend Lead |
| Kağan Konuk | Backend Engineer |
| Sidar Ürey | ML Engineer |
| Musab Alperen Başol | API Integration and Backend Engineer |

---

## 1. Introduction

### 1.1 Purpose
This report specifies the requirements of **OmniLog**, a web platform for media tracking and social journaling that brings video games and TV series into one place. It collects the artifacts of the requirements phase: the project plan, the requirement definitions (user stories), the tests written for them, and their current results.

### 1.2 Background
Dedicated cataloguing platforms exist for films, TV series and video games, but consumption is cross-media. Episodic narrative games (for example Telltale titles, Life is Strange, Detroit: Become Human) are recorded as a single release in existing game databases, so players cannot log, rate and review individual chapters or compare branching decisions next to TV episodes. OmniLog closes this gap. The full motivation is in the Project Charter.

### 1.3 Scope
The scope follows the six epics of the Project Charter:

| Epic | Name |
|---|---|
| 1 | Backend Infrastructure and Database Foundation |
| 2 | User Management and Social Journal |
| 3 | Multi-Media Aggregation and Cataloging (IGDB, TMDB) |
| 4 | Granular Episodic and Decision Logging |
| 5 | AI-Powered Cross-Media Engine and Review Moderation |
| 6 | Analytics Dashboard |

**Out of scope:** media streaming or client hosting, real-time in-game memory hooking, and e-commerce (digital key marketplace, payments).

### 1.4 Stakeholders and users
- **Visitor:** a person who is not logged in and can register or log in.
- **User:** a logged-in gamer or film/TV enthusiast who tracks media.
- **Developer/Operator:** a team member who deploys and monitors the system.

### 1.5 Technology stack (from the charter)
Backend: FastAPI, Python, PostgreSQL, SQLAlchemy, Pydantic, Redis, Docker, python-jose. Frontend: Next.js, React, TypeScript, Tailwind CSS, Recharts. AI: LangChain with OpenAI API, Hugging Face models, a vector database (pgvector or Pinecone).

---

## 2. Project Plan

The plan documents are aligned with the milestones in the Project Charter and are written in Mermaid.

| Document | Content | File |
|---|---|---|
| WBS | Work breakdown into 8 phases and the six epics | [docs/plan/wbs.md](../plan/wbs.md) |
| PERT | Network diagram, expected durations, critical path, schedule risk | [docs/plan/pert.md](../plan/pert.md) |
| Gantt | Schedule of all work packages and milestones | [docs/plan/gantt.md](../plan/gantt.md) |

**Milestones**

| Deliverable | Deadline |
|---|---|
| Project Charter | 02.10.2026 23:59 |
| Requirements Definition Report | 11.10.2026 23:59 |
| Requirement Analysis Report | 18.10.2026 23:59 |
| Software Design Report | 15.11.2026 23:59 |
| Software Testing Report | 22.11.2026 23:59 |
| Codebase | 30.11.2026 23:59 |
| Presentation | TBA |

**Key PERT results:** the critical path is Backend foundation, Media aggregation, Episodic and decision logging, Analytics dashboard, Testing and QA, Stabilization (C, E, F, I, K, L). Its expected length is 57.8 days against a 58-day window, which gives about a 53% chance of finishing on 30.11.2026. The schedule has almost no buffer, so the plan keeps the first version of the external API integration small and freezes scope after Epic 4. Details are in [pert.md](../plan/pert.md).

---

## 3. Requirement Definitions

The requirements are written as **user stories** with Given / When / Then acceptance criteria. The complete text is in [docs/requirements/user-stories.md](user-stories.md).

### 3.1 Overview

| ID | Story (short) | Epic | Priority |
|---|---|---|---|
| US-01 | Service health check | 1 | Must |
| US-02 | Register an account | 2 | Must |
| US-03 | Log in | 2 | Must |
| US-04 | Add a title to my library with a status | 2 | Must |
| US-05 | Rate a title and update its status | 2 | Must |
| US-06 | Create custom lists | 2 | Should |
| US-07 | View my activity diary | 2 | Should |
| US-08 | Search the catalog | 3 | Must |
| US-09 | View title details with seasons and chapters | 3 | Must |
| US-10 | Rate an individual chapter or episode | 4 | Must |
| US-11 | Log playtime per chapter | 4 | Should |
| US-12 | Record branching decisions | 4 | Should |
| US-13 | Cross-media recommendations | 5 | Should |
| US-14 | Spoiler detection in reviews | 5 | Could |
| US-15 | View personal statistics | 6 | Should |

Priority summary (MoSCoW): 8 Must, 6 Should, 1 Could.

### 3.2 Non-functional requirements

| ID | Category | Requirement | Measurable criterion |
|---|---|---|---|
| NFR-01 | Performance | Cached catalog searches are fast. | p95 response time under 500 ms over 100 repeated requests |
| NFR-02 | Security | Protected endpoints require authentication. | `/library`, `/lists`, `/diary`, `/stats` return 401 without a valid token |
| NFR-03 | Security | Passwords are never stored or returned in plain text. | Stored value differs from the plain text, and no response contains a password or hash |
| NFR-04 | Reliability | The API survives external API failures. | When IGDB/TMDB is unavailable, catalog endpoints return cached data or 503, never an unhandled 500 |
| NFR-05 | Maintainability | Backend code is covered by automated tests. | At least 70% line coverage with `pytest-cov` (measured in the Testing phase) |

---

## 4. Test Specification

Tests follow a test-first approach: each user story has at least one functional test, and the non-functional requirements have their own test cases. The tests are written with **pytest** and FastAPI's `TestClient` and are stored in [`tests/requirements/`](../../tests/requirements/).

| File | Covers |
|---|---|
| `test_epic1_infrastructure.py` | US-01 |
| `test_epic2_users.py` | US-02 to US-07 |
| `test_epic3_catalog.py` | US-08, US-09 |
| `test_epic4_episodic.py` | US-10 to US-12 |
| `test_epic5_ai.py` | US-13, US-14 |
| `test_epic6_analytics.py` | US-15 |
| `test_nfr.py` | NFR-01 to NFR-04 |
| `conftest.py`, `helpers.py` | Shared fixtures and API helper functions |

**How to run** (from the repository root, with the virtual environment active):

```bash
python -m pip install -r tests/requirements-test.txt
python -m pytest tests/requirements -v --tb=short
```

---

## 5. Test Results and Implementation Status

Result of the test run on 10.10.2026: **41 tests collected, 1 passed, 11 failed, 29 errors.**

- **Passed:** the health endpoint, which already exists in `backend/app/main.py`.
- **Failed:** the assertion did not hold. For these tests the endpoint exists in the test but not in the backend, so the API answers 404 instead of the expected status (201, 401, 422).
- **Error:** the test could not start because its setup step (registering a user through `/auth/register`) failed with 404. These tests will also run their assertions once authentication exists.

All three outcomes mean "requirement not met yet", which is the intended state of a test-first requirements phase.

| Story / NFR | Tests | Passed | Failed | Error | Status |
|---|---|---|---|---|---|
| US-01 | 1 | 1 | 0 | 0 | Implemented |
| US-02 | 3 | 0 | 3 | 0 | Not implemented |
| US-03 | 2 | 0 | 2 | 0 | Not implemented |
| US-04 | 3 | 0 | 1 | 2 | Not implemented |
| US-05 | 3 | 0 | 0 | 3 | Not implemented |
| US-06 | 3 | 0 | 0 | 3 | Not implemented |
| US-07 | 2 | 0 | 0 | 2 | Not implemented |
| US-08 | 2 | 0 | 0 | 2 | Not implemented |
| US-09 | 2 | 0 | 0 | 2 | Not implemented |
| US-10 | 2 | 0 | 0 | 2 | Not implemented |
| US-11 | 2 | 0 | 0 | 2 | Not implemented |
| US-12 | 3 | 0 | 0 | 3 | Not implemented |
| US-13 | 2 | 0 | 0 | 2 | Not implemented |
| US-14 | 2 | 0 | 0 | 2 | Not implemented |
| US-15 | 2 | 0 | 0 | 2 | Not implemented |
| NFR-01 | 1 | 0 | 0 | 1 | Not implemented |
| NFR-02 | 4 | 0 | 4 | 0 | Not implemented |
| NFR-03 | 1 | 0 | 1 | 0 | Not implemented |
| NFR-04 | 1 | 0 | 0 | 1 | Not implemented |
| **Total** | **41** | **1** | **11** | **29** | |

**What already exists in the codebase**
- Database layer and models: `User`, `MediaItem`, `UserLibrary` with the `MediaType` and `WatchStatus` enums (`backend/app/core/database.py`, `backend/app/models/entities.py`).
- Pydantic v2 request/response schemas for users, media items and library entries (`backend/app/schemas/`).
- `GET /` and `GET /health` endpoints.

No authentication, library, catalog, episodic, AI or analytics endpoints exist yet.

---

## 6. Traceability

| Epic | Stories | Tests | Plan activity (PERT/Gantt) |
|---|---|---|---|
| 1 | US-01 | `test_epic1_infrastructure.py` | C |
| 2 | US-02 to US-07 | `test_epic2_users.py`, `test_nfr.py` | C |
| 3 | US-08, US-09 | `test_epic3_catalog.py` | E |
| 4 | US-10 to US-12 | `test_epic4_episodic.py` | F |
| 5 | US-13, US-14 | `test_epic5_ai.py` | H |
| 6 | US-15 | `test_epic6_analytics.py` | I |
| All | NFR-01 to NFR-05 | `test_nfr.py`, coverage run | K |

---

## 7. Assumptions, Risks and Open Issues

**Assumptions**
1. The API paths and payloads in the tests (for example `POST /auth/register`, `POST /auth/login` with a JSON body, `POST /library`, `GET /catalog/search`) are the team's proposed contract. If the implemented API differs, both the stories and the tests will be updated.
2. A helper endpoint `POST /media` creates catalog entries during test setup.

**Open issues**
1. **Database:** the Project Charter specifies PostgreSQL, while the current implementation uses SQLite (`omnilog.db`). The migration will be decided in the design phase.
2. **Rating scale:** the charter mentions star ratings, while the current data model limits library ratings to 1-10. The stories use 1-10 for library entries and 1-5 for chapters. The team will confirm one scale in the analysis phase.
3. **Test isolation:** the tests currently run against the configured application database and use unique user names to avoid collisions. A dedicated test database will be introduced in the testing phase.
4. **Existing health check:** `/health` does not check the database connection yet, so the "database unreachable" criterion was removed from US-01.
5. **External services:** US-08, US-09 and NFR-01 depend on IGDB and TMDB access (API keys, rate limits).

**Risks**
- The schedule has almost no buffer (see section 2). Mitigations are listed in [pert.md](../plan/pert.md).
- Epic 5 (AI) has the highest technical uncertainty and the lowest priority stories (Should/Could), so it is the first candidate for scope reduction.

---

## 8. Artifact Index

| Artifact | Location |
|---|---|
| Project plan | [docs/plan/](../plan/) |
| User stories and NFRs | [docs/requirements/user-stories.md](user-stories.md) |
| Functional and non-functional tests | [tests/requirements/](../../tests/requirements/) |
| Pydantic schemas (existing code) | [backend/app/schemas/](../../backend/app/schemas/) |
| Data models (existing code) | [backend/app/models/entities.py](../../backend/app/models/entities.py) |
