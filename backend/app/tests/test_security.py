"""Test PII detection and redaction."""

from app.core.security import detect_pii, redact_pii


def test_email_detection():
    """Test email address detection."""
    text = "Contact me at john.doe@example.com for more info."
    pii = detect_pii(text)

    assert len(pii["emails"]) == 1
    assert "john.doe@example.com" in pii["emails"]


def test_phone_detection():
    """Test phone number detection."""
    test_cases = [
        ("Call me at 555-123-4567", "555-123-4567"),
        ("My number is (555) 123-4567", "555-123-4567"),
        ("Phone: 5551234567", "555-123-4567"),
    ]

    for text, expected in test_cases:
        pii = detect_pii(text)
        assert len(pii["phones"]) == 1
        assert expected in pii["phones"]


def test_ssn_detection():
    """Test SSN detection."""
    text = "My SSN is 123-45-6789"
    pii = detect_pii(text)

    assert len(pii["ssns"]) == 1
    assert "123-45-6789" in pii["ssns"]


def test_email_redaction():
    """Test email redaction."""
    text = "Email me at user@example.com please"
    redacted, pii = redact_pii(text)

    assert "user@example.com" not in redacted
    assert "[EMAIL_REDACTED]" in redacted
    assert len(pii["emails"]) == 1


def test_phone_redaction():
    """Test phone number redaction."""
    text = "Call 555-123-4567 for help"
    redacted, pii = redact_pii(text)

    assert "555-123-4567" not in redacted
    assert "[PHONE_REDACTED]" in redacted


def test_multiple_pii_types():
    """Test detection of multiple PII types."""
    text = "Email user@example.com or call 555-123-4567. SSN: 123-45-6789"
    pii = detect_pii(text)

    assert len(pii["emails"]) == 1
    assert len(pii["phones"]) == 1
    assert len(pii["ssns"]) == 1


def test_no_pii():
    """Test text with no PII."""
    text = "This is a normal message with no personal information."
    pii = detect_pii(text)

    assert len(pii["emails"]) == 0
    assert len(pii["phones"]) == 0
    assert len(pii["ssns"]) == 0


def test_redaction_preserves_structure():
    """Test that redaction preserves text structure."""
    text = "Hello user@example.com, call 555-123-4567!"
    redacted, _ = redact_pii(text)

    # Check that structure is preserved
    assert redacted.startswith("Hello")
    assert redacted.endswith("!")
    assert "[EMAIL_REDACTED]" in redacted
    assert "[PHONE_REDACTED]" in redacted
