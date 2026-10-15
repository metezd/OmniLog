# Traceability Table: Epic 3 (IGDB and TMDB)

This table links the Epic 3 requirements (UC-EP3) to the DFD elements, the data entities and the files. It checks that the requirements, the DFDs and the data models agree with each other. The table for all epics is in [traceability.md](traceability.md).

| Req ID | Requirement (short) | Use case | DFD process or element | Data entity or table | API endpoint or key | Reference files | Status |
|---|---|---|---|---|---|---|---|
| R-EP3-01 | Get a title by id | UC-EP3-01 | 3.1 Serve Catalog Request | `media_items` | `GET /catalog/{source}/{external_id}` | behavior/dfd-level0-1.md, behavior/dfd-epic3-catalog.md | draft |
| R-EP3-02 | Check the cache before the database | UC-EP3-01 | 3.1 and D9 Redis Cache | Redis key `omni:catalog:...` | Key pattern `omni:catalog:{source}:{external_id}` | behavior/dfd-epic3-catalog.md | draft |
| R-EP3-03 | Fetch from outside when missing or stale | UC-EP3-02 | 3.3 Fetch From External, 3.4 Normalize and Transform, 3.5 Persist and Cache | `media_items` | - | behavior/dfd-epic3-catalog.md, data/domain-model.md | draft |
| R-EP3-04 | Store API keys safely | UC-EP3-02 | Secret Manager into 3.3 | `external_sources` (no secrets in the table) | - | requirement-analysis-report.md | draft |
| R-EP3-05 | Scheduled bulk sync | UC-EP3-03 | 3.6 Run Sync | `sync_job_logs` | `POST /admin/sync` (manual) | behavior/dfd-epic3-catalog.md | draft |
| R-EP3-06 | Rate limit handling | UC-EP3-04 | 3.7 Handle Errors and Retry | `sync_job_logs` | - | behavior/dfd-epic3-catalog.md | draft |
| R-EP3-07 | Search the catalog by text and type | UC-EP3-05 | 3.2 Search Catalog | `media_items` | `GET /catalog/search`, key `omni:search:{type}:{query_hash}` | behavior/dfd-epic3-catalog.md | draft |
| R-EP3-08 | Title details with seasons and chapters | UC-EP3-06 | 3.1 Serve Catalog Request | `media_items`, `seasons`, `chapters` | `GET /catalog/{id}` | behavior/dfd-epic3-catalog.md, data/er-diagram.md | draft |
| R-EP3-09 | Survive outside failures with cached data or 503 | UC-EP3-04 | 3.7 Handle Errors and Retry | - | All catalog endpoints | behavior/dfd-epic3-catalog.md | draft |

Guide: update the "Status" column in the PR process with the reviewer (draft, reviewed, accepted).

Rows R-EP3-07 to R-EP3-09 are new. They come from US-08, US-09 and NFR-04, which were missing in the first version of this table.

Add a row to this table for every new or changed requirement in each PR.
