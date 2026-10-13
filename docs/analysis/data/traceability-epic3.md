# Traceability / Tutarlılık Tablosu — Epic 3 (IGDB/TMDB)

Bu tablo Epic 3 gereksinimlerini (UC-EP3) DFD elemanlarına, veri varlıklarına ve ilgili dosyalara bağlar. Dosya: docs/analysis/data/traceability-epic3.md

| Req ID | Requirement (Kısa) | Use Case | DFD Process / Element | Data Entity / Table | API Endpoint / Key | Referans Dosya | Durum |
|---|---|---|---|---|---|---|---|
| R-EP3-01 | GET media by id | UC-EP3-01 | ServeAPI (API Gateway) | - | GET /api/catalog/:source/:id | behavior/dfd-level0-1.md, behavior/dfd-epic3-catalog.md | draft |
| R-EP3-02 | Cache check before DB | UC-EP3-01 | CacheRead (RedisCache) | CacheEntry (Redis key omni:catalog:...) | Redis key pattern omni:catalog:{source}:{external_id} | behavior/dfd-epic3-catalog.md | draft |
| R-EP3-03 | Fetch from external when missing/stale | UC-EP3-02 | FetchFromExternal, NormalizeTransform | media (PersistentDB) | - | behavior/dfd-epic3-catalog.md, data/domain-model.md | draft |
| R-EP3-04 | Store API keys securely | UC-EP3-02 | Auth Provider / SecretManager | external_source | - | requirement-analysis-report.md | draft |
| R-EP3-05 | Scheduled bulk sync | UC-EP3-03 | ScheduledSync | sync_job_log | - | behavior/dfd-epic3-catalog.md | draft |
| R-EP3-06 | Rate-limit handling | UC-EP3-04 | ErrorHandling / Retry | sync_job_log | - | behavior/dfd-epic3-catalog.md | draft |


Kılavuz: "Durum" sütununu PR sürecinde reviewer ile güncelleyin (draft -> reviewed -> accepted).

---

Bu tablo, gereksinimlerin DFD ve veri modelleri ile tutarlı olmasını kontrol etmeye yarar. Her PR'de yeni/updated gereksinimler için bu tabloya satır ekleyin.