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

## 👥 Phase 7: Opt-In Social Following Overlap Signal

An optional, strictly additive **social overlap bonus signal** based on public account following overlap (e.g. from an Instagram client-side export):

```
 ┌───────────────────────────┐      ┌─────────────────────────────┐      ┌───────────────────────────────┐
 │ Client-Side Export Parser │      │ POST /profiles/{id}/following│     │ Match Output Bonus Fields     │
 │ (Extracts usernames only) │ ───► │ (Normalizes & Stores list)  │ ───► │  • social_overlap_score (float)│
 │ NEVER sends ZIP to server │      │ (opted_in=True)             │      │  • shared_account_count (int) │
 └───────────────────────────┘      └─────────────────────────────┘      └───────────────────────────────┘
```

### Strict Scope & Privacy Boundaries:
- **No ZIP or Archive Ingestion**: This backend never receives, parses, or stores ZIP files or binary archives. The Instagram ZIP is parsed client-side in the browser/app, and only the resulting list of plain username strings is sent via `POST /profiles/{id}/following`.
- **Usernames Only**: No hashtags, comments, direct messages, ad interests, or search queries are accepted or modeled.
- **Count & Score Only**: API match endpoints (`/match/{a}/{b}`, `/match/{id}/candidates`, `/profiles/{id}/weekly-matches`) **never expose raw usernames or shared account names** to either party — only the computed Jaccard ratio (`social_overlap_score: float`) and shared account count (`shared_account_count: int`).
- **Strictly Non-Gating & Additive**: The social overlap calculation executes **strictly after** the 42-Koota scoring and tiering pipeline has concluded. It has **zero ability** to alter, gate, or override `overall_score`, `tier`, or `tier_ceiling`.
- **Complete Opt-Out Purge**: Calling `DELETE /profiles/{id}/following` permanently removes the `FollowingList` record, sets `opted_in=False`, and resets the overlap signal to `0.0`.

---

## 🤝 Phase 8: Mutual-Interest Confirmation & Staged Disclosure

Turns computed weekly matches into actionable matrimonial connections through **atomic mutual interest confirmation** and **strict staged disclosure**:

```
 ┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
 │ Profile A expresses    │      │ Profile B views match  │      │ Profile B expresses    │
 │ Interest (status:      │ ───► │ (status: "none")       │ ───► │ Interest (status:      │
 │ "pending")             │      │ [A's interest HIDDEN]  │      │ "mutual")              │
 └────────────────────────┘      └────────────────────────┘      └────────────────────────┘
                                                                             │
                                                                             ▼
                                                                 ┌────────────────────────┐
                                                                 │ ATOMIC MUTUAL FLIP     │
                                                                 │ Both rows flip to      │
                                                                 │ "mutual" in 1 TX       │
                                                                 └────────────────────────┘
```

### Atomic Mutual-Flip Transaction Guarantee:
- **Weekly Match Gating**: A user can only express interest in a candidate currently present in their `WeeklyMatchList`.
- **Single-Transaction Flip**: When party A has status `"pending"` and party B expresses `"pending"`, **both rows are flipped to `"mutual"` in the exact same database transaction**. It is structurally impossible for one side to show `"mutual"` while the other shows `"pending"`.
- **Declined Is Terminal**: If a profile sets action `"declined"`, the pair will **never** flip to `"mutual"`, even if the other side later expresses interest.

### Staged-Disclosure Privacy Rule:
- Under `GET /interest/{profile_id}/status` and `GET /profiles/{id}/weekly-matches`, each caller receives interest statuses **strictly from their own perspective**.
- A one-sided `"pending"` or `"declined"` expression is **completely invisible** to the other party (returned as `"none"`) until the second party also expresses interest.

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
- **Zero Raw Usernames or Following Lists** are exposed in match responses.
- **Zero Contact Info or Photos**: Phone, email, and photos do not exist in data models.
- **Staged Disclosure of Interest**: One-sided pending interest is never revealed to the other party until mutuality is confirmed.
- **Sanitized Outputs Only**: Responses deliver precomputed numeric scores, compatibility tiers, alignment insights, friction alerts, contradiction gate notes, and non-gating aggregate overlap statistics.

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
│   │   ├── routes_following.py    # POST/DELETE /profiles/{id}/following (opt-in overlap signal)
│   │   ├── routes_interest.py     # POST /interest, GET /interest/{id}/status (Phase 8 mutual interest)
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
│   ├── interest/
│   │   └── interest_service.py    # Atomic mutual-interest confirmation & staged disclosure logic
│   ├── matching/
│   │   ├── batch_runner.py        # Scheduled sequential batch runner with 30 RPM rate limiting
│   │   ├── candidates_batch.py    # 5-stage precomputed funnel (SQL -> ANN -> NLI -> LLM -> Top 5)
│   │   └── social_overlap.py      # Pure function Jaccard overlap computation on following lists
│   ├── scoring/
│   │   ├── aggregate.py           # Gated aggregation math & contradiction gate detector
│   │   ├── llm_judge.py           # Multi-provider Groq / OpenRouter / Gemini Judge engine
│   │   ├── nli.py                 # Hugging Face NLI contradiction scorer
│   │   ├── objective.py           # Hard filter short-circuit & objective partial credit logic
│   │   ├── semantic.py            # Sentence similarity, embedding cache, and vector cosine math
│   │   └── tiers.py               # 3-tier classifier and 42 curated domain insight templates
│   ├── main.py                    # FastAPI app initialization, lifespan hooks, CORS, and healthcheck
│   └── models.py                  # SQLAlchemy ORM models (Profile, Answer, Koota, InviteCode, FollowingList, WeeklyMatchList, Interest)
├── tests/
│   ├── synthetic_profiles.json    # 16 synthetic profiles with diverse edge-case traits
│   ├── test_aggregation.py        # Tests for score weighting and divergence detection
│   ├── test_api_and_tiers.py      # End-to-end API lifecycle, tier classification, and bonus invariance
│   ├── test_auth.py               # Tests for single-use invite codes, expiry, Google OAuth, and 403 gate
│   ├── test_candidates_batch.py   # Tests for monotonic funnel narrowing, NLI drops, and 30 RPM limit
│   ├── test_following_api.py      # Tests for Following upload, replacement, deletion, and privacy assertions
│   ├── test_gated_aggregation.py  # Tests for Koota 41 veto and Top-10 contradiction ceilings
│   ├── test_interest_api.py       # E2E API tests for interest expression, mutual confirmation, and privacy
│   ├── test_interest_service.py   # Unit tests for atomic flips, decline terminal state, and weekly match gate
│   ├── test_llm_judge.py          # Unit tests for multi-provider LLM Judge and fallbacks
│   ├── test_nli_scorer.py         # Tests for NLI entailment and contradiction formulas
│   ├── test_objective_scorer.py   # Tests for age gap, religion match, and partial credit matrices
│   ├── test_phase1_scaffolding.py # Basic scaffolding, health check, and JSON schema tests
│   ├── test_semantic_scorer.py    # Tests for vector caching and cosine similarity math
│   ├── test_social_overlap.py     # Tests for Jaccard calculation, ratios, opt-out short-circuits
│   ├── test_synthetic_matching.py # Edge-case assertions on 16 synthetic candidate pairs
│   └── test_weekly_matches_api.py # Tests for constant-time weekly matches API & interest status reporting
├── .env.example                   # Annotated template for all required API keys
├── requirements.txt               # Pinned production Python dependencies
└── README.md                      # Complete system documentation
```

---

## 🔌 API Reference

### 1. Express / Decline Interest
```http
POST /interest
Content-Type: application/json

{
  "profile_id": "syn-01-aarav",
  "target_profile_id": "syn-02-ananya",
  "action": "pending"
}
```
**Response (200 OK):**
```json
{
  "profile_id": "syn-01-aarav",
  "target_profile_id": "syn-02-ananya",
  "status": "pending",
  "is_mutual": false,
  "expressed_at": "2026-08-18T02:30:00.000000Z"
}
```

---

### 2. Check Candidate Interest Statuses (Staged Disclosure)
```http
GET /interest/{profile_id}/status
```
**Response (200 OK):**
```json
{
  "profile_id": "syn-01-aarav",
  "statuses": [
    {
      "candidate_id": "syn-02-ananya",
      "status": "pending",
      "is_mutual": false,
      "expressed_at": "2026-08-18T02:30:00.000000Z"
    }
  ]
}
```

---

### 3. Read-Only Weekly Matches (with Mutual Match Count)
```http
GET /profiles/{profile_id}/weekly-matches
```
**Response (200 OK — Constant Time DB Lookup):**
```json
{
  "profile_id": "syn-01-aarav",
  "total_matches": 5,
  "mutual_matches_count": 1,
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
      "social_overlap_score": 0.4286,
      "shared_account_count": 6,
      "interest_status": "mutual",
      "is_mutual": true,
      "generated_at": "2026-08-18T00:00:00Z"
    }
  ]
}
```

---

## 🧪 Automated Test Suite (70 Tests)

The engine features a comprehensive, 100% passing test suite across 17 test modules:

```text
tests/test_phase1_scaffolding.py                 [3/3 passed]
tests/test_objective_scorer.py                   [8/8 passed]
tests/test_semantic_scorer.py                    [6/6 passed]
tests/test_nli_scorer.py                         [3/3 passed]
tests/test_llm_judge.py                          [4/4 passed]
tests/test_gated_aggregation.py                  [2/2 passed]
tests/test_social_overlap.py                     [6/6 passed]
tests/test_following_api.py                      [4/4 passed]
tests/test_interest_service.py                   [7/7 passed]
tests/test_interest_api.py                       [2/2 passed]
tests/test_api_and_tiers.py                      [5/5 passed]
tests/test_aggregation.py                        [3/3 passed]
tests/test_synthetic_matching.py                 [6/6 passed]
tests/test_auth.py                               [5/5 passed]
tests/test_candidates_batch.py                   [3/3 passed]
tests/test_weekly_matches_api.py                 [3/3 passed]
======================== 70 passed in 12.53s ========================
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
