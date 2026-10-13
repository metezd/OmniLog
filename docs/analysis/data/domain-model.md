# Domain Model — OmniLog (Öneri)

Bu belge, API entegrasyonları için gerekli temel domain varlıklarını özetler. Nihai E-R ve alan adları Mete tarafından onaylanacaktır. Dosya: docs/analysis/data/domain-model.md

## Özet Varlıklar
- ExternalSource
  - id (PK)
  - name (IGDB/TMDB)
  - base_url
  - auth_meta (JSON) — token tipi/ekstra meta
  - rate_limit_meta (JSON) — rate-limit bilgisi

- Media
  - id (PK, internal UUID)
  - external_id (string)
  - source_id (FK -> ExternalSource)
  - title
  - type (movie/series/game)
  - genres (array)
  - normalized_payload (JSONB) — canonical fields
  - last_synced (timestamp)
  - created_at, updated_at

- CacheEntry (opsiyonel; Redis’de tutulur)
  - key
  - media_id (FK)
  - ttl_seconds
  - created_at
  - hits (optional)

- SyncJobLog
  - id
  - job_name
  - started_at
  - finished_at
  - status (success/fail)
  - error_text (nullable)

## Normalizasyon Notları
- Farklı kaynaklarda tür alanları farklı olabilir (örn. "game" vs "video_game"). Normalize işlemi canonical bir `type` alanı üretmeli.
- Tarih, resim URL'leri, genre isimleri normalize edilecek.

## Önerilen Index'ler
- media(source_id, external_id) unique index
- media(last_synced) for stale checks

Not: Bu tablo NoSQL veya relationel veritabanı ile uygulanabilir; JSONB alanı PostgreSQL'de işe yarar.