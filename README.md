# Koota Match Engine

A high-precision, India-focused marital compatibility matching backend built on the **42-Koota Framework** across 14 psychological and structural pillars. Deployed entirely on free-tier infrastructure.

---

## Architecture & Stack

- **Framework**: Python 3.11, FastAPI, SQLAlchemy (Async) + `asyncpg` / `aiosqlite`
- **Database**: Supabase Free PostgreSQL / Local SQLite for dev and testing
- **Semantic Inference**: Hugging Face Serverless Inference API (HTTP-only sentence-similarity, zero local PyTorch overhead)
- **Deployment**: Render Free Web Service
- **CI & Keep-Alive**: GitHub Actions (`ci.yml` for automated test suites, `keepalive.yml` to prevent 15-minute Render spin-down and Supabase inactivity pauses)

---

## Directory Structure

```text
koota-match-engine/
  app/
    main.py                 # FastAPI application entry point & lifespan
    models.py               # SQLAlchemy ORM models (Koota, Profile, Answer, MatchResult)
    scoring/
      objective.py          # Hard filter short-circuiting & objective scoring
      semantic.py           # Hugging Face serverless embedding & cosine similarity
      aggregate.py          # Weight merging & objective-subjective divergence detection
      tiers.py              # 3-tier classification & safe templated insight generator
    api/
      routes_profiles.py    # Profile creation & answer submission
      routes_match.py       # Compatibility calculation & candidate ranking
    db/
      seed_kootas.py        # Database seeder
      kootas.json           # Complete 42-Koota domain definition with all questions
  tests/
    test_objective_scorer.py
    test_semantic_scorer.py
    test_aggregation.py
    synthetic_profiles.json
  .github/workflows/
    ci.yml                  # Automated CI test suite
    keepalive.yml           # Scheduled 3-day health pinger for free tier
  Dockerfile
  requirements.txt
  .env.example
  README.md
```

---

## Local Setup

### 1. Clone & Environment Setup

```bash
git clone <repo-url>
cd koota-match-engine

python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Description |
| :--- | :--- |
| `DATABASE_URL` | PostgreSQL or SQLite connection string (e.g. `sqlite+aiosqlite:///./koota.db` for local dev) |
| `SUPABASE_URL` | Supabase project URL (optional for production keepalive/database) |
| `SUPABASE_KEY` | Supabase API key (anon / service role) |
| `HF_API_TOKEN` | Free Hugging Face access token for serverless embeddings |
| `HF_EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| `RENDER_EXTERNAL_URL` | Render service URL for keepalive ping |

### 3. Seed the 42 Kootas

```bash
python -m app.db.seed_kootas
```

### 4. Run the Local Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 5. Run the Test Suite

```bash
pytest -v
```

---

## Free-Tier Keep-Alive System

To prevent Render free web services from sleeping and Supabase instances from pausing after periods of inactivity:
- The `.github/workflows/keepalive.yml` GitHub Action triggers every 3 days.
- **Manual Trigger**: Go to your GitHub repository -> **Actions** -> **Free Tier Keepalive Ping** -> click **Run workflow**.

---

## Strict Design & Privacy Rules

1. **Zero Raw Answer Leakage**: Raw text answers and Layer-1 demographics (caste, religion, income) are never exposed via match API endpoints.
2. **Hard-Filter Short Circuit**: Age gap, religion mismatch, and Koota 42 hard constraints terminate evaluation before running weighted scoring.
3. **Disagreement Surfacing**: Sharp divergences between objective multiple-choice alignment and subjective deep-response resonance (e.g. on in-law deference or career continuity) generate explicit friction flags rather than being averaged into obscurity.
