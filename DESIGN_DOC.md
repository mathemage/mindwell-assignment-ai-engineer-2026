# Mindwell AI — Clinical Supervisor: Design Document

> **Submission for:** AI Engineer Case Study — Mindwell  
> **Format:** Markdown (primary) · PDF export (backup)  
> **Diagrams:** `diagrams/architecture.drawio` (Draw.io)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [A. System Architecture & Stack](#a-system-architecture--stack)
3. [B. Data Privacy & Observability](#b-data-privacy--observability)
4. [C. Security & Isolation](#c-security--isolation)
5. [D. User Experience (Thought Process)](#d-user-experience-thought-process)
6. [E. Strategic Thinking](#e-strategic-thinking)
7. [Technology Decisions Summary](#technology-decisions-summary)

---

## Executive Summary

Mindwell's **Clinical Supervisor** is a Human-in-the-Loop AI system that assists therapists by analyzing patient journal entries and CBT homework, consulting a curated CBT Knowledge Base (KB), and drafting a clinical response for therapist review and approval.

The architecture is built around five principles:

| Principle | How it is expressed in this design |
|---|---|
| **Safety First** | Every message passes through a SafetyAgent (input _and_ output) before any LLM call or delivery |
| **Data Sovereignty** | All components run inside a single VPC; no patient data is sent to public SaaS |
| **Long-Term Memory** | Patient-level vector memory stored in PostgreSQL with `pgvector`; persists across sessions |
| **Lean & Open-Source** | Self-hosted PostgreSQL, pgvector, OpenTelemetry stack — no expensive enterprise licences |
| **Therapist in the Loop** | The LLM _drafts_; the therapist _approves_; the system _never_ autonomously delivers clinical responses (Therapist Review UI is a planned component) |

The full system diagram is in [`diagrams/architecture.drawio`](diagrams/architecture.drawio).

---

## A. System Architecture & Stack

### A.1 High-Level Flow

```
Patient submits journal / homework
        │  HTTPS (TLS 1.3)
        ▼
┌──────────────────────────────────────────┐
│              VPC Boundary                │
│                                          │
│  ┌─────────────────────────────────┐     │
│  │   FastAPI Backend (API Layer)   │     │
│  │  Auth · Chat · Admin endpoints  │     │
│  └───────────────┬─────────────────┘     │
│                  │                       │
│  ┌───────────────▼─────────────────┐     │
│  │  PII Redaction & Safety Pre-    │     │
│  │  check (before LLM context)     │     │
│  └───────────────┬─────────────────┘     │
│                  │ Redacted message       │
│  ┌───────────────▼─────────────────┐     │
│  │       ChatOrchestrator          │     │
│  │  (Multi-Agent Pipeline)         │     │
│  │                                 │     │
│  │  1. SafetyAgent (input)         │     │
│  │  2. RetrieverAgent (RAG)        │     │
│  │  3. DraftAgent (LLM)            │     │
│  │  4. SafetyAgent (output)        │     │
│  │  5. FinalizerAgent (citations)  │     │
│  └───────────────┬─────────────────┘     │
│                  │ Draft response         │
│  ┌───────────────▼─────────────────┐     │
│  │  Therapist Review UI  [Planned] │     │
│  │  (Approve / Edit / Reject)      │     │
│  └─────────────────────────────────┘     │
│                                          │
│  ┌────────────┐  ┌────────────────────┐  │
│  │ PostgreSQL │  │  CBT Knowledge Base│  │
│  │ + pgvector │  │  (Chunks+Embeddings│  │
│  └────────────┘  └────────────────────┘  │
└──────────────────────────────────────────┘
        │
        ▼
  Approved response delivered to patient
```

> See `diagrams/architecture.drawio` for the annotated Draw.io version of this diagram.

### A.2 Agent Structure

The pipeline is an **orchestrator-based multi-agent** design (not a graph-based LangGraph approach, but fully compatible with one):

| Agent | Responsibility | Technology |
|---|---|---|
| **SafetyAgent** | Detects crisis, self-harm, medical-advice requests; runs on _both_ input and LLM output | Regex pattern engine (`re`); extensible to ML classifiers |
| **RetrieverAgent** | Queries the CBT Knowledge Base using vector similarity; returns top-k chunks with citations | `pgvector` cosine similarity, configurable k and threshold |
| **DraftAgent** | Constructs the prompt (system prompt + retrieved context + patient message) and calls the LLM | OpenAI-compatible interface; swappable for Ollama / vLLM |
| **FinalizerAgent** | Assembles citations, safety metadata, and the draft into the final structured payload | Pure Python, no LLM call |
| **ChatOrchestrator** | Coordinates the four agents above; handles short-circuit exits on safety blocks | Synchronous pipeline; async upgrade path available |

**Why not LangGraph?**  
LangGraph is excellent for complex, cyclical multi-agent graphs. For this MVP the pipeline is strictly linear (no cycles, no parallel branches). A hand-rolled orchestrator is simpler to reason about, cheaper to run, and has fewer dependencies. If the product evolves to require parallel sub-agents (e.g., a risk-scoring agent running concurrently with retrieval), LangGraph would be the natural upgrade — and the agent interface used here is compatible with that migration.

### A.3 Memory Store

**Choice: PostgreSQL 16 with the `pgvector` extension**

| Requirement | How PostgreSQL + pgvector satisfies it |
|---|---|
| Self-hostable | Docker image `pgvector/pgvector:pg16`; runs in any VPC |
| Long-term patient facts | Rows in `conversations` and `messages` tables survive restarts |
| Vector similarity search | `pgvector` extension provides `<=>` cosine distance operator with IVFFlat/HNSW indexes |
| Structured metadata | Relational tables for users, conversations, safety logs, eval runs |
| Open Source | PostgreSQL is BSD-licensed; pgvector is MIT |
| Cost | $0 licence cost; fits on a $50/month cloud VM for MVP scale |

**Schema overview:**

```
users ──< conversations ──< messages
                │
                └──< safety_logs
documents ──< chunks ──< embeddings (vector column)
```

Patient-level long-term memory is expressed as the full `messages` history for a `conversation`, combined with an optional `patient_facts` table (key-value facts extracted by a future MemoryExtractorAgent). When the RetrieverAgent is invoked, it queries _both_ the CBT KB embeddings _and_ the patient facts store, giving the LLM memory of previous sessions.

### A.4 Persistence Strategy (In-Memory → Disk)

PostgreSQL is a disk-backed store by default — there is no "in-memory only" risk. The persistence strategy is:

1. **Docker Volume (`postgres_data`):** the database data directory is mounted as a named Docker volume, surviving container restarts.
2. **Write-Ahead Log (WAL):** PostgreSQL's WAL guarantees that committed transactions survive crashes.
3. **Daily pg_dump backups** to an encrypted S3/GCS bucket (outside VPC — write-only IAM role).
4. **Point-In-Time Recovery (PITR):** WAL archiving to object storage enables recovery to any second.
5. **Connection pooling (PgBouncer):** limits connection overhead without sacrificing durability.

If a Redis in-memory cache is added later (e.g., for embedding cache), the same pattern applies: Redis is configured with `appendonly yes` (AOF) and snapshotting (`RDB`) so that a container crash loses at most one second of data.

---

## B. Data Privacy & Observability

### B.1 "Black Box" Problem — Data Before the LLM

Patient text travels through three privacy layers before it reaches the LLM context window:

```
Raw patient text
      │
      ▼ 1. PII Detection (regex: email, phone, SSN)
Redacted text  [EMAIL_REDACTED], [PHONE_REDACTED], [SSN_REDACTED]
      │
      ▼ 2. Pseudonymised user identity
Prompt includes pseudonym (SHA-256 hash[:16]) — never the real user ID
      │
      ▼ 3. System-prompt scoping
LLM receives only: system_prompt + CBT_context_chunks + redacted_patient_text
(No other patient's data; no raw PII)
      │
      ▼
LLM generates draft response
```

Code reference: `backend/app/core/security.py` (PII detection), `backend/app/services/chat_service.py` (redaction before storage and LLM call).

### B.2 Self-Hosted Tracing

**Recommended stack: OpenTelemetry + Jaeger (self-hosted)**

> **Implementation status**: `structlog` structured JSON logging is implemented today (`backend/app/core/logging.py`). The OpenTelemetry Collector, Jaeger, and Prometheus/Grafana components are **planned** — they are not yet in the `docker-compose.yml` or codebase. The table below describes the target architecture.

| Tool | Role | Why self-hosted? |
|---|---|---|
| **OpenTelemetry Collector** | Receives traces/metrics/logs from the FastAPI app via OTLP | Vendor-neutral; works inside VPC |
| **Jaeger** | Distributed trace storage and UI | Apache 2.0 licence; Docker Compose deployable; no data leaves VPC |
| **Prometheus + Grafana** | Metrics (latency, error rate, safety decision distribution) | De-facto open-source standard; self-hosted |
| **structlog** | Structured JSON logging with automatic PII redaction (**implemented**) | Python-native; logs stay on the host |

**Debugging a hallucination session:**

1. Find the `conversation_id` from the therapist complaint.
2. In Jaeger, search traces by `conversation_id`. Each agent step is a span:  
   `SafetyAgent.check_input` → `RetrieverAgent.execute` → `DraftAgent.execute` → `SafetyAgent.check_output` → `FinalizerAgent.execute`
3. Inspect the `RetrieverAgent` span: what chunks were retrieved? What was the similarity score?
4. Inspect the `DraftAgent` span: what was the exact prompt sent to the LLM, and what was the raw response?
5. If the retrieved chunks were irrelevant (low similarity), the root cause is a retrieval quality issue — tune the similarity threshold or re-embed the KB.
6. If chunks were correct but the LLM still hallucinated, the root cause is a prompt issue — harden the system prompt or add a grounding assertion step.

### B.3 Drift Detection — CBT Protocol Compliance

**Monitor the following signals over time:**

| Signal | How to measure | Alert threshold |
|---|---|---|
| **Crisis escalation rate** | `safety_logs` WHERE reason_code = 'crisis_detected' / total messages | > 2σ above 30-day baseline |
| **Medical refusal rate** | `safety_logs` WHERE reason_code = 'medical_advice' | Sharp drop may mean guardrails degraded |
| **Citation coverage** | % of responses with ≥1 citation | < 80% triggers review |
| **LLM tone embedding drift** | Embed each LLM response; compute centroid distance from a "golden" CBT corpus | Cosine distance > 0.15 from baseline |
| **Therapist edit rate** | % of draft responses the therapist modifies before approving | Rising edit rate signals degrading quality |

The **tone embedding drift** metric is the most powerful: we maintain a frozen set of ~200 therapist-approved "gold" responses. Each new response is embedded and its cosine similarity to the gold centroid is logged. A monitoring alert fires when a 7-day rolling average drifts below a threshold, triggering a prompt/model review. (This requires Prometheus + Grafana to be deployed, which is part of the planned observability stack.)

---

## C. Security & Isolation

### C.1 Tenant Isolation — Patient A vs Patient B

Isolation is enforced at **three independent layers** (layer 1 is implemented; layers 2 and 3 are planned for production hardening):

| Layer | Mechanism | Status |
|---|---|---|
| **Application** | Every database query is scoped by `user_id`. The API validates the JWT token and extracts the `user_id`; all ORM queries include `WHERE conversation.user_id = :user_id`. No cross-user query is possible without a code change. | ✅ Implemented |
| **Row-Level Security (RLS)** | PostgreSQL RLS policies (`CREATE POLICY … USING (user_id = current_setting('app.current_user_id'))`) enforce isolation at the database level, so even a SQL injection bypass at the ORM layer cannot return another patient's rows. | 🔲 Planned — not yet in migrations |
| **Vector store scoping** | Each `embedding` row has a foreign key to `chunk → document`. In the current MVP the knowledge base is shared (CBT documents are not patient-specific), and patient conversation history is isolated by `user_id` at the conversation level. Full `tenant_id`-based document namespacing (for multi-organisation deployments) is a planned enhancement. | 🔲 Planned for multi-org |

### C.2 VPC Security — Agent Container ↔ Database Container

```
Internet
   │  (blocked by Security Group)
   │
 [ALB / API Gateway]  ── TLS 1.3 ──►  [Backend Container]
                                              │
                                    Private Subnet (no public IP)
                                              │
                                    [PostgreSQL Container]
                                    (port 5432, internal only)
```

Specific controls:

- **Network**: PostgreSQL is bound to `127.0.0.1` in Docker Compose (`ports: "127.0.0.1:5432:5432"`); in production it is in a private subnet with no internet route.
- **Security Groups (AWS) / Network Security Groups (Azure)**: PostgreSQL SG only accepts inbound 5432 from the Backend SG — no other source.
- **TLS on the DB connection**: `DATABASE_URL` uses `sslmode=require`; the PostgreSQL server presents a self-signed cert signed by the internal CA.
- **Secrets**: `DATABASE_URL`, `OPENAI_API_KEY`, `SECRET_KEY` are injected via AWS Secrets Manager / HashiCorp Vault at runtime — never committed or logged.
- **Principle of least privilege**: the application DB user has `SELECT, INSERT, UPDATE, DELETE` on application tables only; `CREATE`/`DROP` rights are granted only to the migration user during `alembic upgrade head`.

---

## D. User Experience (Thought Process)

### D.1 Intelligence vs. Speed Trade-off

| Option | Latency | Intelligence |
|---|---|---|
| Single LLM call (no RAG) | ~1–2 s | Low — no KB grounding, more hallucinations |
| RAG + single LLM call | ~3–5 s | High — grounded, cited |
| Multi-step agent loop (3+ LLM calls) | ~8–15 s | Very high — but rarely necessary for this task |

**Decision:** Keep the pipeline to a **single LLM call** (the DraftAgent). The safety checks and finalizer are deterministic/fast. The RAG retrieval (~0.2 s for pgvector cosine search on 10 k chunks) is the second biggest cost. Total end-to-end budget: **< 5 seconds** for the happy path.

Reserve multi-step loops (e.g., a self-correction agent that re-checks its own response against CBT principles) for asynchronous background quality scoring, not the real-time path.

### D.2 Handling 3-Second Memory Retrieval

If memory retrieval grows to 3 seconds (e.g., 1 M+ chunks), use **progressive disclosure**:

```
1. API immediately returns HTTP 202 Accepted + job_id
2. Backend streams partial results via Server-Sent Events (SSE):
   - 0.0 s  →  "Analysing your journal entry…"  (UI spinner)
   - 0.5 s  →  Safety check passed (UI checkmark)
   - 1.0 s  →  Retrieved 5 relevant CBT principles (UI shows sources)
   - 3.0 s  →  Draft response ready  (UI displays draft)
3. Therapist sees a "snappy" UI that communicates progress, not a blank screen
```

Additional tactics:
- **Async embedding lookup**: run embedding generation for the new message and vector search concurrently using `asyncio.gather`.
- **Warm query cache**: cache the top-20 most common CBT query embeddings in Redis (TTL 1 hour) to skip vector search for routine questions.
- **Pre-fetch on session open**: when the therapist opens a patient session, trigger a background fetch of that patient's recent memory facts so they are ready when the first message arrives.

---

## E. Strategic Thinking

### E.1 Top 3 Questions for the Product/Clinical Team

**1. What is the exact scope of "patient memory" required by clinicians?**  
Should the AI remember _every_ message (full history), or only _extracted facts_ ("patient reported work anxiety on 2026-01-15")? Full history is cheaper to implement but costly in tokens; fact extraction is more expensive to build but produces a compact, auditable memory. The answer determines whether we build a MemoryExtractorAgent now or defer it.

**2. What is the therapist's approval workflow — inline edit or separate review queue?**  
The architecture supports both: (a) real-time inline editing where the therapist sees the draft and edits before sending, or (b) an async queue where drafts accumulate and therapists batch-review them. Option (b) decouples response latency from the therapist's schedule but changes the patient UX significantly. This decision drives the Therapist Review UI design and whether we need a task queue (Celery/RQ).

**3. Which regulatory framework applies — HIPAA, GDPR, both, or local equivalents?**  
This determines: encryption-at-rest requirements, data residency (single region vs. multi-region), Business Associate Agreement needs with OpenAI (or mandate for a self-hosted LLM), audit log retention periods, and whether a Data Protection Officer is required. Building the wrong compliance posture from day one is expensive to retrofit.

### E.2 The "AI-First" Pivot — Fully Autonomous AI Therapy

#### What changes architecturally

| Component | With therapist in loop (current) | Fully autonomous |
|---|---|---|
| **FinalizerAgent** | Packages draft for therapist approval | Directly delivers approved response to patient |
| **Safety gates** | Regex patterns + therapist as final check | Multi-layer: regex + ML classifier + rule engine + clinical protocol validator |
| **Escalation path** | Notify therapist | Notify on-call human responder OR call emergency services API |
| **Audit trail** | Safety logs, therapist edits | Immutable append-only audit log (WORM) for every decision — required for liability |
| **Model governance** | Monthly prompt review | Continuous automated drift detection + shadow model comparison + A/B testing framework |
| **Consent & explainability** | Therapist implicitly reviews | Patient must consent; every response must be explainable ("This recommendation comes from CBT principle X, source Y") |

#### What we would have built differently from Day 1

1. **Immutable audit log from day one** — every LLM call, every safety decision, every message delivery logged to an append-only store (AWS QLDB / immudb). Retrofitting this is painful.
2. **ML-based safety classifier, not just regex** — regex patterns miss paraphrased crisis signals. A fine-tuned classifier (e.g., DeBERTa on mental health crisis datasets) would be the safety layer. Training data curation starts on day one.
3. **Self-hosted LLM from day one** — for international markets, sending any patient data to OpenAI is likely non-compliant. A self-hosted model (Llama-3 / Mistral via vLLM) inside the VPC would be the default. The `LLMProvider` interface in `backend/app/llm/provider.py` is already designed to be swappable — we would have prioritised the vLLM/Ollama implementation earlier.
4. **Explainability layer** — each response would include a structured rationale: "This response applies the CBT technique of [Cognitive Restructuring] because the patient's message contains [cognitive distortion pattern X]". This requires a separate ExplainerAgent and a structured output schema.

---

## Technology Decisions Summary

| Category | Technology | Rationale |
|---|---|---|
| **Orchestration** | Hand-rolled orchestrator (LangGraph-compatible interface) | Linear pipeline; simpler than graph for MVP; easy to migrate |
| **LLM** | OpenAI GPT-4 (swappable to vLLM/Ollama) | Quality for MVP; `LLMProvider` abstraction enables self-hosted swap |
| **Vector Store** | PostgreSQL 16 + pgvector | Self-hostable, BSD/MIT licence, zero extra DB, relational + vector in one |
| **Embeddings** | OpenAI `text-embedding-3-small` | 1536-dim, excellent quality/cost; swappable to `sentence-transformers` |
| **Framework** | FastAPI + Pydantic v2 | Async-ready, auto-docs, strong typing |
| **Tracing** | OpenTelemetry + Jaeger | Self-hosted, CNCF standard, no SaaS required **(planned)** |
| **Metrics** | Prometheus + Grafana | Open source, VPC-native, industry standard **(planned)** |
| **Logging** | structlog (JSON) | Structured, PII-aware redaction built in |
| **Auth** | JWT (HS256) + bcrypt | Simple, stateless, production-sufficient for MVP |
| **Containerisation** | Docker + Docker Compose | Single-command local dev; Kubernetes-ready for production |
| **Secrets** | Environment variables → AWS Secrets Manager (prod) | Never committed; rotatable |
| **CI/CD** | GitHub Actions | Lint + typecheck + test + security scan on every PR |

---

*Document version: 1.0 — 2026-02-20*  
*Author: AI Engineer Candidate*  
*Diagrams: [`diagrams/architecture.drawio`](diagrams/architecture.drawio)*
