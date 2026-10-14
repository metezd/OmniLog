# OmniLog - Requirement Analysis Report

**Course:** CMPE 331 Software Engineering Concepts, Fall 2026-2027
**Deliverable:** Requirement Analysis Report (deadline 18.10.2026 23:59)
**Version:** 1.0
**Repository branch:** `analysis_work`

| Team member | Role |
|---|---|
| Mete Özdoğan | Product Owner, Full-Stack Architect (domain model and E-R) |
| Kerem Kenet | Frontend Lead (UI mockups) |
| Kağan Konuk | Backend Engineer (Epic 2 and Epic 4 DFDs) |
| Sidar Ürey | ML Engineer (Epic 5) |
| Musab Alperen Başol | API Integration and Backend Engineer (Epic 3, Level 0 and 1 DFDs) |

The reviewer of the analysis PR is Yeşim.

---

## 1. Introduction

### 1.1 Purpose
This report analyzes the requirements of OmniLog. It builds on the [Requirement Specification Report](../requirements/requirements-specification.md) and the user stories. It explains the data model and the behavior of the system, and it checks that all analysis documents agree with each other.

### 1.2 Project summary
OmniLog is a web platform for media tracking and social journaling. It brings video games and TV series into one place. Users can log, rate and review single chapters of episodic games, and can compare their branching decisions. The platform also collects catalog data from IGDB and TMDB, recommends titles across media types and shows personal statistics.

## 2. Scope and boundaries

**In scope:** the six epics of the Project Charter.

| Epic | Name |
|---|---|
| 1 | Backend Infrastructure and Database Foundation |
| 2 | User Management and Social Journal |
| 3 | Multi-Media Aggregation and Cataloging (IGDB, TMDB) |
| 4 | Granular Episodic and Decision Logging |
| 5 | AI-Powered Cross-Media Engine and Review Moderation |
| 6 | Analytics Dashboard |

**Out of scope:** media streaming and client hosting, real-time in-game memory hooking, and e-commerce (digital key marketplace and payments).

## 3. Stakeholders and users

- Product Owner and course instructor
- Team members (see the table above)
- Reviewer (Yeşim)
- Visitor: a person who is not logged in
- User: a logged-in gamer or film and TV fan
- Operator: a team member who deploys, monitors and starts manual syncs

## 4. Analysis artifacts

| Artifact | File |
|---|---|
| Domain model | [data/domain-model.md](data/domain-model.md) |
| E-R diagrams and data dictionary | [data/er-diagram.md](data/er-diagram.md) |
| Traceability table, all epics | [data/traceability.md](data/traceability.md) |
| Traceability table, Epic 3 details | [data/traceability-epic3.md](data/traceability-epic3.md) |
| DFD Level 0 and Level 1 | [behavior/dfd-level0-1.md](behavior/dfd-level0-1.md) |
| DFD Epic 2 (journal) | [behavior/dfd-epic2-journal.md](behavior/dfd-epic2-journal.md) |
| DFD Epic 3 (catalog) | [behavior/dfd-epic3-catalog.md](behavior/dfd-epic3-catalog.md) |
| DFD Epic 4 (episodic) | [behavior/dfd-epic4-episodic.md](behavior/dfd-epic4-episodic.md) |
| DFD Epic 5 (AI) | [behavior/dfd-epic5-ai.md](behavior/dfd-epic5-ai.md) |
| DFD Epic 6 (analytics) | [behavior/dfd-epic6-analytics.md](behavior/dfd-epic6-analytics.md) |
| Screen list for the UI | [ui/screen-list.md](ui/screen-list.md) |
| Baseline of the implemented model | [domain-model.md](domain-model.md), [er.md](er.md) |

## 5. Functional analysis

### 5.1 Use cases

| Use case | Description | Story |
|---|---|---|
| UC-EP1-01 | The operator checks that the service is running | US-01 |
| UC-EP2-01 | A visitor registers an account | US-02 |
| UC-EP2-02 | A user logs in and gets a token | US-03 |
| UC-EP2-03 | A user adds a title to the library with a status | US-04 |
| UC-EP2-04 | A user rates a title and changes its status | US-05 |
| UC-EP2-05 | A user creates a custom list and adds titles | US-06 |
| UC-EP2-06 | A user views the activity diary | US-07 |
| UC-EP3-01 | A user asks for a title by id. On a cache hit, it is served from the cache | US-09 |
| UC-EP3-02 | On a cache miss or a stale record, the database is checked, and then the outside API is called | US-09 |
| UC-EP3-03 | The operator starts a manual sync | US-08, US-09 |
| UC-EP3-04 | The outside API is rate limited. Backoff and retry are used | NFR-04 |
| UC-EP3-05 | A user searches the catalog by title and type | US-08 |
| UC-EP3-06 | A user opens title details with seasons or chapters | US-09 |
| UC-EP4-01 | A user rates a chapter from 1 to 5 | US-10 |
| UC-EP4-02 | A user logs playtime for a chapter | US-11 |
| UC-EP4-03 | A user records a branching decision | US-12 |
| UC-EP5-01 | The system makes an embedding for a new or changed title | US-13 |
| UC-EP5-02 | A user asks for recommendations of another media type | US-13 |
| UC-EP5-03 | A user writes a review and the system flags spoilers | US-14 |
| UC-EP6-01 | A user views personal statistics | US-15 |

### 5.2 Epic 3 detailed requirements

| ID | Requirement |
|---|---|
| R-EP3-01 | The API must provide `GET /catalog/{source}/{external_id}` to get a title by its outside id. |
| R-EP3-02 | Redis is checked first. The cache key pattern is `omni:catalog:{source}:{external_id}`. |
| R-EP3-03 | On a cache miss, the persistent database is checked. An outside call is made when needed. |
| R-EP3-04 | API keys for outside calls are stored safely (secret manager or environment variables). |
| R-EP3-05 | A scheduled sync job runs regularly and is logged. |
| R-EP3-06 | On rate limits and 429 answers, exponential backoff is used. The maximum is 3 retries. |
| R-EP3-07 | The API must provide `GET /catalog/search` with a text and a type. |
| R-EP3-08 | `GET /catalog/{id}` returns seasons and episodes, or chapters. |
| R-EP3-09 | When an outside service fails, the API returns cached data or 503, never an unhandled 500. |

The traceability of these requirements is in [data/traceability-epic3.md](data/traceability-epic3.md).

## 6. Non-functional analysis

### 6.1 Requirements from the specification

| ID | Requirement | Analysis result |
|---|---|---|
| NFR-01 | p95 response time of cached searches is under 500 ms | Search results are cached in Redis with the key `omni:search:{type}:{query_hash}` |
| NFR-02 | Protected endpoints need a token | Checked in process 1.0 for every protected path |
| NFR-03 | Passwords are never stored or returned in plain text | Hash only. The response schema has no password field |
| NFR-04 | The API survives outside failures | Process 3.7 and the fallback to cache or 503 |
| NFR-05 | At least 70% test coverage | Measured in the Testing phase |

### 6.2 Additional analysis targets

These targets are stricter or more detailed than the specification. They were called NFR-1 to NFR-4 in the first draft. They are renamed here so that they do not clash with NFR-01 to NFR-05.

| ID | Target |
|---|---|
| AN-1 | Read time for a cache hit on one title is under 50 ms. |
| AN-2 | The cache TTL is configurable. The default for tests is 1 hour. |
| AN-3 | Sync jobs are observable: duration, success and failure rate, and error logs. |
| AN-4 | The cache layer has a failover plan (optional: Redis Sentinel or Cluster). |

## 7. Data analysis summary

The full model is in [data/domain-model.md](data/domain-model.md) and [data/er-diagram.md](data/er-diagram.md).

- The model has 19 entities in 4 areas: journal, catalog, episodic logging and AI.
- Three tables exist in the code already (`users`, `media_items`, `user_libraries`). The others are proposed.
- The catalog is shared. All personal data is stored in other tables.
- Statistics need no tables. They are computed from the other tables.
- The vector table `media_embeddings` was added for Epic 5. All media types share one vector space. See section 8 of [data/er-diagram.md](data/er-diagram.md).

## 8. Behavior analysis summary

The system is split into six Level 1 processes (1.0 to 6.0). Each has a Level 2 diagram. The processes, the data stores and the flows are in [behavior/dfd-level0-1.md](behavior/dfd-level0-1.md).

| Process | Main idea |
|---|---|
| 1.0 | One gateway checks the token for all protected paths |
| 2.0 | Every user action creates a diary event through process 2.5 |
| 3.0 | Cache first, then database, then outside API. Outside failures are handled with retry and fallback |
| 4.0 | Every chapter action first checks that the user owns the library entry and the chapter belongs to the title |
| 5.0 | Embeddings are made when the catalog changes. Recommendations use cosine similarity. Spoilers are detected when a review is saved |
| 6.0 | Statistics are computed on request and cached. The cache is deleted when data changes |

## 9. Consistency check

All analysis documents were compared with each other, with the user stories, with the tests and with the code. The table shows what was found and what was done.

| # | Finding | Action |
|---|---|---|
| F-01 | The domain model and the E-R diagram only covered the API integration entities. | Rewritten for all six epics. |
| F-02 | There was no data dictionary. | Added to `data/er-diagram.md`. |
| F-03 | There were no DFDs for Epic 2, 4, 5 and 6. | Added. |
| F-04 | The Level 0 and 1 DFD only covered the integration layer. | Rewritten for the whole system. |
| F-05 | The traceability table covered Epic 3 only. | A table for all epics was added. The Epic 3 table was kept and extended. |
| F-06 | The Epic 3 DFD had no search flow (US-08) and no title details flow (US-09). | Added. |
| F-07 | The draft domain model used a UUID as the media id. The code and tests use an integer. | Integer kept. |
| F-08 | The code has `external_api_id` (integer). The catalog needs a source and a text id. | `source_id` and `external_id` proposed. The code needs a migration. |
| F-09 | The earlier E-R linked `sync_job_log` to media. A sync job works on a source. | Linked to `external_sources`. |
| F-10 | The Epic 3 requirement used the path `/api/catalog/...`. The tests use `/catalog/...`. | No `/api` prefix. |
| F-11 | The first report used NFR-1 to NFR-4. They clash with NFR-01 to NFR-05 (for example 50 ms and 500 ms). | Renamed to AN-1 to AN-4. |
| F-12 | The earlier E-R had no table for embeddings. | `media_embeddings` and `user_taste_vectors` added. |
| F-13 | The baseline documents and the code comment say RAWG. The Charter says IGDB. | The baseline document was changed to IGDB. The comment in `entities.py` still says RAWG. |
| F-14 | The user model had no admin role, but the Operator starts manual syncs. | `is_admin` proposed. |
| F-15 | The Charter lists user profiles in Epic 2, but there is no user story. | A profile screen is listed as optional. A story could be added. |
| F-16 | Nothing creates chapters, decision points and options for episodic games. | Open point (see section 10). |
| F-17 | Documents in `docs/analysis` were partly in Turkish. | All translated to English. |

## 10. Open issues and decisions needed

| # | Issue | Suggested owner |
|---|---|---|
| 1 | Database: PostgreSQL (Charter, JSONB, pgvector) or SQLite (code now). Decide in the design phase. | Product Owner |
| 2 | Rating scales: 1 to 10 for the library and 1 to 5 for chapters. One scale should be confirmed. | Product Owner |
| 3 | Source of chapters, decision points and options for episodic games. IGDB has no standard chapter list. | Product Owner, API Integration |
| 4 | Embedding model and its dimension. The vector column needs a fixed size. | ML Engineer |
| 5 | Is collaborative filtering part of version 1? This report assumes content-based only. | ML Engineer |
| 6 | Spoiler model and threshold. | ML Engineer |
| 7 | One or many decision points for each chapter in the API. | Backend |
| 8 | Add a user story for user profiles, or remove profiles from the Epic 2 scope. | Product Owner |

## 11. Risks and assumptions

**Assumptions**
1. The IGDB and TMDB keys are shared safely inside the team.
2. The API paths in the tests are the team's contract (see the requirement specification).
3. Statistics use only the data of the logged-in user.

**Risks**
- Outside rate limits can slow down the sync jobs.
- Normalization rules differ between sources. This can make fields unclear. The Product Owner and the API Integration engineer must agree on them.
- Epic 5 has the highest technical uncertainty and the lowest priority. It is the first candidate for scope reduction.
- Chapter data for games is not available from the sources (finding F-16).
- The schedule has almost no buffer (see the PERT analysis).

## 12. Traceability

The full table is in [data/traceability.md](data/traceability.md). The Epic 3 details are in [data/traceability-epic3.md](data/traceability-epic3.md).

## 13. Next steps

1. Review of this PR by the reviewer.
2. Decisions on the open issues in section 10.
3. UI mockups in Figma, based on [ui/screen-list.md](ui/screen-list.md).
4. Start of the Software Design Report (deadline 15.11.2026).
