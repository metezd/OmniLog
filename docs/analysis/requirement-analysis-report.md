# Requirement Analysis Report — OmniLog (Preliminary)

Bu doküman, analiz aşaması için senin (Musab) sorumluluğundaki gereksinimlerin ve Epic 3 entegrasyonunun (IGDB / TMDB) ön analiz raporunun ilk taslağını içerir. Dosya path: docs/analysis/requirement-analysis-report.md

## 1. Proje Özeti
OmniLog: medya (oyun/film/dizi) meta verilerini toplayan, normalize eden, cacheleyen ve frontend taleplerine hızlı yanıt veren bir katalog servisi içerir. Epic 3, IGDB ve TMDB gibi harici katalog sağlayıcılarıyla entegrasyonu kapsar.

## 2. Kapsam ve Sınırlar
- Kapsam: Harici sağlayıcılardan (IGDB, TMDB) veri çekme, normalize etme, cacheleme (Redis), kalıcı veritabanına yazma, API ile sunma, rate-limit ve retry mekanizmaları.
- Dışında: ML öneri motoru, embedding pipeline (Sidar'ın sorumluluğu), frontend detaylı mockup'ları (Kerem), domain modelin nihai onayı (Mete).

## 3. Stakeholder'lar
- Product Owner / Hoca
- Mete (Domain model & E-R)
- Kağan (Epic2, Epic4 DFD'ler)
- Sidar (ML)
- Kerem (Frontend)
- Yeşim (Reviewer)

## 4. Use Case'ler (Kısa)
- UC-EP3-01: Kullanıcı bir medya öğesini id ile ister — cache hit ise cache'den servis edilir.
- UC-EP3-02: Cache miss veya stale durumunda DB kontrol edilir; yoksa veya stale ise dış API'den çekilir.
- UC-EP3-03: Admin manuel senkronizasyon başlatır.
- UC-EP3-04: External API rate-limit durumunda backoff & retry uygulanır.

## 5. Fonksiyonel Gereksinimler (Önemli olanlar)
- R-EP3-01: API, `GET /api/catalog/:source/:id` endpoint'ini sağlamalı.
- R-EP3-02: Öncelikle Redis cache kontrol edilecek; cache key pattern `omni:catalog:{source}:{external_id}` olmalı.
- R-EP3-03: Cache miss durumunda persistent DB kontrol edilecek ve gerekirse external çağrı tetiklenecek.
- R-EP3-04: External çağrılar için API anahtarları güvenli şekilde saklanacak (secrets manager / env).
- R-EP3-05: Scheduled Sync job periyodik olarak çalışmalı ve loglanmalı.
- R-EP3-06: Rate-limit ve 429 durumlarında exponential backoff ile retry yapılacak (max 3).

## 6. Non-functional Gereksinimler
- NFR-1: Read latency cache hit için < 50ms hedefi.
- NFR-2: Cache TTL konfigüre edilebilir olmalı; test ortamı için default 1 saat.
- NFR-3: Sync job için observability: job duration, success/failure oranı, error logs.
- NFR-4: High availability: cache katmanı failover planı (opsiyonel: Redis sentinel/cluster).

## 7. Veri Akışları ve Referans DFD'ler
- Primary DFD: docs/analysis/behavior/dfd-level0-1.md (seviye 0-1)
- Epic 3 DFD: docs/analysis/behavior/dfd-epic3-catalog.md

## 8. Traceability (kısa örnek) — detaylı tablo ayrı dosyada
Bu doküman ile traceability tablosu eşleştirilmiştir. Her gereksinim için ilgili DFD süreçleri, veri depoları ve hedef API endpoint'leri tabloda izlenir.

## 9. Riskler ve Varsayımlar
- Varsayım: IGDB/TMDB API anahtarları ekip içinde güvenli biçimde paylaşılacak.
- Risk: External API rate-limit'leri senin sync job'ları yavaşlatabilir.
- Risk: Normalizasyon kuralları (örn. farklı kaynaklarda farklı alan isimleri) belirsizliği artırabilir — Mete ile senkronize ol.

## 10. Teslimler ve Sonraki Adımlar
- Bu raporun taslağı: docs/analysis/requirement-analysis-report.md (bu dosya)
- Traceability tablosu: docs/analysis/data/traceability-epic3.md
- PR: analysis_work branch'inde PR açılacak, reviewer: @yesim, deadline: 14.10.2026

---

Not: Bu raporun gerçekteki gereksinim listesini daha da detaylandırmak ve numaralandırmak gerekiyor; ben temel ve öncelikli maddeleri ekledim. Düzenlemeler yapabilirsin, ben commitlerim.