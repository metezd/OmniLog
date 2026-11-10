# OmniLog — Runtime Sequence Diagrams

This document defines the runtime interaction sequence diagrams for **OmniLog** across catalog search & caching, granular episodic logging & branching decision recording, and AI cross-media recommendation & NLP spoiler moderation.

## 1. Catalog Search with Read-Through Redis Cache (`US-08`, `US-09`, `NFR-01`)

```mermaid
sequenceDiagram
  actor User
  participant Next as Next.js (/search)
  participant API as FastAPI (/catalog/search)
  participant Cache as Redis 7
  participant Ext as External Catalog API (TMDB / IGDB)
  participant DB as PostgreSQL 16

  User->>Next: Search title (q, type)
  Next->>API: GET /catalog/search?q=...&type=...
  API->>Cache: GET omni:search:{type}:{hash}
  alt Cache Hit
    Cache-->>API: Cached ExternalTitle list
  else Cache Miss
    Cache-->>API: None
    API->>Ext: Fetch titles by query
    Ext-->>API: Normalized ExternalTitle list
    API->>Cache: SETEX omni:search:{type}:{hash} (TTL 3600s)
  end
  API->>DB: Upsert MediaItem rows
  DB-->>API: Persisted MediaItem entities with IDs
  API-->>Next: 200 OK List[MediaItemResponse]
  Next-->>User: Render SearchResultCard grid
```

## 2. Granular Episodic Logging & Branching Decision Recording (`US-10`, `US-11`, `US-12`)

```mermaid
sequenceDiagram
  actor User
  participant Next as Next.js (/title/[id])
  participant API as FastAPI (/library/{id}/chapters/{cid})
  participant DB as PostgreSQL 16

  User->>Next: Select Choice "A" / Rate 5★ / Log 45m
  Next->>API: PUT /decision (or /rating, POST /playtime)
  API->>DB: Verify ownership of UserLibrary & Chapter existence
  API->>DB: Upsert ChapterProgress & UserDecision / PlaytimeLog
  API->>DB: Insert ActivityEvent (DECISION_RECORDED / CHAPTER_RATED / PLAYTIME_LOGGED)
  DB-->>API: Commit Transaction
  API-->>Next: 200 OK / 201 Created
  Next-->>User: Revalidate /title/[id], /diary, /stats
```

## 3. Review Submission with Automated NLP Spoiler Moderation (`US-14`)

```mermaid
sequenceDiagram
  actor User
  participant Next as Next.js (ReviewSection)
  participant API as FastAPI (POST /library/{id}/review)
  participant NLP as ReviewService (Spoiler Classifier)
  participant DB as PostgreSQL 16

  User->>Next: Submit review text
  Next->>API: POST /library/{entry_id}/review { text }
  API->>NLP: detect_spoilers(text)
  NLP-->>API: (contains_spoiler, spoiler_score, model_version)
  API->>DB: Upsert Review + Insert ActivityEvent(REVIEW_POSTED)
  DB-->>API: Persisted Review entity
  API-->>Next: 201 Created ReviewResponse
  Next-->>User: Render Spoiler Warning Badge & Blur Toggle
```
