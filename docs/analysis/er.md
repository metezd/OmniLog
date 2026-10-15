# ER Diagram Summary

> **Note:** this document describes the baseline that is already implemented. The full E-R model and the data dictionary for all six epics are in [data/er-diagram.md](data/er-diagram.md).

This document captures the logical data model for the current OmniLog implementation. It reflects the backend entities already defined in the project and the relationships needed to support personal media tracking.

## Entity list

### users
| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INTEGER | PK | Primary key |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | Login/display identifier |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL | User email |
| `hashed_password` | VARCHAR(255) | NOT NULL | Hashed password |
| `created_at` | DATETIME | DEFAULT now | Account creation time |

### media_items
| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INTEGER | PK | Primary key |
| `title` | VARCHAR(200) | NOT NULL | Media title |
| `media_type` | ENUM | NOT NULL | `GAME`, `SERIES`, or `MOVIE` |
| `poster_url` | VARCHAR(500) | NULL | Optional cover image |
| `release_date` | VARCHAR(50) | NULL | Optional release date string |
| `external_api_id` | INTEGER | NULL | Optional third-party ID |

### user_libraries
| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INTEGER | PK | Primary key |
| `user_id` | INTEGER | FK -> `users.id`, NOT NULL | Owner of the library entry |
| `media_item_id` | INTEGER | FK -> `media_items.id`, NOT NULL | Referenced media item |
| `status` | ENUM | NOT NULL, DEFAULT `PLAN_TO_WATCH` | Personal tracking state |
| `rating` | FLOAT | NULL | User rating, 1-10 when present |
| `updated_at` | DATETIME | DEFAULT now, on update | Last modification time |

## Cardinality

- `users` to `user_libraries`: 1:N
- `media_items` to `user_libraries`: 1:N
- `user_libraries` is the bridging table between users and media items

## Relationship rules

- One user may have many media entries in their library.
- One media item may be associated with many user libraries.
- A user cannot have duplicate entries for the same media item.
- A rating is allowed only when it is within the range 1 to 10.
- Deleting a user or media item cascades to its related library entries.

## Logical model

```text
users (1) ─────< (N) user_libraries (N) >───── (1) media_items
```

## Key observations

- The model is normalized around a shared media catalog and personal user state.
- User-specific metadata is stored in `user_libraries` rather than in `media_items`.
- This keeps the catalog stable while allowing each user to track status and ratings independently.
