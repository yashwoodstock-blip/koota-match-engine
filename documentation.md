# 💍 Koota Match Engine: Comprehensive Technical Reference Manual

---

## 1. Executive Overview & System Purpose

The **Koota Match Engine** is an enterprise-grade, high-precision psychometric marital matching system designed specifically for the sociocultural, psychological, and demographic realities of modern Indian matrimony.

Traditional Indian matrimonial systems rely heavily on archaic astrological heuristics (*Ashtakoota* / 36 *Gunas*) or superficial socio-economic filters (caste, salary brackets, physical height). In contrast, the Koota Match Engine models compatibility across **42 scientific Kootas grouped across 14 life pillars**. It couples deterministic hard-filter gatekeepers, vector similarity embeddings, Natural Language Inference (NLI) contradiction screens, multi-provider Large Language Model (LLM) judges, client-side social graph overlap analysis, and an editorial React Native (Expo) mobile experience—all engineered to operate permanently within a **zero-cost ($0.00/month) cloud architecture**.

---

## 2. Full-Stack System Architecture

```mermaid
graph TD
    subgraph Client Application [React Native / Expo SDK 52]
        UI_INVITE[Invite Code Screen] -->|Validate Single-Use Token| API_INVITE[/auth/invite/redeem]
        UI_AUTH[Google OAuth Flow] -->|Exchange Auth Token| API_AUTH[/auth/google/callback]
        UI_ONBOARD[42-Koota Questionnaire] -->|Upsert Objective & Free-Text| API_ANSWERS[/profiles/{id}/answers]
        UI_WEEKLY[Weekly Matches Screen] -->|Constant-Time Cache Read| API_WEEKLY[/profiles/{id}/weekly-matches]
        UI_INTEREST[Express / Decline Interest] -->|Atomic Single-Tap| API_INTEREST[/interest]
        UI_REFRESH[Refresh Matches Button] -->|24h Cooldown Funnel| API_REFRESH[/profiles/{id}/refresh-matches]
        UI_CODE[Compatibility Codes UI] -->|Generate & Exchange Codes| API_CODES[/profiles/{id}/compatibility-check]
    end

    subgraph Backend API Layer [FastAPI + AsyncSQLAlchemy 2.0]
        API_AUTH --> DB_PROFILE[(Supabase Postgres Profiles)]
        API_ANSWERS -->|Write-Time Vector Embedding| HF_EMB[HF MiniLM Embedding Model]
        HF_EMB --> DB_ANSWERS[(Answers & Embedding Tables)]
        
        API_WEEKLY --> DB_WEEKLY[(WeeklyMatchList Table)]
        API_INTEREST -->|Atomic Mutual Flip Service| DB_INTEREST[(Interests Table)]
        API_CODES --> DB_CODES[(CompatibilityCodes Table)]
    end

    subgraph 5-Stage Matching Funnel Pipeline [Batch Runner & On-Demand]
        CRON[Scheduled Weekly Cron / On-Demand Trigger] --> FUNNEL[Funnel Pipeline Engine]
        FUNNEL --> S1[Stage 1: SQL Indexed Hard Filter]
        S1 -->|Age Gap <= 2 yrs + Religion + Caste Req| S2[Stage 2: pgvector / Cosine ANN Retrieval Top 50]
        S2 -->|Koota 41 Life Purpose Embedding| S3[Stage 3: HF BART-MNLI Contradiction Screen Top 10]
        S3 -->|Drop Fundamental Contradictions| S4[Stage 4: Multi-Provider LLM Judge Shortlist Top 10]
        S4 -->|Groq Llama-3.3-70B / OpenRouter / Gemini| S5[Stage 5: Gated Aggregation & Tier Classification]
        S5 --> DB_WEEKLY
    end
```

### Architectural Design Principles
1. **Pipelined Filter-and-Refine Funnel**: Employs monotonically narrowing stages (SQL Hard Filter $\rightarrow$ Vector ANN $\rightarrow$ NLI Contradiction Classifier $\rightarrow$ LLM Judge $\rightarrow$ Gated Aggregator) to minimize computational overhead and stay within strict free-tier rate limits.
2. **Write-Time Heavy, Read-Time Instant (CQRS-lite)**: Expensive transformer embeddings are computed and cached when users submit answers (`POST /profiles/{id}/answers`). Candidate matches are precomputed into `WeeklyMatchList`. User match lookups (`GET /profiles/{id}/weekly-matches`) execute as $O(1)$ constant-time database queries with zero live LLM or transformer invocations.
3. **Multi-Provider Fallback Chain with Circuit Breaking**: The LLM-as-a-Judge subsystem utilizes Groq Llama-3.3-70B as primary, gracefully falling back sequentially to OpenRouter (Nemotron-70B / Gemma-4) and Google Gemini without halting batch runs.
4. **Strict Isolation of Informational Overlap**: Social graph overlap ([`app/matching/social_overlap.py`](file:///d:/Vivah/app/matching/social_overlap.py)) is purely informational. It has 0.00 weight on numeric match scores and zero influence over tier ceilings.
5. **Staged Disclosure & Zero-Knowledge Output Serialization**: Responses never serialize raw free-text answers, sensitive demographic fields (caste, exact income, phone, email), or raw following handles. Unilateral interest states remain completely hidden until mutuality is achieved.
6. **Robust Client-Side Resilience**: Mobile API client features a 30s `AbortController` timeout and automatic 1-time retry on HTTP 502/503/504 cold starts.

---

## 3. Complete Codebase Directory & File Inventory

```text
koota-match-engine/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Full stack CI: Pytest + Jest + TypeScript gates
│       ├── keepalive.yml          # Free-tier keepalive ping workflow (every 3 days)
│       └── weekly-match.yml       # Scheduled Sunday cron precomputing weekly matches
├── app/
│   ├── __init__.py                # App package initialization
│   ├── main.py                    # FastAPI entrypoint, logging middleware, /health probe
│   ├── models.py                  # SQLAlchemy 2.0 ORM domain entities and relationships
│   ├── api/
│   │   ├── __init__.py            # API package initialization
│   │   ├── routes_auth.py         # Invite code validation and Google OAuth endpoints
│   │   ├── routes_following.py    # Opt-in client-extracted social following list endpoints
│   │   ├── routes_interest.py     # Mutual-interest expression, decline, and status routes
│   │   ├── routes_match.py        # Direct pair match scoring and candidate ranking endpoints
│   │   ├── routes_on_demand.py    # On-demand funnel refresh & compatibility code endpoints
│   │   ├── routes_profiles.py     # Profile CRUD, PATCH demographics, 42-Koota answers upsert
│   │   ├── routes_weekly.py       # Constant-time read-only weekly matches API
│   │   └── schemas.py             # Pydantic v2 validation contracts and DTO schemas
│   ├── auth/
│   │   ├── deps.py                # Profile ownership verification (403 gate) & auth dependencies
│   │   ├── google_oauth.py        # Supabase Google OAuth verification and profile mapping
│   │   └── invite.py              # Single-use HMAC-signed invite code lifecycle management
│   ├── db/
│   │   ├── __init__.py            # Database package initialization
│   │   ├── kootas.json            # 42-Koota Question Bank across 14 life pillars
│   │   ├── seed_kootas.py         # Database seeder for initializing all 42 Kootas
│   │   ├── seed_synthetic.py      # Database seeder for 16 edge-case synthetic profiles
│   │   └── session.py             # Async database engine, sessionmaker, and table initializer
│   ├── interest/
│   │   ├── __init__.py            # Interest package initialization
│   │   └── interest_service.py    # Atomic mutual-flip confirmation and staged disclosure service
│   ├── matching/
│   │   ├── batch_runner.py        # Batch runner orchestrating full-pool candidate precomputation
│   │   ├── candidates_batch.py    # Monotonic 5-stage precomputation funnel pipeline
│   │   ├── match_pipeline_service.py # Shared Koota metadata loading & UTC normalization
│   │   └── social_overlap.py      # Pure function Jaccard overlap calculator for following lists
│   └── scoring/
│       ├── __init__.py            # Scoring package initialization
│       ├── aggregate.py           # Gated aggregation math, divergence detection, and veto gates
│       ├── llm_judge.py           # Multi-provider LLM-as-a-Judge subjective evaluation engine
│       ├── nli.py                 # Hugging Face Serverless BART-MNLI contradiction scorer
│       ├── objective.py           # Hard-filter short-circuit and partial credit matrices
│       ├── semantic.py            # Cosine semantic similarity over Hugging Face embeddings
│       └── tiers.py               # 3-tier classification engine with contradiction ceilings
├── mobile/                        # React Native / Expo SDK 52 TypeScript mobile application
│   ├── assets/                    # Production editorial icons, adaptive icons, and splash
│   ├── eas.json                   # EAS build configuration for Android APK and production AAB
│   ├── package.json               # Mobile dependencies & Jest scripts
│   ├── tsconfig.json              # TypeScript strict configuration
│   └── src/
│       ├── api/
│       │   ├── authApi.ts         # Authentication & invite verification API client
│       │   ├── client.ts          # Base Axios client with 30s timeout & cold-start retry
│       │   ├── interestApi.ts     # Interest expression & status API client
│       │   ├── onDemandApi.ts     # On-demand refresh & compatibility code API client
│       │   ├── profileApi.ts      # Profile CRUD, PATCH, & answers upsert API client
│       │   └── weeklyMatchesApi.ts# Read-only weekly matches API client
│       ├── components/
│       │   ├── AlignmentFrictionList.tsx # Editorial alignment & conversation-starter pills
│       │   ├── DeclineConfirmationModal.tsx # Gentle decline confirmation modal
│       │   ├── MatchCard.tsx      # Editorial match card (no photos, pure psychometrics)
│       │   ├── MutualRevealAnimation.tsx # Spring-driven celebration modal on mutual match
│       │   ├── QuestionnaireProgress.tsx # Elegant typography & spring progress bar
│       │   └── RefreshMatchesButton.tsx  # Live countdown cooldown button for funnel refresh
│       ├── context/
│       │   ├── AuthContext.tsx    # Supabase session management & SecureStore integration
│       │   └── QuestionnaireContext.tsx # 42-Koota answer state, draft saving, and batching
│       ├── navigation/
│       │   └── AppNavigator.tsx   # React Navigation stack & tab navigators
│       ├── reducers/
│       │   └── interestReducer.ts # Optimistic single-tap state reducer for match actions
│       ├── screens/
│       │   ├── CompatibilityCodeScreen.tsx # Generate, share, and redeem compatibility codes
│       │   ├── EditProfileScreen.tsx       # Demographic & questionnaire answers edit screen
│       │   ├── HomeScreen.tsx              # Editorial dashboard & match digest
│       │   ├── InviteCodeScreen.tsx        # Single-use invite code gate screen
│       │   ├── LoginScreen.tsx             # Editorial Google OAuth entry point
│       │   ├── ObjectiveQuestionnaireScreen.tsx # Objective multiple-choice questions
│       │   ├── ProfileSetupScreen.tsx      # Basic demographic profile registration
│       │   ├── SubjectiveQuestionnaireScreen.tsx# Free-text reflective answer screen
│       │   └── WeeklyMatchesScreen.tsx     # Precomputed matches list with on-demand refresh
│       ├── styles/
│       │   └── theme.ts           # Warm ivory, terracotta, champagne editorial design tokens
│       └── utils/
│           ├── answerPersistence.ts # Async storage draft persistence for questionnaire
│           └── kootaDefinitions.ts  # Typed definitions of all 42 Kootas and 14 pillars
├── sbom-backend.json              # CycloneDX SBOM for Python backend dependencies
├── sbom-mobile.json               # CycloneDX SBOM for npm mobile dependencies
├── scripts/
│   ├── generate_app_assets.py     # Pillow-based editorial icon and splash generator
│   └── generate_sbom.py           # CycloneDX SBOM generator script
└── tests/                         # Pytest test suite (89 tests)
    ├── test_aggregation.py
    ├── test_api_and_tiers.py
    ├── test_auth.py
    ├── test_candidates_batch.py
    ├── test_compatibility_codes_privacy.py
    ├── test_following_api.py
    ├── test_gated_aggregation.py
    ├── test_hard_filter_field_consistency.py
    ├── test_interest_api.py
    ├── test_interest_service.py
    ├── test_interest_staged_disclosure_e2e.py
    ├── test_llm_judge.py
    ├── test_nli_scorer.py
    ├── test_objective_scorer.py
    ├── test_on_demand_refresh_and_compatibility.py
    ├── test_phase1_scaffolding.py
    ├── test_profile_answers_upsert_and_patch.py
    ├── test_semantic_scorer.py
    ├── test_social_overlap.py
    ├── test_synthetic_matching.py
    └── test_weekly_matches_api.py
```

---

## 4. Complete API Specification

### Authentication & Invite Routes (`/auth`)
- `POST /auth/invite/redeem`: Validate and claim single-use invite code. Returns HMAC-signed onboarding token.
- `POST /auth/google/callback`: Verify Supabase Google OAuth access token, retrieve email and sub, create or return Profile.
- `POST /auth/invite/generate`: Admin endpoint to mint signed single-use invite codes with expiration timestamps.

### Profile & Answers Routes (`/profiles`)
- `POST /profiles`: Create initial demographic profile (Name, Age, Gender, Religion, Caste, Caste Preference, City).
- `GET /profiles/{id}`: Retrieve profile demographics and onboarding status (Ownership verified).
- `PATCH /profiles/{id}`: Partial update of demographics. If `religion`, `caste_preference`, or `caste` change, returns `hard_filter_changed: true` and immediately invalidates `WeeklyMatchList` caches.
- `DELETE /profiles/{id}`: Soft or hard delete of profile, answers, and matches.
- `POST /profiles/{id}/answers`: Explicit atomic **UPSERT** of objective and subjective 42-Koota answers. Automatically triggers background write-time MiniLM embedding generation.
- `GET /profiles/{id}/answers`: Retrieve all submitted answers for the caller.
- `GET /profiles/{id}/completion`: Returns percentage completion across all 14 pillars and 42 Kootas.

### Matching & Funnel Routes (`/profiles`, `/match`)
- `GET /profiles/{id}/weekly-matches`: Read-only constant-time retrieval of Sunday precomputed matches. Returns candidate names, compatibility scores, tier classification, alignment points, friction conversation-starters, and caller-specific interest state. Zero demographics leaked.
- `POST /profiles/{id}/refresh-matches`: On-demand execution of the 5-stage matching funnel for this profile. Gated by a **strict 24-hour cooldown**. Returns HTTP 429 with `next_eligible_at` and `retry_after_seconds` if called before cooldown expiry. Bounded to $\le 10$ LLM judge calls.
- `GET /match/{profile_a_id}/{profile_b_id}`: Real-time debug evaluation of a single pair across all 42 Kootas.
- `GET /match/{id}/candidates`: Developer candidate pool inspection.

### Mutual-Consent Compatibility Codes (`/profiles`)
- `POST /profiles/{id}/compatibility-code`: Generate an unambiguous 6-character alphanumeric code (`23456789ABCDEFGHJKLMNPQRSTUVWXYZ`) with 7-day TTL for sharing with an off-platform partner.
- `POST /profiles/{id}/compatibility-check`: Submit an external partner's compatibility code. Executes a full 42-Koota evaluation and returns the mutual compatibility score and tier. Atomically burns the code (single-use guarantee).
- `GET /profiles/{id}/compatibility-codes`: List active and burned codes generated by the caller.

### Mutual Interest Routes (`/interest`)
- `POST /interest`: Express (`action: "pending"`) or decline (`action: "declined"`) interest in a candidate from `WeeklyMatchList`.
  - **Atomic Mutual Flip**: If both parties express pending interest, both records atomically transition to `mutual` in a single ACID transaction.
- `GET /interest/{profile_id}/status`: Staged-disclosure view of caller's outgoing interest states. A candidate's pending interest remains completely invisible until mutual confirmation.

### Social Following Overlap Routes (`/following`)
- `POST /following/{profile_id}`: Opt-in client-extracted social following list upload (hashed handles).
- `GET /following/{profile_id}`: Retrieve following summary count.
- `DELETE /following/{profile_id}`: Revoke and purge all stored following data.

### System & Health Routes (`/`)
- `GET /health`: Production readiness check. Performs an active `SELECT 1` database query; returns HTTP 200 `{ status: "healthy", database: "healthy" }` or HTTP 503 `{ status: "degraded", database: "unhealthy" }`.
- `GET /`: Service identification and documentation links.

---

## 5. Mobile Application & Editorial UX Architecture

The Koota Match mobile app is built with **React Native / Expo SDK 52, TypeScript, and React Navigation**, following an award-winning editorial aesthetic:

### Editorial Visual Design System
- **Palette**: Warm Ivory (`#FAF7F2`), Terracotta (`#C85A32`), Deep Slate (`#2A2A2A`), Champagne Gold (`#F2EDE4`), Muted Sand (`#E5DFD5`), and Success Pine (`#2D5A43`). Light theme only.
- **Typography**: Editorial serif titles with clean geometric sans-serif body copy, generous whitespace, confident tracking, and balanced line heights.
- **Micro-Animations**: Spring-based physics (`Animated.spring` with friction 7, tension 40) across card reveals, progress updates, and mutual match reveal celebrations.
- **Zero Photo Design**: Eliminates superficial appearance bias; focuses entirely on deep psychometric compatibility and conversation-starter friction points.

### Mobile Feature Implementations
1. **Invite-Gated Authentication**: `InviteCodeScreen` validates single-use HMAC invite tokens before directing users to Google OAuth in `LoginScreen`. Tokens are safely stored in `expo-secure-store`.
2. **42-Koota Questionnaire Engine**: Fluid questionnaire splitting objective choices and reflective subjective inputs with auto-draft persistence (`answerPersistence.ts`).
3. **Optimistic Mutual Interest UI**: `interestReducer.ts` handles instant single-tap state updates on `MatchCard`, rolling back gracefully if network requests fail.
4. **Mutual Match Celebration Modal**: `MutualRevealAnimation.tsx` renders a spring-driven modal celebration when a match flips to mutual status.
5. **Live Cooldown Refresh Button**: `RefreshMatchesButton.tsx` tracks server-side cooldown expiration with real-time remaining countdown (e.g. `Next refresh in 14h 22m`).
6. **Edit Profile with Pre-Save Warning**: `EditProfileScreen.tsx` alerts users before saving if their edits will invalidate their existing weekly match digest.

---

## 6. Mathematical Scoring & 5-Stage Funnel Pipeline

$$\text{Final Aggregate Score} = \sum_{k=1}^{42} \left( \text{Normalized Weight}_k \times S_k \right) \times \prod_{g \in \text{Veto Gates}} \text{Multiplier}_g$$

### Funnel Stage Breakdown
1. **Stage 1 — SQL Indexed Hard Filters**:
   - Age gap: $|\text{Age}_A - \text{Age}_B| \le 2\text{ years}$.
   - Religion: $\text{Religion}_A == \text{Religion}_B$.
   - Caste: If either requires same caste, $\text{Caste}_A == \text{Caste}_B$.
2. **Stage 2 — Vector ANN Embedding Retrieval (pgvector)**:
   - Cosine similarity over Koota 41 (Life Purpose & Marriage Philosophy) Hugging Face `all-MiniLM-L6-v2` embeddings retrieves Top 50 candidates.
3. **Stage 3 — NLI Contradiction Screening (BART-MNLI)**:
   - Evaluates premise/hypothesis contradiction probabilities on subjective answers. Candidates with fundamental contradictions ($> 0.85$ contradiction probability) receive capped scores ($\le 0.45$) and are filtered out.
4. **Stage 4 — Multi-Provider LLM-as-a-Judge**:
   - Shortlisted Top 10 pairs undergo deep psychological compatibility evaluation via Groq Llama-3.3-70B (with fallback to OpenRouter & Gemini). Generates nuanced alignment points and conversation-starter friction points.
5. **Stage 5 — Gated Aggregation & Tier Classification**:
   - Applies weighted pillar math and assigns final tiers:
     - **Strong Match**: Score $\ge 0.80$, zero critical contradictions.
     - **Compatible with Flagged Friction Points**: Score $0.65 - 0.79$.
     - **Not Viable**: Score $< 0.65$ or failed veto gate (never shown in weekly digest).

---

## 7. The 42 Kootas Across 14 Life Pillars

| Pillar ID | Pillar Name | Weight Range | Koota IDs | Core Focus |
|:---|:---|:---|:---|:---|
| **Pillar A** | Career, Ambition & Geography | $w6$–$w12$ | 1, 2, 3 | Geographic relocation willingness, career priority balance, travel rhythm. |
| **Pillar B** | Financial Architecture & Philosophy | $w8$–$w14$ | 4, 5, 6, 7 | Debt philosophy, joint vs separate accounts, risk tolerance, parental support obligations. |
| **Pillar C** | Family Systems & Boundary Dynamics | $w8$–$w14$ | 8, 9, 10 | Co-living with in-laws, parental involvement in conflict, elderly care distribution. |
| **Pillar D** | Children, Parenting & Legacy | $w10$–$w15$ | 11, 12, 13 | Desired number of children, timeline, schooling philosophy, religious upbringing. |
| **Pillar E** | Conflict Architecture & Communication | $w8$–$w14$ | 14, 15, 16, 17 | Conflict resolution style (cool-down vs immediate), repair speed, apologies. |
| **Pillar F** | Household Labor & Operational Symmetry | $w6$–$w10$ | 18, 19, 20 | Domestic chore division, cooking responsibilities, outsourced domestic help. |
| **Pillar G** | Emotional Processing & Vulnerability | $w8$–$w12$ | 21, 22, 23 | Emotional expression comfort, stress decompression needs, deep listening habits. |
| **Pillar H** | Social Life, Independence & Friendships | $w4$–$w8$ | 24, 25 | Solo time necessity, friend group integration, weekend social battery. |
| **Pillar I** | Spirituality, Faith & Rituals | $w6$–$w12$ | 26, 27, 28 | Daily spiritual practice, festival celebration intensity, dietary religious strictness. |
| **Pillar J** | Intimacy, Affection & Romance | $w8$–$w12$ | 29, 30 | Pre-marital emotional intimacy dialogue, daily physical non-sexual affection. |
| **Pillar K** | Health, Wellness & Lifestyle | $w4$–$w8$ | 31, 32, 33 | Dietary habits (vegetarian/non-veg), fitness discipline, sleep schedule synchronization. |
| **Pillar L** | Crisis Resilience & Adaptability | $w8$–$w12$ | 34, 35, 36, 37 | Substance usage habits, reaction to sudden career loss, grief support style. |
| **Pillar M** | Shared Meaning & Life Purpose | **$w14$–$w15$** | 38, 39, 40, 41 | **Existential coping, 10-year life vision, fundamental purpose of marriage.** |
| **Pillar N** | Hard Demographics & Community | **Filter / $w1$** | 42 | Age gap ceiling ($\le 2$ yrs), religion match, community/caste requirements. |

---

## 8. Verification & Automated Test Infrastructure

The codebase enforces full-stack automated testing across backend unit/integration tests and mobile component/reducer tests:

### Backend Pytest Suite (**89 passed**, 0 failed)
```bash
pytest -v
```
- Scaffolding & Seed verification (`test_phase1_scaffolding.py`): 3 tests.
- Scorer & Judge units (`test_objective_scorer.py`, `test_semantic_scorer.py`, `test_nli_scorer.py`, `test_llm_judge.py`): 21 tests.
- Social graph overlap isolation (`test_social_overlap.py`, `test_following_api.py`): 10 tests.
- Interest service & staged-disclosure E2E (`test_interest_service.py`, `test_interest_api.py`, `test_interest_staged_disclosure_e2e.py`): 12 tests.
- Batch & On-Demand funnel verification (`test_candidates_batch.py`, `test_on_demand_refresh_and_compatibility.py`): 9 tests.
- Hard-filter consistency & answers upsert (`test_hard_filter_field_consistency.py`, `test_profile_answers_upsert_and_patch.py`): 8 tests.
- Compatibility code privacy & boundaries (`test_compatibility_codes_privacy.py`): 4 tests.
- Synthetic pool edge cases (`test_synthetic_matching.py`): 6 tests.
- Complete API & Tier validations (`test_api_and_tiers.py`, `test_auth.py`, `test_weekly_matches_api.py`): 16 tests.

### Mobile Jest Suite (**17 test suites, 55 passed**, 0 failed)
```bash
cd mobile && npm test -- --watchAll=false
```
- Component tests: `MatchCard.test.tsx`, `AlignmentFrictionList.test.tsx`, `DeclineConfirmationModal.test.tsx`, `MutualRevealAnimation.test.tsx`, `RefreshMatchesButton.test.tsx`.
- Screen tests: `WeeklyMatchesScreen.test.tsx`, `CompatibilityCodeScreen.test.tsx`, `EditProfileScreen.test.tsx`, `InviteCodeScreen.test.tsx`, `LoginScreen.test.tsx`, `ProfileSetupScreen.test.tsx`, `ObjectiveQuestionnaireScreen.test.tsx`, `SubjectiveQuestionnaireScreen.test.tsx`.
- Reducer & context tests: `interestReducer.test.ts`, `AuthContext.test.tsx`, `QuestionnaireContext.test.tsx`, `authApi.test.ts`.

### TypeScript Typecheck (**0 errors**)
```bash
cd mobile && npx tsc --noEmit
```

---

## 9. Security, Supply Chain & Privacy Audit

1. **Zero-Knowledge Match Serialization**: Responses never leak raw free-text answers, raw following handles, phone numbers, or unconsented demographics.
2. **Ownership Verification (403 Gates)**: Enforced via `verify_profile_ownership` dependency across all private/mutating routes (`PATCH/DELETE /profiles/{id}`, `/answers`, `/weekly-matches`, `/refresh-matches`, `/compatibility-code`, `/compatibility-check`, `/following`, `/interest`).
3. **Secrets Management**: Zero hardcoded keys or API tokens. Secrets are passed via runtime environment variables and GitHub Action secrets.
4. **Supply Chain BOM**: CycloneDX-standard Software Bill of Materials generated for both backend ([`sbom-backend.json`](file:///d:/Vivah/sbom-backend.json)) and mobile ([`sbom-mobile.json`](file:///d:/Vivah/sbom-mobile.json)).
5. **Cold-Start & Rate Limit Protection**: Sliding window rate-limiters prevent exceeding free LLM quotas, while client-side retry protects mobile users against platform cold starts.

---

## 10. Deployment, CI/CD & Build Runbook

### Local Development Setup

#### Backend Setup:
```bash
git clone https://github.com/yashwoodstock-blip/koota-match-engine.git
cd koota-match-engine

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Seed 42 Kootas and 16 Synthetic Profiles
python -m app.db.seed_kootas
python -m app.db.seed_synthetic

# Run FastAPI Local Server
uvicorn app.main:app --reload --port 8000
```

#### Mobile Setup:
```bash
cd mobile
npm install
npx expo start
```

### EAS Android Build Generation
Build configuration is located in [`mobile/eas.json`](file:///d:/Vivah/mobile/eas.json):
```bash
# Build standalone Android APK for device testing
cd mobile
npx eas-cli build --platform android --profile preview

# Build production Android App Bundle (AAB) for Google Play
npx eas-cli build --platform android --profile production
```

### CI/CD Workflow
Located at [`.github/workflows/ci.yml`](file:///d:/Vivah/.github/workflows/ci.yml). Automatically triggers on every push and pull request to `main`:
- Job 1: Sets up Python 3.12, installs dependencies, and runs full 89-test Pytest suite.
- Job 2: Sets up Node.js 20, runs TypeScript typecheck (`tsc --noEmit`), and executes all 55 Jest unit tests.

---

## 11. Version History & Changelog

- **v1.0.0 (Phases 1–5)**: 42-Koota Question Bank, objective partial credit matrices, MiniLM vector caching, BART-MNLI contradiction scoring, Groq Llama-3.3-70B judge, and 3-tier classification.
- **v1.1.0 (Phase 6)**: Invite-only Google OAuth gate and scheduled Sunday precomputed weekly match funnel.
- **v1.2.0 (Phase 7)**: Opt-in client-extracted social following list Jaccard overlap signal (strictly isolated).
- **v1.3.0 (Phase 8)**: Mutual-interest confirmation, single-transaction atomic flip, and staged disclosure privacy rules.
- **v1.4.0 (Phase 9 & 10)**: React Native Expo mobile app, Google OAuth authentication flow, `expo-secure-store` integration, and editorial 42-Koota onboarding questionnaire.
- **v1.5.0 (Phase 11 & 11.5)**: Weekly Matches screen, Match Cards, optimistic interest reducer, celebration reveal animation, and Edit Profile & Answers screen with match reset warnings.
- **v1.6.0 (Addenda)**: On-demand Funnel Refresh with 24-hour rate limit cooldown and Mutual-Consent Compatibility Codes with 7-day TTL and zero raw data leaks.
- **v1.7.0 (Hardening & Pre-Deployment Audit)**: Architecture refactoring into `match_pipeline_service`, ownership verification on all routes, structured logging middleware, live DB health probe, CycloneDX SBOM generation, EAS build profile, and multi-job CI workflow.
