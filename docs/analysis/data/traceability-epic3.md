# Traceability Table: Epic 3 (IGDB and TMDB)

This table links the Epic 3 requirements (UC-EP3) to the DFD elements, the data entities and the files. It checks that the requirements, the DFDs and the data models agree with each other. The table for all epics is in [traceability.md](traceability.md).

| Req ID | Requirement (short) | Use case | DFD process or element | Data entity or table | API endpoint or key | Reference files | Status |
|---|---|---|---|---|---|---|---|
| R-EP3-01 | Get a title by id | UC-EP3-01 | 3.1 Serve Catalog Request | `media_items` | `GET /catalog/{id}`. The lookup `GET /catalog/{source}/{external_id}` is not built | behavior/dfd-level0-1.md, behavior/dfd-epic3-catalog.md | Partly implemented |
| R-EP3-02 | Check the cache first | UC-EP3-01 | 3.1 and D9 Redis Cache | Redis key `omni:catalog:...` | Key pattern `omni:catalog:{source}:{external_id}` | behavior/dfd-epic3-catalog.md | Implemented. The cache is checked before the outside call. D5 is not read first |
| R-EP3-03 | Fetch from outside when missing | UC-EP3-02 | 3.3 Fetch From External, 3.4 Normalize and Transform, 3.5 Persist and Cache | `media_items` | - | behavior/dfd-epic3-catalog.md, data/domain-model.md | Implemented. A stale check by `last_synced` is not built, the cache decides |
| R-EP3-04 | Store API keys safely | UC-EP3-02 | Environment variables into 3.3 | None. The keys are never stored in a table | - | requirement-analysis-report.md | Implemented with environment variables. `external_sources` and a Secret Manager are not built |
| R-EP3-05 | Scheduled bulk sync | UC-EP3-03 | 3.6 Run Sync | `sync_job_logs` | `POST /admin/sync` (manual) | behavior/dfd-epic3-catalog.md | Not implemented |
| R-EP3-06 | Rate limit handling | UC-EP3-04 | 3.7 Handle Errors and Retry | - | - | behavior/dfd-epic3-catalog.md | Implemented (retries with backoff, `Retry-After`). The failure goes to the log, not to `sync_job_logs` |
| R-EP3-07 | Search the catalog by text and type | UC-EP3-05 | 3.2 Search Catalog | `media_items` | `GET /catalog/search`, key `omni:search:{type}:{query_hash}` | behavior/dfd-epic3-catalog.md | Implemented |
| R-EP3-08 | Title details with seasons and chapters | UC-EP3-06 | 3.1 Serve Catalog Request | `media_items`, `seasons`, `chapters` | `GET /catalog/{id}` | behavior/dfd-epic3-catalog.md, data/er-diagram.md | Implemented |
| R-EP3-09 | Survive outside failures with saved data or 503 | UC-EP3-04 | 3.7 Handle Errors and Retry | - | All catalog endpoints | behavior/dfd-epic3-catalog.md | Implemented |

The tests of these requirements are listed in [traceability.md](traceability.md), section 2 (US-08, US-09, NFR-01 and NFR-04).

The "Status" column shows the implementation state, checked against the code on 19.11.2026. The analysis review state (draft, reviewed, accepted) is in [traceability.md](traceability.md).

Rows R-EP3-07 to R-EP3-09 are new. They come from US-08, US-09 and NFR-04, which were missing in the first version of this table. A keyless demo mode (Steam Store, TVMaze and iTunes) also exists in the code and has no requirement of its own.

Add a row to this table for every new or changed requirement in each PR.
