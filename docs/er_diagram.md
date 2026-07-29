# Entity-Relationship Diagram

Verified directly against a live PostgreSQL schema (`\d+` output on each
table after running `alembic upgrade head`) — not hand-drawn from memory.

```mermaid
erDiagram
    USERS ||--o{ RESUMES : uploads
    RESUMES ||--|| ATS_SCORES : "scored as (1:1)"
    RESUMES ||--|| PREDICTIONS : "predicted as (1:1)"

    USERS {
        int id PK
        varchar255 email UK
        varchar255 hashed_password
        varchar255 full_name
        timestamp created_at
    }
    RESUMES {
        int id PK
        int user_id FK
        varchar500 file_path
        varchar255 original_filename
        text raw_text
        jsonb extracted_data
        timestamp uploaded_at
    }
    ATS_SCORES {
        int id PK
        int resume_id FK_UK
        int overall_score
        jsonb category_scores
        jsonb suggestions
        timestamp created_at
    }
    PREDICTIONS {
        int id PK
        int resume_id FK_UK
        varchar100 predicted_role
        jsonb role_probabilities
        float8 salary_min
        float8 salary_avg
        float8 salary_max
        float8 confidence
        timestamp created_at
    }
```

## Design notes

- **`ats_scores.resume_id` and `predictions.resume_id` are both UNIQUE
  foreign keys** — this is what makes the relationship genuinely 1:1
  rather than 1:many. Verified in the live schema (`ats_scores_resume_id_key`
  and `predictions_resume_id_key` unique constraints). This is also why
  the `/predictions/generate` and `/ats/score/{id}` endpoints **update**
  the existing row on a second call rather than inserting a duplicate —
  the application code checks for an existing row first, but the unique
  constraint is the actual guarantee at the database level.

- **JSONB, not JSON**: `extracted_data`, `category_scores`, `suggestions`,
  and `role_probabilities` are all genuine PostgreSQL `jsonb` (confirmed
  in the live schema dump) — chosen over exploding each into separate
  tables since their shape varies per resume (a candidate might have 3
  skills or 30) and JSONB supports indexing/containment queries if ever
  needed, unlike plain `JSON`.

- **No `roadmap_progress` table yet** — the Phase 1 plan sketched one for
  tracking per-skill learning progress, but it was never built since the
  roadmap feature turned out not to need persistence (it's recomputed
  live from the skill gap each time). Noted here rather than silently
  dropped, in case it's picked up as a future feature.
