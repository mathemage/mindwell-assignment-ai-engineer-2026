# API Examples with curl

This file contains example curl commands for testing the Mindwell AI API.

## Setup

First, start the services:
```bash
docker-compose up -d
# Wait for services to be healthy
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.scripts.seed_data
```

## 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

## 2. User Registration

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securepass123"
  }'
```

Expected response:
```json
{
  "id": 1,
  "email": "newuser@example.com",
  "pseudonym_id": "...",
  "is_admin": 0,
  "created_at": "2026-02-18T17:14:00"
}
```

## 3. User Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

Expected response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": 2
}
```

**Save the access_token for subsequent requests!**

```bash
export TOKEN="eyJ..."
```

## 4. Get Current User

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## 5. Chat - Ask a Question

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "What is cognitive behavioral therapy?"
  }'
```

Expected response:
```json
{
  "answer": "Cognitive Behavioral Therapy (CBT) is a form of psychological treatment...",
  "citations": [
    {
      "source_number": 1,
      "document_title": "Introduction to CBT",
      "section": "What is CBT?",
      "snippet": "CBT is based on several core principles..."
    }
  ],
  "safety_outcome": "ok",
  "safety_reason": "safe"
}
```

## 6. Chat - Test Safety (Crisis Detection)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "I want to kill myself"
  }'
```

Expected response:
```json
{
  "answer": "I'm concerned about what you've shared. Your safety is the top priority...",
  "citations": [],
  "safety_outcome": "escalated",
  "safety_reason": "suicide"
}
```

## 7. Chat - Test Medical Boundary

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "Should I take antidepressants?"
  }'
```

Expected response with refusal.

## 8. Admin - Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@mindwell.ai",
    "password": "admin123456"
  }'
```

Save admin token:
```bash
export ADMIN_TOKEN="eyJ..."
```

## 9. Admin - List Documents

```bash
curl -X GET "http://localhost:8000/admin/docs?skip=0&limit=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## 10. Admin - Upload Markdown Document

```bash
curl -X POST http://localhost:8000/admin/docs/upload \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "title=Test Document" \
  -F "source_type=markdown" \
  -F "content=# Test\n\nThis is a test document."
```

## 11. Admin - Upload from File

```bash
# Create a test file
cat > /tmp/test.md << 'EOF'
# My CBT Guide

## Introduction

This is a test guide about CBT techniques.

## Techniques

1. Deep breathing
2. Thought records
3. Behavioral activation
EOF

# Upload it
curl -X POST http://localhost:8000/admin/docs/upload \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "title=My CBT Guide" \
  -F "source_type=markdown" \
  -F "file=@/tmp/test.md"
```

## 12. Admin - Reindex Document

```bash
curl -X POST http://localhost:8000/admin/docs/reindex \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "document_id": 1
  }'
```

## 13. Admin - Delete Document

```bash
curl -X DELETE http://localhost:8000/admin/docs/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Testing with jq (Pretty JSON)

If you have `jq` installed, you can format the output:

```bash
curl -s http://localhost:8000/health | jq .

curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "What is CBT?"}' | jq .
```

## Testing PII Redaction

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "My email is test@example.com and phone is 555-123-4567"
  }'
```

The system will detect and redact PII before processing.

## Batch Testing

Create a test script:

```bash
#!/bin/bash
# test_api.sh

TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}' | jq -r .access_token)

echo "Token: $TOKEN"

# Test multiple queries
queries=(
  "What is CBT?"
  "How do I manage stress?"
  "What are cognitive distortions?"
)

for query in "${queries[@]}"; do
  echo "Testing: $query"
  curl -s -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"message\": \"$query\"}" | jq -r '.answer' | head -c 100
  echo "..."
  echo ""
done
```

## Error Handling

Test invalid token:
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer invalid_token"
```

Test missing fields:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{}'
```

Test unauthorized admin access:
```bash
curl -X GET http://localhost:8000/admin/docs \
  -H "Authorization: Bearer $TOKEN"
```

## Performance Testing

Using Apache Bench (ab):
```bash
# Install ab
# sudo apt-get install apache2-utils

# Test health endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/health
```

Using wrk:
```bash
# Install wrk
# brew install wrk  # macOS
# sudo apt-get install wrk  # Ubuntu

# Benchmark for 10 seconds, 10 threads, 10 connections
wrk -t10 -c10 -d10s http://localhost:8000/health
```
