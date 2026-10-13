# E-R Diyagramı — (Metin/ASCII açıklama + Mermaid)

Basit E-R diyagramı Mermaid formatında. Dosya: docs/analysis/data/er-diagram.md

```mermaid
erDiagram
    EXTERNAL_SOURCE {
        int id PK
        string name
        string base_url
        json auth_meta
    }
    MEDIA {
        uuid id PK
        string external_id
        int source_id FK
        string title
        string type
        json normalized_payload
        timestamp last_synced
    }
    SYNC_JOB_LOG {
        int id PK
        string job_name
        timestamp started_at
        timestamp finished_at
        string status
        text error_text
    }

    EXTERNAL_SOURCE ||--o{ MEDIA : provides
    MEDIA ||--o{ SYNC_JOB_LOG : updated_by
```

Açıklama:
- EXTERNAL_SOURCE -> MEDIA (1 - many)
- MEDIA -> SYNC_JOB_LOG (1 - many) (her senkronizasyon medya üzerindeki güncellemeleri tetikleyebilir)

Görsel ihtiyaçları için PlantUML veya Draw.io kullanılabilir; bu mermaid temelli şablon repo'ya gömülebilir.