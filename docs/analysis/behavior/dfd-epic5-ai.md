# Epic 5 FDD: Öneri Motoru, Spoiler Tespiti ve Embedding Yapısı

Bu belge, OmniLog'un Epic 5 kapsamındaki yapay zekâ odaklı özelliklerini ve bu özelliklerin veri modeline etkisini açıklar. Odak noktaları şunlardır:

- öneri motoru (recommendation engine)
- spoiler tespiti (spoiler detection)
- embedding tablosunun veri modeline entegrasyonu
- vektör alanı için önerilen depolama yaklaşımı
- E-R model üzerindeki gözden geçirme sonuçları

## 1. Amaç ve kapsam

Epic 5, kullanıcı deneyimini artırmak amacıyla şu üç temel bileşeni içerir:

1. Kullanıcının medya geçmişi ve tercihleri üzerinden kişiselleştirilmiş öneriler üretmek.
2. Kullanıcı yorumlarında spoiler içeren ifadeleri tespit etmek.
3. Görsel, metinsel ve davranışsal sinyalleri ortak bir embedding uzayında temsil etmek.

Bu bağlamda veri modeli yalnızca kullanıcı ve medya ilişkisini değil; aynı zamanda arka planda üretilen embedding bilgilerini de barındırmalıdır.

## 2. Alan modeli ve iş akışı

### 2.1 Temel varlıklar

- User: sistemde kayıtlı kullanıcı
- MediaItem: katalogdaki oyun, dizi veya film kaydı
- UserLibrary: kullanıcının medya ile kurduğu kişisel ilişki
- Review / Journal Entry: kullanıcı yorumları ve değerlendirmeleri
- MediaEmbedding: içerik embedding bilgilerini tutan tablo
- UserPreferenceEmbedding: kullanıcı profili embedding bilgileri

### 2.2 İş akışı

1. Kullanıcı medya ekler, izler, değerlendirir veya yorum yazar.
2. Sistem, kullanıcı davranışlarını ve medya metadatasını toplar.
3. Kullanıcı ve medya için embedding vektörleri üretilir.
4. Benzerlik hesabı yapılır ve öneri listeleri oluşturulur.
5. Yorum metni spoiler taşıyıp taşımadığı analiz edilir.
6. Sonuçlar kullanıcı arayüzüne yansıtılır.

## 3. Öneri motoru

### 3.1 Temel yaklaşım

Öneri sistemi, yalnızca etiket veya kategori eşleştirmesi değil; aşağıdaki sinyalleri birleştiren bir yaklaşım kullanmalıdır:

- kullanıcıların mevcut kütüphanesi
- izleme durumu (`PLAN_TO_WATCH`, `IN_PROGRESS`, `COMPLETED`, `DROPPED`)
- aldığı rating
- medya türü (`GAME`, `SERIES`, `MOVIE`)
- kullanıcı yorumları ve başlık metinleri
- üretilmiş embedding vektörleri

### 3.2 Öneri mantığı

Öneri motoru genellikle şu sırada çalışır:

1. Kullanıcı profil vektörü oluşturulur.
2. Benzer medya öğeleri için embedding matrisi oluşturulur.
3. Cosine similarity veya dot product kullanılarak en benzer başlıklar hesaplanır.
4. Kullanıcının zaten sahip olduğu başlıklar filtrelenir.
5. Sonuçlar yeniden sıralanır ve puanlanır.

### 3.3 Öneri çıktısı

Öneri sonuçları şu şekilde temsil edilebilir:

- mediatitle
- similarity_score
- reason_code
- recommendation_source
- created_at

Bu yapı, sistemin içgörüsü ve iyileştirme sürecini kolaylaştırır.

## 4. Spoiler tespiti

### 4.1 Amaç

Kullanıcı yorumlarında veya incelemelerde spoiler içeren ifadeleri otomatik olarak tespit etmek, kullanıcı deneyimini korur. Özellikle anlatı ağırlıklı oyunlar ve diziler için bu gereklilik önemlidir.

### 4.2 Tespit yaklaşımı

Spoiler tespiti için önerilen yaklaşım:

- yorum metninin sınıflandırılması
- karakter/olay/sonlu karakter dizileri için anahtar kelime analizi
- embedding bazlı benzerlik kontrolü
- insan denetimi için düşük güvenli skorlar

### 4.3 Veri yönü

Spoiler bilgisi, yorum veya jüri girdisine ek olarak ayrı bir alan olarak tutulabilir:

- `is_spoiler` : boolean
- `spoiler_confidence` : float
- `spoiler_detected_at` : datetime
- `review_id` : foreign key

Bu şekilde veriler daha sonra arama, filtreleme ve moderation akışında kullanılabilir.

## 5. Embedding tablosu ve ER model revizyonu

### 5.1 Mevcut model ile uyum

Mevcut veri modeli, kullanıcı ile medya arasındaki kişisel ilişkiyi `user_libraries` üzerinden tutar. Epic 5 için bu yapı genişletilebilir. Embedding verileri, kullanıcı ve medya varlıkları için ayrı bir depolama katmanı olarak eklenmelidir.

Önerilen tablo yapısı:

#### `media_embeddings`

| Alan | Tür | Açıklama |
|---|---|---|
| `id` | INTEGER | primary key |
| `media_item_id` | INTEGER | `media_items.id` foreign key |
| `embedding_model` | VARCHAR | örn. `text-embedding-3-small` |
| `embedding_version` | VARCHAR | model sürümü |
| `vector` | VECTOR | medya vektörü |
| `created_at` | DATETIME | oluşturulma zamanı |
| `updated_at` | DATETIME | son güncelleme |

#### `user_embeddings`

| Alan | Tür | Açıklama |
|---|---|---|
| `id` | INTEGER | primary key |
| `user_id` | INTEGER | `users.id` foreign key |
| `embedding_model` | VARCHAR | kullanıcı profili modeli |
| `embedding_version` | VARCHAR | model sürümü |
| `vector` | VECTOR | kullanıcı profili vektörü |
| `created_at` | DATETIME | oluşturulma zamanı |
| `updated_at` | DATETIME | son güncelleme |

### 5.2 Vektör alanı için önerilen yaklaşım

İlk etapta veritabanı alanı olarak `VECTOR` tipi kullanılabilir. PostgreSQL ortamında bu alan için `pgvector` gibi bir uzantı tercih edilir. Amaç şudur:

- embedding vektörlerinin doğrudan veri tabanında saklanması
- benzerlik sorgularının SQL içinde yapılması
- model versiyonlama ve tekrar üretim ihtiyacının kolay yönetilmesi

Not: Eğer sistemin ölçeği beklenenden yüksekse, embedding depolama için veritabanı yerine ayrılmış vector store da düşünülebilir; ancak ER modeli ve uygulama katmanı bakımından `media_embeddings` ve `user_embeddings` tablosu temel tasarım olarak uygundur.

### 5.3 E-R gözden geçirme notları

Mevcut tablo yapısı şu şekilde düşünülmelidir:

- `users` ve `media_items` ana varlıklar olarak kalır.
- `user_libraries` kullanıcının kişisel medya ilişkisidir.
- `media_embeddings` ve `user_embeddings` ikincil, hesaplanmış veri yapılarıdır.
- Bu tablolar ana varlıkların özelliklerini bozmadan, zenginleştirilmiş analitik ve öneri verisini tutar.

Özetle:

- kullanıcı ve medya bilgileri ilişkisel modelde kalır
- embedding verileri ayrı bir katmanda tutulur
- arka planda oluşturulan vektörler, öneri ve benzerlik işleyişini destekler

## 6. Ana kararlar

1. Öneri motoru kullanıcı ve medya embedding'lerine dayanmalıdır.
2. Spoiler tespiti yorum metni üzerinde yapılmalıdır ve sonuç metadata olarak saklanmalıdır.
3. Embedding bilgileri ayrı tablolarda tutulmalıdır; ana varlık yapısını bozmamalıdır.
4. `VECTOR` alanı için PostgreSQL + pgvector yaklaşımı en uyumlu çözümdür.
5. `UserLibrary` yapısı mevcut kalmalı; yalnızca öneri ve spoiler işlevleri için ek metadata katmanı eklenmelidir.

## 7. Son değerlendirme

Epic 5 için önerilen tasarım, sistemi hem veri bütünlüğü hem de öneri ve spoiler tespiti gereksinimleri açısından güçlü tutar. Mevcut `User`, `MediaItem`, `UserLibrary` yapısı korunurken, embedding ve semantik analitik veriler ayrı bir katmanda yönetilir. Bu yaklaşım, gelecekte daha fazla özellik eklendiğinde de ölçeklenebilir ve bakımı kolay kalır.
