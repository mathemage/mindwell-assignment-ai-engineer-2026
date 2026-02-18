# Data Privacy Policy

## Overview

Mindwell AI is committed to protecting user privacy. This document explains what data we collect, how we use it, how we protect it, and your rights regarding your data.

## Data Collection

### User Account Information

**What We Collect:**
- Email address (for authentication)
- Hashed password (bcrypt with salt)
- Account creation timestamp
- User role (regular user or admin)

**How We Use It:**
- Authentication and authorization
- Account management
- Service communications

**Pseudonymization:**
- User IDs are pseudonymized using SHA-256 hashing
- Pseudonyms are used for internal references
- Original user IDs are never exposed in logs or API responses

### Conversation Data

**What We Collect:**
- Chat messages (user and assistant)
- Message timestamps
- Conversation metadata (citations, safety outcomes)

**PII Handling:**
- Personal Identifiable Information (PII) is automatically detected
- Detected PII types: emails, phone numbers, SSNs
- PII is redacted before storage
- Original PII patterns are logged separately for audit (not the actual values)

**How We Use It:**
- Provide chat functionality
- Improve response quality
- Safety monitoring and compliance

### Safety Logs

**What We Collect:**
- Safety decision outcomes
- Reason codes
- Matched patterns (not user content)
- Timestamps

**How We Use It:**
- Monitor system safety
- Audit trail for clinical compliance
- Improve safety detection

### Knowledge Base Documents

**What We Collect:**
- Document titles and content
- Document metadata (upload time, uploader)
- Generated chunks and embeddings

**How We Use It:**
- Provide information retrieval
- Generate AI responses with citations

## Data We Do NOT Collect

- Real names (unless voluntarily provided in messages)
- Physical addresses
- Payment information (not implemented in MVP)
- Device fingerprints or tracking cookies
- Browsing history outside our service
- Third-party profile data

## How We Protect Your Data

### Encryption

**In Transit:**
- All API communications should use HTTPS/TLS in production
- Database connections should use SSL/TLS in production

**At Rest:**
- Passwords: Hashed with bcrypt (irreversible)
- Database: Encryption depends on hosting provider
  - **Recommendation**: Enable database encryption at rest

### Access Controls

**Application Level:**
- JWT token authentication required
- Role-based access control (RBAC)
- Session expiration (30 minutes)

**Database Level:**
- Limited connection pooling
- Principle of least privilege for database user
- No direct database access from application logs

**Infrastructure Level:**
- **Recommendation**: Network isolation (VPC)
- **Recommendation**: Firewall rules limiting access
- **Recommendation**: Regular security audits

### PII Protection

**Detection:**
- Automatic pattern matching for common PII types
- Email addresses
- US phone numbers
- Social Security Numbers

**Redaction:**
- PII replaced with tokens (e.g., [EMAIL_REDACTED])
- Original values not stored in messages
- Detection metadata stored separately

**Logging:**
- All logs automatically redact PII
- Passwords, tokens, and API keys never logged
- Structured logging with sensitive field filtering

### Pseudonymization

**User Identifiers:**
- Real user IDs hashed with SHA-256
- First 16 characters used as pseudonym
- Pseudonyms used in all internal references
- Mapping never exposed externally

**Benefits:**
- Limits exposure in case of data breach
- Allows data analysis without identifying users
- Supports compliance with privacy regulations

## Data Retention

### Current Policy (MVP)

**Indefinite Retention:**
- User accounts
- Conversations and messages
- Safety logs
- Knowledge base documents

**Justification:**
- Clinical audit trail requirements
- Service improvement and quality assurance

### Recommended Production Policy

**User Accounts:**
- Active: Indefinite
- Inactive: Delete after 2 years of inactivity
- Deleted: 30-day grace period before permanent deletion

**Conversations:**
- Active users: Keep for 1 year
- After 1 year: Pseudonymize further or aggregate
- User-requested deletion: 30 days

**Safety Logs:**
- Keep for 7 years (clinical compliance)
- After 7 years: Archive or delete

**Knowledge Base:**
- Active documents: Indefinite
- Deprecated: Archive after review

## Data Sharing

### Third-Party Services

**OpenAI:**
- User queries sent to OpenAI API for processing
- OpenAI's data usage policy applies
- Zero data retention option should be configured
- **Recommendation**: Review OpenAI's Enterprise agreement

**No Other Third Parties:**
- We do not sell user data
- We do not share data with advertisers
- We do not use data for marketing

### Legal Requirements

We may disclose data when required by law:
- Valid subpoena or court order
- National security requests
- Protection of rights and safety

**Process:**
- Legal review before disclosure
- Notify affected users when legally permitted
- Disclose minimum necessary data

## Your Rights

### Right to Access

- Request a copy of your data
- Review what information we have
- Understand how we use your data

**How to Exercise:**
- Email: privacy@mindwell.ai
- Response time: 30 days

### Right to Rectification

- Correct inaccurate data
- Update incomplete data

**How to Exercise:**
- Update account information through UI
- Email for other corrections: privacy@mindwell.ai

### Right to Erasure ("Right to be Forgotten")

- Request deletion of your account and data
- **Exceptions**:
  - Legal obligations (e.g., clinical audit trails)
  - Ongoing safety investigations

**How to Exercise:**
- Email: privacy@mindwell.ai
- Include account email and confirmation
- Response time: 30 days
- Grace period: 30 days before permanent deletion

### Right to Data Portability

- Export your data in machine-readable format
- Transfer data to another service

**Current Status**: Not implemented in MVP
**Recommendation**: Implement JSON export functionality

### Right to Object

- Object to specific data processing
- Opt-out of non-essential communications

**How to Exercise:**
- Email: privacy@mindwell.ai

### Right to Restrict Processing

- Limit how we process your data while investigating concerns

**How to Exercise:**
- Email: privacy@mindwell.ai

## Children's Privacy

**Age Requirement**: Users must be 18 years or older (or 13+ with parental consent)

**COPPA Compliance** (if applicable):
- Parental consent required for users under 13
- Limited data collection for minors
- Parental access to child's data

**Current Implementation**: Age verification not implemented (MVP)

## International Data Transfers

**Current Deployment**: Single region (to be determined)

**Considerations for Production**:
- EU users: GDPR compliance, data localization
- UK users: UK GDPR compliance
- California users: CCPA compliance

**Mechanisms**:
- Standard Contractual Clauses (SCCs)
- Adequacy decisions
- Binding Corporate Rules (BCRs)

## Cookies and Tracking

**Current Implementation**: No cookies or tracking (API-only MVP)

**If Frontend Added**:
- Authentication tokens only
- No advertising or tracking cookies
- Cookie consent banner (if required)

## Data Breach Notification

### Internal Procedures

**Detection:**
- Automated monitoring and alerts
- Security event logging
- Regular security audits

**Response:**
1. Contain the breach
2. Assess scope and impact
3. Notify affected parties
4. Report to authorities (if required)
5. Remediate vulnerabilities

### User Notification

**Timeline:**
- Within 72 hours of discovery (GDPR requirement)
- Within 30 days (HIPAA requirement)

**Content:**
- Nature of the breach
- Data affected
- Steps taken to address
- Recommended actions for users

## Changes to This Policy

**Notification:**
- Email to registered users
- Prominent notice on website
- Effective date clearly stated

**Material Changes:**
- 30-day notice period
- Option to delete account if disagree

## Compliance Frameworks

### HIPAA (if applicable)

**Status**: Not currently compliant
**Requirements for Compliance**:
- Business Associate Agreements (BAAs)
- Encryption at rest and in transit
- Comprehensive audit trails
- Breach notification procedures
- Regular risk assessments

### GDPR (EU users)

**Status**: Partial compliance (MVP)
**Additional Requirements**:
- Data Protection Officer (DPO)
- Data Protection Impact Assessment (DPIA)
- Privacy by Design
- Data portability implementation
- Consent management

### CCPA (California users)

**Status**: Not currently compliant
**Requirements**:
- Privacy policy disclosure
- Right to know what data collected
- Right to deletion
- Opt-out of data sales (N/A - we don't sell data)
- Non-discrimination for exercising rights

## Clinical Considerations

### Mental Health Data Sensitivity

**Special Protections:**
- Mental health conversations are highly sensitive
- Extra care in access controls
- Limited retention periods recommended
- Secure deletion procedures

### Crisis Data

**Safety Logs:**
- Crisis detections logged for safety
- Used to improve safety systems
- Retained for clinical audit trail
- Access restricted to safety team

## Contact Information

**Data Privacy Inquiries:**
- Email: privacy@mindwell.ai
- Response time: 30 days

**Data Protection Officer (if applicable):**
- Email: dpo@mindwell.ai

**Security Issues:**
- Email: security@mindwell.ai
- **Do not** include sensitive personal data in security reports

## Accountability

### Regular Reviews

- Quarterly privacy policy review
- Annual comprehensive audit
- Security assessments
- Compliance checks

### Training

- Staff training on data privacy
- Security awareness programs
- Incident response drills

### Documentation

- Processing activity records
- Data flow mapping
- Privacy impact assessments
- Compliance documentation

---

**Last Updated**: 2026-02-18
**Version**: 1.0
**Effective Date**: 2026-02-18

By using Mindwell AI, you acknowledge that you have read and understood this Data Privacy Policy.
