"""Test safety policy and crisis detection."""
import pytest

from app.safety.policy import SafetyChecker, SafetyDecision, ReasonCode


def test_suicide_detection():
    """Test suicide ideation detection."""
    checker = SafetyChecker()

    test_cases = [
        "I want to kill myself",
        "I'm thinking about suicide",
        "I don't want to live anymore",
        "I want to end it all",
    ]

    for text in test_cases:
        result = checker.check_input(text)
        assert result.decision == SafetyDecision.ESCALATED
        assert result.reason_code == ReasonCode.SUICIDE
        assert result.override_response is not None
        assert "988" in result.override_response  # Crisis hotline number


def test_self_harm_detection():
    """Test self-harm detection."""
    checker = SafetyChecker()

    test_cases = [
        "I've been cutting myself",
        "I want to hurt myself",
        "I'm self-harming",
    ]

    for text in test_cases:
        result = checker.check_input(text)
        assert result.decision == SafetyDecision.ESCALATED
        assert result.reason_code == ReasonCode.SELF_HARM


def test_medical_advice_detection():
    """Test medical advice request detection."""
    checker = SafetyChecker()

    test_cases = [
        "Should I take antidepressants?",
        "Can you diagnose my condition?",
        "What medication should I take?",
        "Should I stop taking my medication?",
    ]

    for text in test_cases:
        result = checker.check_input(text)
        assert result.decision == SafetyDecision.REFUSED
        assert result.reason_code == ReasonCode.MEDICAL_ADVICE
        assert "healthcare provider" in result.override_response.lower()


def test_safe_input():
    """Test that safe inputs pass."""
    checker = SafetyChecker()

    test_cases = [
        "What is cognitive behavioral therapy?",
        "Can you help me with anxiety?",
        "I'm feeling stressed today",
        "Tell me about coping strategies",
    ]

    for text in test_cases:
        result = checker.check_input(text)
        assert result.decision == SafetyDecision.OK
        assert result.reason_code == ReasonCode.SAFE


def test_output_safety_check():
    """Test output safety checking."""
    checker = SafetyChecker()

    # Safe output
    safe_output = "Here are some coping strategies you can try..."
    result = checker.check_output(safe_output)
    assert result.decision == SafetyDecision.OK

    # Output with medical advice (should be caught)
    unsafe_output = "You should take 50mg of medication daily."
    result = checker.check_output(unsafe_output)
    assert result.decision == SafetyDecision.REFUSED


def test_crisis_response_includes_resources():
    """Test that crisis responses include emergency resources."""
    checker = SafetyChecker()
    result = checker.check_input("I want to die")

    assert result.override_response is not None
    assert "988" in result.override_response  # Suicide Prevention Lifeline
    assert "741741" in result.override_response  # Crisis Text Line
    assert "911" in result.override_response  # Emergency services
