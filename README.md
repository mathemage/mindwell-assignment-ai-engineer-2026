# Mindwell AI - CBT Assistant MVP

A production-ready MVP for Mindwell-style AI features with strong safety, privacy, and evaluation. This system provides an AI-powered chat assistant for digital Cognitive Behavioral Therapy (CBT) programs with:

- 🔍 **RAG with Citations**: Answers grounded in knowledge base with source citations
- 🛡️ **Clinical Safety**: Crisis detection and medical advice boundaries
- 🔐 **Privacy-First**: PII detection, redaction, and pseudonymization
- 🤖 **Multi-Agent Pipeline**: Retrieve → Draft → Safety Check → Finalize
- 📊 **Evaluation Ready**: Offline metrics and regression tests

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key

### 1. Clone and Setup

```bash
git clone https://github.com/mathemage/mindwell-assignment-ai-engineer-2026.git
cd mindwell-assignment-ai-engineer-2026

# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 2. Start with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f backend
```

The API will be available at `http://localhost:8000`

### 3. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Seed sample data (CBT documents and test users)
docker-compose exec backend python -m app.scripts.seed_data
```

### 4. Test the API

**Register a user:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

**Chat (use token from login):**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"message": "What is cognitive behavioral therapy?"}'
```

## Local Development

### Without Docker

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .[dev]

# Start PostgreSQL with pgvector
docker-compose up postgres

# Run migrations
alembic upgrade head

# Seed data
python -m app.scripts.seed_data

# Start development server
uvicorn app.main:app --reload
```

### Using Make Commands

```bash
make help           # Show all available commands
make install        # Install dependencies
make dev            # Run development server
make test           # Run tests
make lint           # Run linter
make format         # Format code
make typecheck      # Run type checker
make docker-up      # Start Docker services
make docker-down    # Stop Docker services
```

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── agents/         # Multi-agent pipeline
│   │   ├── api/           # FastAPI routes and schemas
│   │   ├── core/          # Config, logging, security
│   │   ├── db/            # Database models and session
│   │   ├── eval/          # Evaluation scripts
│   │   ├── llm/           # LLM provider and prompts
│   │   ├── rag/           # Chunking, embeddings, retrieval
│   │   ├── safety/        # Safety policy and detection
│   │   ├── scripts/       # Seed data and utilities
│   │   ├── services/      # Business logic
│   │   ├── tests/         # Test suite
│   │   └── main.py        # FastAPI application
│   ├── alembic/           # Database migrations
│   ├── pyproject.toml     # Python dependencies
│   └── Dockerfile
├── docker-compose.yml
├── Makefile
├── .env.example
├── ARCHITECTURE.md        # System architecture
├── SECURITY.md           # Security policy
└── DATA_PRIVACY.md       # Privacy policy
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

**Authentication:**
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

**Chat:**
- `POST /chat` - Send chat message, get AI response with citations

**Admin (requires admin role):**
- `POST /admin/docs/upload` - Upload document (markdown, PDF, or text)
- `GET /admin/docs` - List all documents
- `POST /admin/docs/reindex` - Reindex document
- `DELETE /admin/docs/{id}` - Delete document

### Default Test Accounts

After running seed script:

**Admin:**
- Email: `admin@mindwell.ai`
- Password: `admin123456`

**Regular User:**
- Email: `user@example.com`
- Password: `password123`

## Features

### RAG with Citations

- **Chunking**: Intelligent splitting by headings (markdown) or size
- **Vector Search**: pgvector cosine similarity
- **Top-k Retrieval**: Configurable (default: 5)
- **Citations**: Each response includes source references

### Clinical Safety

**Crisis Detection:**
- Suicide ideation
- Self-harm expressions
- Emergency situations

**Boundaries:**
- Refuses medical diagnoses
- Refuses prescription requests
- Provides crisis resources when needed

**All safety decisions are logged for audit.**

### Privacy Protection

**PII Detection & Redaction:**
- Email addresses
- Phone numbers
- Social Security Numbers

**Pseudonymization:**
- User IDs hashed for anonymity
- Original IDs never logged

**Secure Logging:**
- Passwords and tokens never logged
- PII automatically redacted from logs

### Multi-Agent Architecture

1. **RetrieverAgent**: Find relevant knowledge base chunks
2. **DraftAgent**: Generate response with LLM
3. **SafetyAgent**: Check input and output for safety
4. **FinalizerAgent**: Add citations and metadata

## Configuration

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql+psycopg://mindwell:password@localhost:5432/mindwell

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small

# Security
SECRET_KEY=your-secret-key-here

# RAG
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.7

# Safety
ENABLE_CRISIS_DETECTION=true
ENABLE_PII_REDACTION=true
```

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest backend/app/tests/test_safety.py

# Run with verbose output
pytest -v
```

## Development Workflow

### 1. Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type check
make typecheck

# Run all checks (CI simulation)
make ci
```

### 2. Database Migrations

```bash
# Create new migration
make migrate-create MESSAGE="add new field"

# Run migrations
make migrate

# Rollback
alembic downgrade -1
```

### 3. Adding Documents

**Via API (requires admin token):**
```bash
curl -X POST http://localhost:8000/admin/docs/upload \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "title=My CBT Guide" \
  -F "source_type=markdown" \
  -F "file=@path/to/guide.md"
```

**Via seed script:** Add documents to `backend/app/scripts/seed_data.py`

## Deployment

### Docker Production

```bash
# Set production environment variables
export ENVIRONMENT=production
export SECRET_KEY=$(openssl rand -hex 32)
export DATABASE_URL=postgresql://...

# Build and run
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes (Recommended for Production)

See deployment examples in `k8s/` directory (TODO: add k8s manifests)

### Production Checklist

- [ ] Use strong, unique `SECRET_KEY`
- [ ] Set `ENVIRONMENT=production`
- [ ] Enable HTTPS/TLS
- [ ] Configure database SSL
- [ ] Set up automated backups
- [ ] Configure log aggregation
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Enable rate limiting
- [ ] Restrict CORS origins
- [ ] Review security policy
- [ ] Set up secrets management
- [ ] Configure data retention policies

## Monitoring & Observability

### Logs

Structured JSON logging to stdout:
```json
{
  "timestamp": "2026-02-18T17:14:00Z",
  "level": "info",
  "logger": "app.agents.orchestrator",
  "event": "ChatOrchestrator complete",
  "user_id": "abc123..."
}
```

### Metrics (TODO)

Recommended metrics to track:
- Request latency
- Error rates
- Safety decision distribution
- Token usage and costs
- Retrieval quality (hit rate)

## Evaluation

### Running Evaluations

```bash
# TODO: Implement evaluation scripts
python -m app.eval.run_retrieval_eval
python -m app.eval.run_answer_quality_eval
```

### Metrics

- **Retrieval**: Hit@k, MRR, precision
- **Answer Quality**: Groundedness, citation accuracy
- **Safety**: False positive/negative rates
- **Performance**: Latency, token usage

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
make migrate
make seed
```

### OpenAI API Errors

- Verify API key in `.env`
- Check API quota and limits
- Review OpenAI status page

### Import Errors

```bash
# Ensure backend is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# Or install in editable mode
pip install -e backend/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `make ci` to verify
5. Submit pull request

### Commit Message Format

Follow conventional commits:
```
feat(scope): Add new feature
fix(scope): Fix bug
docs(scope): Update documentation
test(scope): Add tests
refactor(scope): Refactor code
```

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System design and components
- [SECURITY.md](./SECURITY.md) - Security measures and policies
- [DATA_PRIVACY.md](./DATA_PRIVACY.md) - Data handling and privacy
- [API Docs](http://localhost:8000/docs) - Interactive API documentation

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic v2
- **Database**: PostgreSQL 16 with pgvector
- **LLM**: OpenAI (GPT-4, text-embedding-3-small)
- **Dev Tools**: ruff, mypy, pytest, pre-commit
- **Infrastructure**: Docker, Docker Compose

## License

See [LICENSE](./LICENSE) for details.

## Support

- Issues: [GitHub Issues](https://github.com/mathemage/mindwell-assignment-ai-engineer-2026/issues)
- Email: support@mindwell.ai

## Acknowledgments

Built as an MVP demonstrating best practices for AI-powered mental health applications with emphasis on safety, privacy, and clinical appropriateness.
