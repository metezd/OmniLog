# OmniLog — Runtime Sequence Diagrams

This document summarizes the runtime interaction sequence diagrams for **OmniLog**. Full PlantUML models (`.puml`) and rendered `.png`/`.svg` images for 10 user stories (US-02, US-03, US-04, US-08, US-09, US-10, US-11, US-12, US-14, US-15 — 67% of the 15 user stories) are in this folder:

- `01-us02-register.puml` / `.png` / `.svg`
- `02-us03-login.puml` / `.png` / `.svg`
- `03-us04-add-to-library.puml` / `.png` / `.svg`
- `04-us08-catalog-search.puml` / `.png` / `.svg`
- `05-us09-title-details.puml` / `.png` / `.svg`
- `06-us10-rate-chapter.puml` / `.png` / `.svg`
- `07-us11-log-playtime.puml` / `.png` / `.svg`
- `08-us12-record-decision.puml` / `.png` / `.svg`
- `09-us15-stats.puml` / `.png` / `.svg`
- `10-us14-review.puml` / `.png` / `.svg`

## 1. Catalog Search with Read-Through Redis Cache (`US-08`, `NFR-01`, `NFR-04`)

```mermaid
sequenceDiagram
  actor User
  participant Next as Next.js (src/lib/server/catalog.ts)
  participant API as FastAPI (app/api/catalog.py: GET /catalog/search)
  participant SVC as CatalogService (app/services/catalog_service.py)
  participant Cache as Cache (app/core/cache.py: Redis / _local)
  participant Ext as IgdbClient / TmdbClient (app/integrations/)
  participant DB as PostgreSQL 16 (media_items)

  User->>Next: searchCatalog(query, type)
  Next->>API: GET /catalog/search?q=...&type=... (Bearer token)
  API->>SVC: search_catalog(db, media_type, q)
  SVC->>Cache: get_json("omni:search:{type}:{sha256[:32]}")
  alt Cache Hit
    Cache-->>SVC: Cached ExternalTitle list
  else Cache Miss
    Cache-->>SVC: None
    SVC->>Ext: search_games(query, 10) / search(media_type, query, 10)
    alt ExternalServiceError
      Ext-->>SVC: ExternalServiceError
      SVC->>DB: _search_saved(db, media_type, query)
      alt Saved rows exist
        DB-->>SVC: Saved MediaItem list
      else Empty
        SVC-->>API: CatalogUnavailableError (503 + Retry-After: 30)
      end
    else Upstream 200 OK
      Ext-->>SVC: ExternalTitle list
      SVC->>Cache: set_json(key, titles, CACHE_TTL_SECONDS=3600)
    end
  end
  SVC->>DB: _save(db, media_type, titles)
  DB-->>SVC: MediaItem rows with IDs
  SVC-->>API: list[MediaItem]
  API-->>Next: 200 OK list[MediaItemResponse]
  Next-->>User: Render SearchResultCard grid
```

## 2. Granular Episodic Logging & Branching Decision Recording (`US-10`, `US-11`, `US-12`)

```mermaid
sequenceDiagram
  actor User
  participant Next as Next.js (src/lib/actions/chapters.ts)
  participant API as FastAPI (app/api/chapters.py: /library/{entry_id}/chapters/{chapter_id})
  participant SVC as ChapterService (app/services/chapter_service.py)
  participant DIA as DiaryService (app/services/diary_service.py)
  participant DB as PostgreSQL 16

  User->>Next: Rate 1..5 / Log minutes / Choose option label
  Next->>API: PUT /rating | POST /playtime | PUT /decision
  API->>SVC: rate_chapter / log_playtime / record_decision
  SVC->>DB: get_chapter_context(db, user, entry_id, chapter_id)
  SVC->>DB: Upsert ChapterProgress / PlaytimeLog / UserDecision
  SVC->>DIA: record_event(CHAPTER_RATED / PLAYTIME_LOGGED / DECISION_RECORDED)
  SVC->>DB: Commit transaction (state change + DiaryEntry)
  API-->>Next: 200 OK / 201 Created
  Next-->>User: revalidatePath(/diary, /stats, /title/{id})
```

## 3. Review Submission with Automated NLP Spoiler Moderation (`US-14`)

```mermaid
sequenceDiagram
  actor User
  participant Next as Next.js (src/lib/actions/library.ts: submitReviewAction)
  participant API as FastAPI (app/api/library.py: POST /library/{entry_id}/review)
  participant SVC as ReviewService (app/services/review_service.py)
  participant DIA as DiaryService (app/services/diary_service.py)
  participant DB as PostgreSQL 16

  User->>Next: Submit review text
  Next->>API: POST /library/{entry_id}/review { text }
  API->>SVC: upsert_review(db, current_user, entry_id, payload)
  SVC->>SVC: detect_spoilers(payload.text) -> (contains_spoiler, spoiler_score, "omnilog-nlp-spoiler-v1")
  SVC->>DB: Upsert Review (reviews table)
  SVC->>DIA: record_event(DiaryAction.REVIEW_POSTED)
  SVC->>DB: Commit transaction
  API-->>Next: 201 Created ReviewResponse
  Next-->>User: Render Spoiler Warning Badge & Blur Toggle (ReviewSection.tsx)
```
