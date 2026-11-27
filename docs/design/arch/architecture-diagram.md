# OmniLog — System Architecture Diagram

This document defines the multi-tier containerized software architecture of **OmniLog**, aligned with `docker-compose.prod.yml`, `docker/Caddyfile`, `backend/app/`, and `frontend/src/`.

- **PlantUML Sources & Rendered Images**:
  - `01-system-architecture.puml` / `.png` / `.svg`
  - `02-backend-layers.puml` / `.png` / `.svg`
  - `03-frontend-structure.puml` / `.png` / `.svg`

```mermaid
flowchart LR
  subgraph Client["Browser Client"]
    UI["Next.js App Router UI\nsrc/app (/, /login, /register, /library, /search, /title/[id], /lists, /lists/[id], /diary, /recommendations, /stats, /friends)\nsrc/components (auth, layout, library, lists, search, social, states, title)"]
  end

  subgraph ProxyContainer["Reverse Proxy Container (caddy:2-alpine)"]
    CADDY["Caddy Reverse Proxy (docker/Caddyfile)\nPorts 80 / 443 Automatic HTTPS"]
  end

  subgraph FrontendContainer["Frontend Container (Node 26 / Next.js 16)"]
    MW["Route Guard (src/proxy.ts)\nlib/auth/routes.ts + lib/auth/token.ts"]
    ACT["Server Actions (src/lib/actions)\nauth.ts, library.ts, chapters.ts, lists.ts"]
    SRV["Server Data Layer (src/lib/server)\nauthed.ts, backend.ts, session.ts (omnilog_session httpOnly cookie)\ncatalog.ts, library.ts, journal.ts, chapters.ts, reviews.ts, recommendations.ts, stats.ts, user.ts"]
  end

  subgraph BackendContainer["Backend Container (Python 3.15 / FastAPI)"]
    API["FastAPI Routers (backend/app/api)\nauth.py (/auth), media.py (/media), catalog.py (/catalog),\nlibrary.py (/library, /library/{entry_id}/review), chapters.py (/library/{entry_id}/chapters),\njournal.py (/lists, /diary), recommendations.py (/recommendations), stats.py (/stats), deps.py"]
    SVC["Services Layer (backend/app/services)\nauth_service.py, media_service.py, catalog_service.py, library_service.py,\nchapter_service.py, journal_service.py, diary_service.py, review_service.py, stats_service.py"]
    INT["Integration Layer (backend/app/integrations)\nigdb.py, tmdb.py, common.py, genres.py"]
    CORE["Core Layer (backend/app/core)\nconfig.py, security.py (PyJWT, bcrypt), cache.py, database.py, errors.py, usernames.py"]
  end

  subgraph DataLayer["Data & Cache Layer"]
    PG[("PostgreSQL 16 (pgvector/pgvector:pg16)\nbackend/app/models/entities.py (14 models + media_item_genres)\nbackend/migrations/versions (0001..0011)")]
    RD[("Redis 7 (redis:7-alpine)\nomni:search & omni:catalog cache\n+ in-process _local fallback")]
  end

  subgraph ExternalAPIs["External Catalog Providers"]
    TMDB["TMDB API + TVMaze / Wikidata Fallback\n(TV Series & Movies)"]
    IGDB["IGDB API (Twitch OAuth) + Steam Store Fallback\n(Video Games)"]
  end

  UI --> CADDY
  CADDY --> MW
  MW --> ACT
  MW --> SRV
  ACT --> SRV
  SRV -->|"Bearer JWT over HTTP (backendFetch)"| API
  API --> SVC
  API --> CORE
  SVC --> INT
  SVC --> CORE
  SVC --> PG
  CORE --> RD
  INT --> TMDB
  INT --> IGDB
```
