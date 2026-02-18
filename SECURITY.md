# Security Policy

## Overview

This document outlines the security measures implemented in the Mindwell AI system to protect user data, ensure safe operations, and maintain system integrity.

## Authentication & Authorization

### User Authentication

- **Method**: JWT (JSON Web Tokens) with HS256 algorithm
- **Token Expiration**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Password Security**:
  - Minimum length: 8 characters
  - Hashed using bcrypt with automatic salt
  - Passwords never stored in plain text
  - Passwords never logged

### Authorization

- **Role-Based Access Control (RBAC)**:
  - Regular users: Can chat and view their own conversations
  - Admin users: Can manage knowledge base documents
- **Token Validation**: Required for all protected endpoints
- **User Pseudonymization**: User IDs are pseudonymized using SHA-256 hashing

## Data Privacy

### Personal Identifiable Information (PII)

The system implements comprehensive PII protection:

1. **Detection Patterns**:
   - Email addresses
   - Phone numbers (US format)
   - Social Security Numbers

2. **PII Handling**:
   - **Logs**: All PII is redacted before logging
   - **Storage**: User messages are stored with PII redacted
   - **Metadata**: PII detections are logged separately for audit

3. **User Identity**:
   - Real user IDs replaced with pseudonymized identifiers
   - Pseudonyms generated using SHA-256 hash (first 16 chars)
   - Original mapping never exposed in API responses

### Data Retention

- **Conversations**: Stored indefinitely (should be reviewed for production)
- **Safety Logs**: Stored indefinitely for audit purposes
- **User Data**: Soft delete recommended (not currently implemented)

**Recommendation**: Implement data retention policies compliant with GDPR, HIPAA, or other applicable regulations.

## Clinical Safety

### Crisis Detection

The system includes pattern-based crisis detection for:

1. **Suicide Ideation**:
   - Patterns: "kill myself", "suicide", "want to die", etc.
   - Response: Immediate escalation with crisis resources
   - Resources provided:
     - National Suicide Prevention Lifeline: 988
     - Crisis Text Line: Text HOME to 741741
     - Emergency Services: 911

2. **Self-Harm**:
   - Patterns: "cut myself", "self-harm", "hurt myself"
   - Response: Same as suicide ideation

3. **General Crisis**:
   - Patterns: "crisis", "emergency", "can't go on"
   - Response: Escalation with crisis resources

4. **Medical Advice Requests**:
   - Patterns: "should i take", "prescribe", "diagnose"
   - Response: Refusal with guidance to consult healthcare provider

### Safety Logging

- All safety decisions are logged with:
  - Decision type (ok, refused, escalated)
  - Reason code
  - Matched pattern (when applicable)
  - Timestamp
  - Associated conversation/message

## Secret Management

### Environment Variables

**Never Commit Secrets** to version control. All sensitive configuration is managed via environment variables:

- `OPENAI_API_KEY`: OpenAI API key
- `SECRET_KEY`: JWT signing key
- `DATABASE_URL`: Database connection string

### Production Recommendations

1. Use a secrets management service:
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Google Secret Manager

2. Rotate secrets regularly
3. Use different keys for each environment
4. Implement secret access auditing

## Input Validation

### API Level

- **Pydantic Schemas**: All inputs validated with type checking
- **Length Limits**:
  - Chat messages: 5000 characters max
  - Document titles: 500 characters max
  - Email: Valid email format required
  - Password: Minimum 8 characters

### Database Level

- **SQLAlchemy ORM**: Parameterized queries prevent SQL injection
- **Foreign Key Constraints**: Ensure referential integrity
- **Type Validation**: Database-level type checking

### LLM Level

- **Prompt Injection Protection**:
  - System prompts clearly separate context from user input
  - User input clearly marked in prompts
  - No user input in system configuration

## Logging Security

### Structured Logging

- **Format**: JSON (production) or text (development)
- **Level**: INFO (configurable)
- **Sensitive Data Redaction**:
  - Passwords
  - Tokens
  - API keys
  - Secrets
  - Authorization headers
  - PII (emails, phones, SSNs)

### Log Access

**Recommendations**:
- Restrict log access to authorized personnel only
- Implement log retention policies
- Use log aggregation with access controls (e.g., ELK stack)
- Enable audit trails for log access

## Network Security

### HTTPS

**Production Requirements**:
- All traffic must use HTTPS/TLS
- Use valid SSL certificates
- Implement HSTS headers
- Disable insecure protocols (SSL, TLS 1.0, TLS 1.1)

### CORS

- **Development**: Allows all origins
- **Production**: Must whitelist specific origins
- **Credentials**: Enabled for authenticated requests

### Rate Limiting

**Current Status**: Not implemented (MVP)

**Recommendations**:
- Implement rate limiting per user/IP
- Default: 60 requests per minute (configurable)
- Use Redis for distributed rate limiting
- Return 429 Too Many Requests when exceeded

## Database Security

### Connection Security

- **Connection Pooling**: Limited to 5 connections with 10 max overflow
- **Connection String**: Never logged or exposed
- **SSL/TLS**: Should be enabled for production

### Access Control

- **Principle of Least Privilege**: Application user has minimal required permissions
- **No Root Access**: Application never uses database superuser
- **Separate Users**: Different users for migrations vs application

### Backups

**Recommendations**:
- Automated daily backups
- Encrypted backup storage
- Regular backup testing
- Point-in-time recovery capability

## LLM Security

### API Key Protection

- Never logged
- Never committed to version control
- Stored in environment variables
- Rotated regularly

### Prompt Safety

- System prompts enforce safety rules
- No user input in system configuration
- Clear separation between instructions and data
- Citation requirements prevent hallucination

### Rate Limiting

- Implement OpenAI rate limiting
- Handle rate limit errors gracefully
- Retry with exponential backoff

## Vulnerability Management

### Dependency Security

**Current**:
- Use specific version constraints in `pyproject.toml`
- Regular dependency updates

**Recommendations**:
- Use Dependabot for automated security updates
- Scan dependencies with tools like `safety` or `pip-audit`
- Review security advisories regularly

### Code Security

**Current**:
- Type checking with mypy
- Linting with ruff
- Pre-commit hooks

**Recommendations**:
- Static analysis with Bandit
- Regular security audits
- Penetration testing before production

## Incident Response

### Monitoring

**Required for Production**:
1. Error tracking (e.g., Sentry)
2. Log monitoring and alerting
3. Performance monitoring (e.g., New Relic, DataDog)
4. Security event monitoring

### Response Plan

1. **Detection**: Automated alerts for security events
2. **Assessment**: Evaluate severity and impact
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threat and patch vulnerabilities
5. **Recovery**: Restore normal operations
6. **Review**: Post-incident analysis and improvements

## Compliance Considerations

### HIPAA (if applicable)

**Requirements**:
- Encryption at rest and in transit
- Access controls and audit trails
- Business Associate Agreements with third parties
- Data breach notification procedures

### GDPR (if applicable)

**Requirements**:
- Right to access (user data export)
- Right to erasure (data deletion)
- Right to portability
- Consent management
- Data processing agreements

**Current Implementation Status**: MVP does not fully implement GDPR requirements. Must be added before EU deployment.

## Security Checklist for Production

- [ ] Change all default credentials
- [ ] Use strong, unique SECRET_KEY
- [ ] Enable HTTPS with valid certificates
- [ ] Implement rate limiting
- [ ] Restrict CORS to specific origins
- [ ] Enable database SSL/TLS
- [ ] Set up automated backups
- [ ] Configure log retention and rotation
- [ ] Implement monitoring and alerting
- [ ] Set up secrets management service
- [ ] Regular security audits
- [ ] Dependency vulnerability scanning
- [ ] Penetration testing
- [ ] Incident response plan
- [ ] Data retention policies
- [ ] Privacy policy and terms of service

## Reporting Security Issues

If you discover a security vulnerability, please email: security@mindwell.ai

**Do not** open public GitHub issues for security vulnerabilities.

## Updates

This security policy should be reviewed and updated:
- Quarterly
- After security incidents
- When adding new features
- When regulations change

---

**Last Updated**: 2026-02-18
**Version**: 1.0
