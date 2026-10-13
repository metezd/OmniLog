# DFD — Epic 3: IGDB / TMDB Catalog Integration

Bu belge Epic 3 (IGDB/TMDB entegrasyonu) için DFD (Data Flow Diagram) açıklaması ve görsel taslağını içerir. Dosya: docs/analysis/behavior/dfd-epic3-catalog.md

## Amaç
- Harici medya veri kaynaklarından (IGDB, TMDB) meta verilerin güvenli ve tutarlı çekilmesi.
- Verilerin normalize edilip cache (Redis) ve kalıcı veritabanına kaydedilmesi.
- Frontend taleplerine düşük gecikmeli yanıt sağlayacak cache katmanı.
- Rate limit, auth, retry, ve sync job mekanizmalarının gösterilmesi.

## Özet Bileşenler
- Dış Sistemler (External Entities): IGDB, TMDB
- Süreçler (Processes): FetchFromExternal, NormalizeTransform, CacheWrite, ServeAPI, ScheduledSync, ErrorHandling
- Veri Depoları (Data Stores): RedisCache, PersistentDB, SyncJobLog
- Aktörler: Frontend (Client), Admin UI (manual sync), Auth Provider (API Key Manager)

## Merkez Akış (High-level)
1. Frontend / Client, `GET /api/catalog/:source/:id` çağrısı yapar.
2. API: önce RedisCache'i kontrol eder (Cache hit?).
   - Hit: Cache'den döner.
   - Miss: PersistentDB'yi kontrol et.
     - Eğer DB'de yok veya stale ise (last_synced > TTL) -> FetchFromExternal başlatılır.
3. FetchFromExternal IGDB/TMDB API çağrısı yapar (API key ile) ve yanıt alır.
4. NormalizeTransform süreçleri veriyi kanonik forma çevirir.
5. CacheWrite Redis'e yazar (expiration TTL ile) ve PersistentDB'ye kaydeder / günceller.
6. API sonucu frontend'e döner.
7. Arka planda ScheduledSync periyodik olarak bulk sync yapar ve SyncJobLog kaydeder.

## Meraki (Mermaid) DFD Taslağı

```mermaid
flowchart TB
  subgraph External
    IGDB[IGDB API]
    TMDB[TMDB API]
    Client[Frontend / Client]
    Admin[Admin UI]
  end

  subgraph System
    API[API Gateway / Catalog Service]
    Cache[Redis Cache]
    DB[Persistent DB]
    Fetch[FetchFromExternal]
    Norm[Normalize & Transform]
    Sync[Scheduled Sync Job]
    Log[SyncJobLog / RequestLog]
  end

  Client -->|GET /api/catalog/:src/:id| API
  API -->|check key: omni:catalog:{src}:{id}| Cache
  Cache -- hit -->|return cached payload| API
  Cache -- miss -->|no entry| API
  API -->|query| DB
  DB -- stale/absent -->|request fetch| Fetch
  Fetch -->|call| IGDB
  Fetch -->|call| TMDB
  Fetch -->|raw payload| Norm
  Norm -->|canonical payload| DB
  Norm -->|canonical payload| Cache
  API -->|return payload| Client
  Sync -->|periodic bulk jobs| Fetch
  Fetch -->|job result| Log
  API -->|log request| Log
  Admin -->|trigger sync| Sync

  classDef external fill:#f9f,stroke:#333,stroke-width:1px;
  class IGDB,TMDB,Client,Admin external;
```

## Veri Akışlarının Detayları
- Cache key pattern: `omni:catalog:{source}:{external_id}`
  - TTL önerisi: media tipine göre 1h - 24h arasında (örn. trending içerik 1h, static metadata 24h).
- PersistentDB schema (özet):
  - media(id PK, source, external_id, title, type, genres[], normalized_payload JSONB, last_synced TIMESTAMP)
  - external_source(id, name, base_url, auth_meta)
  - sync_job_log(id, job_name, started_at, finished_at, status, error_text)
- Error & retry:
  - Eğer external API 429 dönerse exponential backoff ve job retry (max 3)
  - Rate limit bilgisi varsa (X-RateLimit-Remaining), adaptive throttling uygulanır.
- Auth: Servis tarafında IGDB/TMDB anahtarları env veya secret manager'da tutulur; API çağrılarında Auth Provider'dan token yenileme akışı gösterilebilir.

## Senaryolar / Use Case Mapping
- UC-EP3-01: Client requests media by id -> Cache hit -> serve
- UC-EP3-02: Client requests media by id -> Cache miss -> DB stale -> fetch external -> normalize -> persist & cache -> serve
- UC-EP3-03: Admin triggers manual sync -> Scheduled Sync Job runs bulk fetch -> logs
- UC-EP3-04: External API rate-limited -> backoff & retry -> log failure

## Checklist — Commit edilmesi gereken ek öğeler
- [ ] Bu DFD markdown'u `docs/analysis/behavior/dfd-epic3-catalog.md` olarak repo'ya ekle (yapıldı).
- [ ] Traceability tablosuna UC-EP3 gereksinimlerini ekle (ör: docs/analysis/data/traceability.md veya docs/analysis/behavior/traceability-epic3.md)
- [ ] requirement-analysis-report.md dosyasında Epic3 referanslarını ekle
- [ ] Domain model/ER ile alan adlarını eşleştir (Mete ile koordinasyon)
- [ ] UI mockup: Integrations (API key yönetimi), Sync status ekranına link ver

## Önerilen Sonraki Adımlar (Senin tarafın için)
1. Bu dosyayı `docs/analysis/behavior/dfd-epic3-catalog.md` olarak branch `analysis_work` içinde commit ettim.
2. Traceability tablosunu oluştur: `docs/analysis/data/traceability-epic3.md` (ben hazır bir template de ekleyebilirim).
3. requirement-analysis-report.md taslağına Epic3 gereksinimlerini ekle.
4. PR açıklamasında Bu dosyaya ve `dfd-level0-1.md`'ye dikkat edilmesini belirt.

---

Bu DFD taslağı senin için bir başlangıç — istersen ben traceability tablosu template'ini de hemen oluşturayım ve aynı branch'e ekleyeyim.