"""Safety policy and crisis detection."""

import re
from enum import StrEnum
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class SafetyDecision(StrEnum):
    """Safety decision outcomes."""

    OK = "ok"
    REFUSED = "refused"
    ESCALATED = "escalated"


class ReasonCode(StrEnum):
    """Reason codes for safety decisions."""

    SAFE = "safe"
    CRISIS_DETECTED = "crisis_detected"
    SELF_HARM = "self_harm"
    SUICIDE = "suicide"
    MEDICAL_ADVICE = "medical_advice"
    INAPPROPRIATE_CONTENT = "inappropriate_content"


class SafetyResult:
    """Result from safety check."""

    def __init__(
        self,
        decision: SafetyDecision,
        reason_code: ReasonCode,
        details: dict[str, Any] | None = None,
        override_response: str | None = None,
    ) -> None:
        self.decision = decision
        self.reason_code = reason_code
        self.details = details or {}
        self.override_response = override_response

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision": self.decision.value,
            "reason_code": self.reason_code.value,
            "details": self.details,
            "override_response": self.override_response,
        }


# Crisis detection patterns
SUICIDE_PATTERNS = [
    r"\b(kill myself|suicide|end (my|it all)|take my own life)\b",
    r"\b(want to die|wish (i was|i were) dead|don't want to (live|be here))\b",
    r"\b(better off dead|no reason to live)\b",
]

SELF_HARM_PATTERNS = [
    r"\b(cut myself|cutting|self[- ]harm(?:ing)?|hurt myself)\b",
    r"\b(burning myself|hitting myself)\b",
]

CRISIS_PATTERNS = [
    r"\b(crisis|emergency|help me)\b.*\b(now|urgent|immediately)\b",
    r"\b(can't go on|can't take it)\b",
]

MEDICAL_ADVICE_PATTERNS = [
    r"\b(should i take|you should take|prescribe|medication for|drug for|diagnose)\b",
    r"\b(what medicine|which pill|medical advice)\b",
    r"\b(stop taking|start taking).*\b(medication|medicine|drug)\b",
]

CRISIS_RESPONSE = """I'm concerned about what you've shared. Your safety is the top priority.

Please reach out to these resources immediately:
- **National Suicide Prevention Lifeline**: 988 (call or text, 24/7)
- **Crisis Text Line**: Text HOME to 741741
- **Emergency Services**: 911

If you're in immediate danger, please call 911 or go to your nearest emergency room.

I also encourage you to contact your therapist or mental health provider as soon as possible.

This AI assistant cannot provide crisis support, but trained professionals are available 24/7 to help."""


class SafetyChecker:
    """Check content for safety issues."""

    def __init__(self) -> None:
        # Compile patterns for efficiency
        self.suicide_regex = [re.compile(pattern, re.IGNORECASE) for pattern in SUICIDE_PATTERNS]
        self.self_harm_regex = [
            re.compile(pattern, re.IGNORECASE) for pattern in SELF_HARM_PATTERNS
        ]
        self.crisis_regex = [re.compile(pattern, re.IGNORECASE) for pattern in CRISIS_PATTERNS]
        self.medical_regex = [
            re.compile(pattern, re.IGNORECASE) for pattern in MEDICAL_ADVICE_PATTERNS
        ]

    def check_input(self, text: str) -> SafetyResult:
        """Check user input for safety issues."""
        logger.info("Checking input safety", text_length=len(text))

        # Check for suicide ideation (highest priority)
        for pattern in self.suicide_regex:
            if pattern.search(text):
                logger.warning("Suicide ideation detected")
                return SafetyResult(
                    decision=SafetyDecision.ESCALATED,
                    reason_code=ReasonCode.SUICIDE,
                    details={"matched_pattern": pattern.pattern},
                    override_response=CRISIS_RESPONSE,
                )

        # Check for self-harm
        for pattern in self.self_harm_regex:
            if pattern.search(text):
                logger.warning("Self-harm detected")
                return SafetyResult(
                    decision=SafetyDecision.ESCALATED,
                    reason_code=ReasonCode.SELF_HARM,
                    details={"matched_pattern": pattern.pattern},
                    override_response=CRISIS_RESPONSE,
                )

        # Check for general crisis
        for pattern in self.crisis_regex:
            if pattern.search(text):
                logger.warning("Crisis situation detected")
                return SafetyResult(
                    decision=SafetyDecision.ESCALATED,
                    reason_code=ReasonCode.CRISIS_DETECTED,
                    details={"matched_pattern": pattern.pattern},
                    override_response=CRISIS_RESPONSE,
                )

        # Check for medical advice requests
        for pattern in self.medical_regex:
            if pattern.search(text):
                logger.warning("Medical advice request detected")
                return SafetyResult(
                    decision=SafetyDecision.REFUSED,
                    reason_code=ReasonCode.MEDICAL_ADVICE,
                    details={"matched_pattern": pattern.pattern},
                    override_response="I cannot provide medical advice, diagnoses, or medication recommendations. "
                    "Please consult with a licensed healthcare provider for medical concerns. "
                    "I can provide general information about CBT techniques and coping strategies if that would be helpful.",
                )

        logger.info("Input passed safety checks")
        return SafetyResult(decision=SafetyDecision.OK, reason_code=ReasonCode.SAFE)

    def check_output(self, text: str) -> SafetyResult:
        """Check LLM output for safety issues."""
        logger.info("Checking output safety", text_length=len(text))

        # Check if output inappropriately attempts to provide medical advice
        for pattern in self.medical_regex:
            if pattern.search(text):
                logger.warning("Output contains medical advice")
                return SafetyResult(
                    decision=SafetyDecision.REFUSED,
                    reason_code=ReasonCode.MEDICAL_ADVICE,
                    details={"matched_pattern": pattern.pattern},
                    override_response="I apologize, but I cannot provide that information. "
                    "Please consult with a healthcare professional for medical advice.",
                )

        logger.info("Output passed safety checks")
        return SafetyResult(decision=SafetyDecision.OK, reason_code=ReasonCode.SAFE)
