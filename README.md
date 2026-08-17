# 💍 Koota Match Engine

> **A High-Precision, Zero-Cost 42-Koota Marital Compatibility Engine Tailored for Indian Cultural & Psychological Realities.**

[![CI Test Suite](https://github.com/yashwoodstock-blip/koota-match-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/yashwoodstock-blip/koota-match-engine/actions/workflows/ci.yml)
[![Weekly Match Funnel](https://github.com/yashwoodstock-blip/koota-match-engine/actions/workflows/weekly-match.yml/badge.svg)](https://github.com/yashwoodstock-blip/koota-match-engine/actions/workflows/weekly-match.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python)](https://www.python.org/)
[![Supabase](https://img.shields.io/badge/Database-Supabase%20Postgres-3ECF8E?style=flat&logo=supabase)](https://supabase.com)
[![Groq Llama-3.3-70B](https://img.shields.io/badge/LLM%20Judge-Groq%20Llama--3.3--70B-F55036?style=flat)](https://groq.com)
[![Hugging Face](https://img.shields.io/badge/Embeddings%20%26%20NLI-Hugging%20Face%20Serverless-FFD21E?style=flat&logo=huggingface)](https://huggingface.co)
[![Zero-Cost Stack](https://img.shields.io/badge/Cloud%20Cost-%240.00%2Fmo%20(Free%20Tier)-brightgreen?style=flat)](#-zero-cost-deployment-architecture)

---

## 📖 Executive Summary

The **Koota Match Engine** replaces archaic astrology-based matchmaking with an empirical, multi-dimensional psychometric framework. Expanding traditional Indian matrimonial criteria into **42 scientific Kootas across 14 life pillars**, the engine blends deterministic objective logic, transformer embeddings, natural language inference (NLI), and multi-provider LLM-as-a-Judge reasoning to deliver weekly precomputed matches without exposing sensitive private text.

---

## 🚪 Phase 6: Invite-Only Onboarding & Precomputed Funnel

Aadhaar/DigiLocker KYC has been replaced by a **strict invite-only gate**:

```
 ┌────────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
 │ Single-Use     │       │ Google OAuth via     │       │ Demographic & Staged │
 │ Invite Code    │ ────► │ Supabase Auth        │ ────► │ 42-Koota Question    │
 │ (/auth/redeem) │       │ (/auth/google/cb)    │       │ Assessment           │
 └────────────────┘       └──────────────────────┘       └──────────────────────┘
```

1. **Invite-Only Gate**: A valid, unused 8-character invite code is mandatory to initiate registration. Any attempt to create a profile without a redeemed invite code or token receives an immediate `403 Forbidden`.
2. **Google OAuth via Supabase Auth**: Verified Google identity creates/links exactly one `Profile` row per unique email address ($0$ authentication infrastructure cost).
3. **Intent & Demographics**: Collects Layer-1 demographics (age, religion, caste preference, city) followed by objective and staged subjective assessment batches.

---

## 🌪️ The Weekly Precomputed Match Funnel

Rather than running heavy on-request matching during user browsing, candidate discovery runs on a **Sunday 00:00 UTC batch job** with a monotonic 5-stage funnel:

```mermaid
graph TD
    A[Total Active Profile Pool] --> B[Stage 1: SQL-Level Hard Filter]
    B -->|Age Gap <= 2 yrs + Religion Exact Match + Caste Rules| C[Eligible Candidate Pool]
    
    C --> D[Stage 2: Vector ANN Retrieval<br/>Koota 41 Life Purpose Embedding]
    D -->|Sort by Vector Similarity & LIMIT 50| E[Top 50 Candidates]
    
    E --> F[Stage 3: NLI Contradiction Screen<br/>BART-MNLI on Top-10 Kootas]
    F -->|Drop Koota 41 & Top-10 Contradictions outright| G[Ranked Survivors]
    G -->|Keep Top 10 Shortlist| H[Top 10 Shortlist]
    
    H --> I[Stage 4: Multi-Provider LLM-as-a-Judge<br/>Groq Llama-3.3-70B / OpenRouter]
    I -->|Gated Aggregation Math & Tier Ceilings| J[Gated Scored Matches]
    
    J --> K[Stage 5: Persist Top 5 into WeeklyMatchList]
    K --> L[Read-Only API: GET /profiles/{id}/weekly-matches]
```

### Funnel Narrowing Metrics

| Stage | Mechanism | Input Size | Output Size | Compute Characteristic |
| :--- | :--- | :---: | :---: | :--- |
| **Stage 1: SQL Filter** | Indexed SQL `WHERE` on age gap, religion, caste | Entire Pool | Variable | $< 1\text{ms}$ sub-millisecond |
| **Stage 2: Vector ANN** | Cosine similarity on Koota 41 (Life Purpose) embedding | Filtered Pool | **Top 50** | Database vector indexing / In-memory |
| **Stage 3: NLI Screen** | Hugging Face BART-MNLI contradiction detection | Top 50 | **Top 10** | Contradictions dropped instantly |
| **Stage 4: LLM Judge** | Multi-Provider Groq Llama-3.3-70B / OpenRouter Judge | Top 10 | Top 10 Scored | Bounded strictly to top 10 ($\le 10$ calls) |
| **Stage 5: Weekly List** | Gated Aggregation math & persistent storage | Top 10 | **Top 5** | Written to `WeeklyMatchList` table |

---

## 🏛️ The 42-Koota Domain Framework

The engine evaluates compatibility across 14 Pillars weighted on a research-calibrated scale ($w1$ to $w15$):

### Pillar Hierarchy & Weighting ($w1$–$w15$)

| Pillar | Focus Area | Weight Range | Key India-Centric Realities Evaluated |
| :--- | :--- | :---: | :--- |
| **Pillar A** | Knowing Each Other (Love Maps) | $w4$–$w6$ | Emotional vulnerability, childhood histories, career trajectories. |
| **Pillar B** | Fondness, Admiration & Respect | $w6$–$w10$ | Public appreciation, gratitude habits, caste/social status egalitarianism. |
| **Pillar C** | Emotional Attunement & Bids | $w6$–$w8$ | Responsiveness to emotional bids, social battery management in joint family setups. |
| **Pillar D** | Mutual Influence & Decision Making | $w10$–$w12$ | Financial purchase autonomy, veto dynamics, career vs family trade-offs. |
| **Pillar E** | Conflict Style & De-escalation | $w8$–$w10$ | Stonewalling vs immediate engagement, repair attempts during domestic arguments. |
| **Pillar F** | In-Law Dynamics & Elder Care | **$w10$–$w14$** | **Co-residence expectations, elder care division among siblings, parent boundary enforcement.** |
| **Pillar G** | Career Continuity & Gender Roles | **$w10$–$w14$** | **Dual-career relocations, domestic chore distribution, postpartum career restarts.** |
| **Pillar H** | Financial Architecture & Money Values | $w10$–$w12$ | Joint vs separate accounts, parental financial remittances, investment risk tolerance. |
| **Pillar I** | Parenting Philosophy & Family Size | $w8$–$w12$ | Timeline to children, disciplinary philosophy, grandparent involvement boundaries. |
| **Pillar J** | Intimacy, Affection & Physical Needs | $w6$–$w10$ | Communication comfort regarding intimacy, non-sexual physical affection frequency. |
| **Pillar K** | Social Architecture & Community | $w4$–$w8$ | Community obligations, festival celebrations, friend circle boundary management. |
| **Pillar L** | Crisis Resilience & Life Transitions | $w8$–$w12$ | Health crises, economic downturn handling, sabbatical support agreements. |
| **Pillar M** | Shared Meaning & Life Purpose | **$w14$–$w15$** | **Existential purpose of marriage, spiritual/philosophical alignment, core life legacy.** |
| **Pillar N** | Hard Demographics & Filters | **Filter / $w1$** | **Age gap threshold ($\le 2$ yrs default), religion exact match, caste requirements.** |

---

## 🔒 Privacy Architecture

To guarantee total matrimonial privacy:
- **Zero Raw Free-Text Answers** are returned in any API response.
- **Zero Demographic Data** (income, caste, raw age) is leaked in match payloads.
- **Sanitized Outputs Only**: Responses deliver precomputed numeric scores, compatibility tiers, alignment insights, friction alerts, and contradiction gate notes.

---

## 📁 Repository Directory Map

```text
koota-match-engine/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Automated pytest CI runner on every push/PR
│       ├── keepalive.yml          # Cron job running every 3 days to keep Render & Supabase awake
│       └── weekly-match.yml       # Scheduled Sunday cron executing weekly precomputed match funnel
├── app/
│   ├── api/
│   │   ├── routes_auth.py         # /auth/invite/generate, /auth/invite/redeem, /auth/google/callback
│   │   ├── routes_match.py        # POST /match/{id_a}/{id_b} and GET /match/{id}/candidates
│   │   ├── routes_profiles.py     # Profile CRUD (invite-gated) and answer submissions
│   │   ├── routes_weekly.py       # GET /profiles/{id}/weekly-matches (strictly read-only)
│   │   └── schemas.py             # Pydantic v2 request/response validation contracts
│   ├── auth/
│   │   ├── google_oauth.py        # Supabase Google OAuth wiring, JWT server-side verification
│   │   └── invite.py              # Single-use invite code generation, expiry, and token signing
│   ├── db/
│   │   ├── kootas.json            # Complete 42-Koota Question Bank across 14 Pillars
│   │   ├── seed_kootas.py         # Database seeder to initialize and verify all 42 Kootas
│   │   ├── seed_synthetic.py      # Seeder for 16 realistic edge-case synthetic profiles
│   │   └── session.py             # SQLAlchemy 2.0 async session and engine factory
│   ├── matching/
│   │   ├── batch_runner.py        # Scheduled sequential batch runner with 30 RPM rate limiting
│   │   └── candidates_batch.py    # 5-stage precomputed funnel (SQL -> ANN -> NLI -> LLM -> Top 5)
│   ├── scoring/
│   │   ├── aggregate.py           # Gated aggregation math & contradiction gate detector
│   │   ├── llm_judge.py           # Multi-provider Groq / OpenRouter / Gemini Judge engine
│   │   ├── nli.py                 # Hugging Face NLI contradiction scorer
│   │   ├── objective.py           # Hard filter short-circuit & objective partial credit logic
│   │   ├── semantic.py            # Sentence similarity, embedding cache, and vector cosine math
│   │   └── tiers.py               # 3-tier classifier and 42 curated domain insight templates
│   ├── main.py                    # FastAPI app initialization, lifespan hooks, CORS, and healthcheck
│   └── models.py                  # SQLAlchemy ORM models (Profile, Answer, Koota, InviteCode, WeeklyMatchList)
├── tests/
│   ├── synthetic_profiles.json    # 16 synthetic profiles with diverse edge-case traits
│   ├── test_aggregation.py        # Tests for score weighting and divergence detection
│   ├── test_api_and_tiers.py      # End-to-end API lifecycle and tier classification tests
│   ├── test_auth.py               # Tests for single-use invite codes, expiry, Google OAuth, and 403 gate
│   ├── test_candidates_batch.py   # Tests for monotonic funnel narrowing, NLI drops, and 30 RPM limit
│   ├── test_gated_aggregation.py  # Tests for Koota 41 veto and Top-10 contradiction ceilings
│   ├── test_llm_judge.py          # Unit tests for multi-provider LLM Judge and fallbacks
│   ├── test_nli_scorer.py         # Tests for NLI entailment and contradiction formulas
│   ├── test_objective_scorer.py   # Tests for age gap, religion match, and partial credit matrices
│   ├── test_phase1_scaffolding.py # Basic scaffolding, health check, and JSON schema tests
│   ├── test_semantic_scorer.py    # Tests for vector caching and cosine similarity math
│   ├── test_synthetic_matching.py # Edge-case assertions on 16 synthetic candidate pairs
│   └── test_weekly_matches_api.py # Tests for constant-time, read-only weekly matches API
├── .env.example                   # Annotated template for all required API keys
├── requirements.txt               # Pinned production Python dependencies
└── README.md                      # Complete system documentation
```

---

## 🔌 API Reference

### 1. Generate Invite Code (Admin)
```http
POST /auth/invite/generate
Content-Type: application/json

{
  "created_by": "admin",
  "expires_in_days": 30
}
```
**Response (201 Created):**
```json
{
  "status": "success",
  "code": "K9X4M2P7",
  "expires_at": "2026-09-17T02:00:00.000000Z",
  "created_by": "admin"
}
```

---

### 2. Redeem Invite Code
```http
POST /auth/invite/redeem
Content-Type: application/json

{
  "code": "K9X4M2P7"
}
```
**Response (200 OK):**
```json
{
  "status": "valid",
  "message": "Invite code verified successfully.",
  "invite_code": "K9X4M2P7",
  "invite_token": "K9X4M2P7:1787002000:a1b2c3d4..."
}
```

---

### 3. Read-Only Weekly Matches
```http
GET /profiles/{profile_id}/weekly-matches
```
**Response (200 OK — Constant Time DB Lookup):**
```json
{
  "profile_id": "syn-01-aarav",
  "total_matches": 5,
  "is_precomputed": true,
  "matches": [
    {
      "candidate_id": "syn-02-ananya",
      "candidate_name": "Ananya Iyer",
      "score": 0.9136,
      "tier": "strong match",
      "alignment_points": [
        "Deep philosophical consensus on the transcendent purpose and companionship of marriage.",
        "High resonance on in-law engagement rhythm and balanced filial boundaries."
      ],
      "friction_points": [],
      "contradiction_gates": [],
      "generated_at": "2026-08-18T00:00:00Z"
    }
  ]
}
```

---

## 🧪 Automated Test Suite (49 Tests)

The engine features a comprehensive, 100% passing test suite across 13 test modules:

```text
tests/test_phase1_scaffolding.py                 [3/3 passed]
tests/test_objective_scorer.py                   [8/8 passed]
tests/test_semantic_scorer.py                    [6/6 passed]
tests/test_nli_scorer.py                         [3/3 passed]
tests/test_llm_judge.py                          [4/4 passed]
tests/test_gated_aggregation.py                  [2/2 passed]
tests/test_api_and_tiers.py                      [4/4 passed]
tests/test_aggregation.py                        [3/3 passed]
tests/test_synthetic_matching.py                 [6/6 passed]
tests/test_auth.py                               [5/5 passed]
tests/test_candidates_batch.py                   [3/3 passed]
tests/test_weekly_matches_api.py                 [2/2 passed]
======================== 49 passed in 3.36s ========================
```

---

## 🚀 Local Setup & Manual Batch Testing

### 1. Run Migrations and Seeders
```bash
# Seed 42 Kootas
python -m app.db.seed_kootas

# Seed 16 synthetic test profiles
python -m app.db.seed_synthetic
```

### 2. Trigger the Precomputed Match Funnel Manually
```bash
# Run batch runner for all active profiles
python -m app.matching.batch_runner
```

### 3. Trigger Weekly Cron via GitHub Actions
To test the weekly cron on GitHub Actions without waiting for Sunday:
```bash
gh workflow run "Weekly Match Precomputation Funnel" --repo yashwoodstock-blip/koota-match-engine
```

### 4. Run API Server
```bash
uvicorn app.main:app --reload
```
Interactive Swagger Documentation: **`http://127.0.0.1:8000/docs`**

### 5. Run Test Suite
```bash
pytest -v
```

---

## 🌐 Zero-Cost Deployment Architecture

The engine is engineered to run permanently on free-tier infrastructure ($0.00/month):

```
┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
│  Render Free Web App   │      │  Supabase Free Postgres│      │  GitHub Actions Cron   │
│  FastAPI Application   │◄────►│  Postgres + pgvector   │◄────►│  Keepalive (every 3d)  │
│  (Read-only Matches)   │      │  + Supabase Google Auth│      │  Weekly Match (Sunday) │
└────────────────────────┘      └────────────────────────┘      └────────────────────────┘
            │                                                                │
            ▼                                                                ▼
┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
│  Groq Free LLM Tier    │      │  OpenRouter Free Pool  │      │  Hugging Face Serverless│
│  Llama-3.3-70B (30 RPM)│      │  Nemotron & Gemma-4    │      │  MiniLM & BART-MNLI    │
└────────────────────────┘      └────────────────────────┘      └────────────────────────┘
```

- **Render Web Service**: Deploys via Docker or Python runtime.
- **Supabase PostgreSQL & Auth**: Free cloud database + Google OAuth authentication.
- **GitHub Keep-Alive Action**: Pings Render & Supabase every 3 days to prevent inactivity sleep.
- **GitHub Weekly Match Action**: Automatically precomputes top 5 matches every Sunday at 00:00 UTC.

---

## 📜 License

MIT License. Designed and engineered for modern, scientific, culturally-attuned marital matching.
