# Mindwell AI - Architecture Documentation

## Overview

Mindwell AI is a production-ready MVP for Cognitive Behavioral Therapy (CBT) digital assistance. It provides an AI-powered chat interface with strong safety guardrails, privacy protection, and citation-based responses grounded in an approved knowledge base.

## System Architecture

```
┌─────────────┐
│   Client    │
│  (User/UI)  │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────────┐
│         FastAPI Backend             │
├─────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐        │
│  │   Auth   │  │   Chat   │        │
│  │   API    │  │   API    │        │
│  └────┬─────┘  └────┬─────┘        │
│       │             │               │
│  ┌────▼─────────────▼──────┐       │
│  │   Chat Orchestrator     │       │
│  │  (Multi-Agent Pipeline) │       │
│  └────┬───────────────┬────┘       │
│       │               │             │
│  ┌────▼────┐    ┌────▼────┐       │
│  │ Safety  │    │   RAG   │       │
│  │ Module  │    │  System │       │
│  └─────────┘    └────┬────┘       │
│                      │             │
│  ┌───────────────────▼────┐       │
│  │    LLM Provider        │       │
│  │  (OpenAI Compatible)   │       │
│  └────────────────────────┘       │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────┐
│   PostgreSQL + PG    │
│      Vector          │
└──────────────────────┘
```

## Core Components

### 1. API Layer (`app/api/`)

**Purpose:** Handle HTTP requests and responses

**Components:**
- `routes/auth.py`: Authentication (login, register, user info)
- `routes/chat.py`: Chat message processing
- `routes/admin.py`: Document management for admins
- `schemas.py`: Pydantic models for request/response validation
- `deps.py`: Dependency injection (auth, database sessions)

**Key Features:**
- JWT-based authentication
- Role-based access control (user vs admin)
- Request validation with Pydantic
- Structured error responses

### 2. Multi-Agent Pipeline (`app/agents/`)

**Purpose:** Orchestrate the chat processing workflow

**Agents:**

1. **RetrieverAgent**: Queries the knowledge base using vector similarity search
2. **DraftAgent**: Generates response using LLM and retrieved context
3. **SafetyAgent**: Checks input and output for safety issues
4. **FinalizerAgent**: Adds citations and metadata to response

**Orchestrator Flow:**
```
User Query
    ↓
Safety Check (Input)
    ↓
Retrieve Context
    ↓
Draft Response (LLM)
    ↓
Safety Check (Output)
    ↓
Finalize with Citations
    ↓
Return to User
```

### 3. RAG System (`app/rag/`)

**Components:**

- **Chunking** (`chunking.py`):
  - Markdown: Split by headings
  - Text: Split by size with sentence boundaries
  - Configurable chunk size (default: 1000 chars) and overlap (default: 200 chars)

- **Embeddings** (`embeddings.py`):
  - OpenAI text-embedding-3-small (1536 dimensions)
  - Batch processing with retry logic
  - Vector storage in PostgreSQL with pgvector

- **Retrieval** (`retrieval.py`):
  - Cosine similarity search
  - Top-k results (default: 5)
  - Similarity threshold filtering (default: 0.7)
  - Citation generation from metadata

### 4. LLM Integration (`app/llm/`)

**Provider Interface:**
- Abstraction for different LLM providers
- OpenAI implementation with retry logic
- Structured response support (JSON mode)

**Prompts:**
- System prompt with CBT context and safety rules
- Chat prompt template with context injection
- Citation requirements built into prompts

### 5. Safety Module (`app/safety/`)

**Policy Enforcement:**

- **Crisis Detection**: Suicide, self-harm, imminent danger
- **Medical Advice Boundary**: Refuse diagnosis/prescription requests
- **PII Protection**: Detect and redact email, phone, SSN
- **Decision Logging**: Track all safety decisions with reason codes

**Safety Outcomes:**
- `OK`: Safe to proceed
- `REFUSED`: Request declined with explanation
- `ESCALATED`: Crisis detected, provide emergency resources

### 6. Database Layer (`app/db/`)

**Models:**

- **User**: Authentication and pseudonymized identity
- **Document**: Knowledge base documents
- **Chunk**: Document segments for retrieval
- **Embedding**: Vector representations
- **Conversation**: Chat sessions
- **Message**: Individual chat messages
- **SafetyLog**: Audit trail for safety decisions
- **EvaluationRun**: Metrics tracking

**Key Features:**
- SQLAlchemy 2.0 with async support readiness
- Alembic migrations
- Cascade deletes for data integrity
- pgvector extension for similarity search

### 7. Services Layer (`app/services/`)

**DocumentService:**
- Process documents (markdown, PDF, text)
- Generate chunks and embeddings
- Reindex existing documents
- CRUD operations

**ChatService:**
- Manage conversations
- Store messages with metadata
- PII detection and redaction
- Safety logging

### 8. Core Utilities (`app/core/`)

- **Config**: Environment-based settings
- **Logging**: Structured JSON logging with PII redaction
- **Security**: JWT, password hashing, PII detection
- **Errors**: Custom exception hierarchy

## Data Flow Examples

### Chat Request Flow

```
1. User sends message
2. API validates JWT token
3. ChatService retrieves/creates conversation
4. PII detection and redaction on user message
5. Store user message in database
6. ChatOrchestrator processes:
   a. Safety check input
   b. Retrieve relevant chunks
   c. Draft response with LLM
   d. Safety check output
   e. Finalize with citations
7. Store assistant message
8. Log safety decision
9. Return response to user
```

### Document Upload Flow

```
1. Admin uploads document (file or text)
2. API validates admin role
3. Extract text (PDF → text extraction)
4. DocumentService processes:
   a. Store document record
   b. Chunk content
   c. Generate embeddings for each chunk
   d. Store chunks and embeddings
5. Return document metadata
```

## Technology Stack

### Backend
- **Python 3.11+**: Modern Python with type hints
- **FastAPI**: High-performance async web framework
- **Pydantic v2**: Data validation and settings
- **SQLAlchemy 2.0**: ORM with async support readiness

### Database
- **PostgreSQL 16**: Relational database
- **pgvector**: Vector similarity search extension

### LLM & AI
- **OpenAI API**: GPT-4 for chat, text-embedding-3-small for vectors
- **tiktoken**: Token counting
- **tenacity**: Retry logic

### DevOps
- **Docker & Docker Compose**: Containerization
- **Alembic**: Database migrations
- **uvicorn**: ASGI server

### Dev Tools
- **ruff**: Fast linter and formatter
- **mypy**: Static type checking
- **pytest**: Testing framework
- **pre-commit**: Git hooks

## Security Considerations

1. **Authentication**: JWT tokens with expiration
2. **Authorization**: Role-based access control
3. **PII Protection**: Detection and redaction in logs and storage
4. **Secrets Management**: Environment variables, never committed
5. **Input Validation**: Pydantic schemas for all inputs
6. **SQL Injection**: SQLAlchemy ORM parameterization
7. **CORS**: Configurable origins
8. **Rate Limiting**: (TODO: Implementation needed)

## Scalability Considerations

**Current Design (MVP):**
- Single server deployment
- Synchronous LLM calls
- Connection pooling (5 connections, 10 max overflow)

**Future Improvements:**
- Task queue (Celery/RQ) for async processing
- Redis caching for embeddings
- Horizontal scaling with load balancer
- Streaming responses for chat
- CDN for static assets

## Monitoring & Observability

**Current:**
- Structured JSON logging
- Safety decision tracking
- Database audit trails

**Recommended Additions:**
- OpenTelemetry instrumentation
- Prometheus metrics
- Grafana dashboards
- Error tracking (Sentry)
- Log aggregation (ELK stack)

## Extension Points

The architecture is designed for extensibility:

1. **LLM Providers**: Add new providers by implementing `LLMProvider` interface
2. **Document Types**: Add new parsers in chunking logic
3. **Safety Rules**: Extend `SafetyChecker` with new patterns
4. **Agents**: Add custom agents to the pipeline
5. **Evaluation**: Add metrics in `app/eval/`

## Development Workflow

1. Local development with docker-compose
2. Database migrations with Alembic
3. Pre-commit hooks for code quality
4. CI/CD with GitHub Actions
5. Seed data for testing

## Deployment

**Docker Compose (Development):**
```bash
docker-compose up
```

**Production Considerations:**
- Kubernetes deployment
- Managed PostgreSQL (AWS RDS, Google Cloud SQL)
- Managed secrets (AWS Secrets Manager, HashiCorp Vault)
- HTTPS with SSL certificates
- Backup and disaster recovery
- Health checks and auto-scaling

## Trade-offs & Design Decisions

1. **Synchronous vs Async**: Chose sync for simplicity; async can be added later
2. **Embeddings**: OpenAI embeddings for quality; could use open-source alternatives
3. **Vector DB**: pgvector for simplicity; could use Pinecone/Weaviate for scale
4. **Safety**: Rule-based for transparency; could add ML-based classifiers
5. **Auth**: Simple JWT for MVP; should add OAuth/SSO for production
6. **Frontend**: Optional for MVP; API-first design allows any frontend

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pgvector](https://github.com/pgvector/pgvector)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [SQLAlchemy](https://www.sqlalchemy.org/)
