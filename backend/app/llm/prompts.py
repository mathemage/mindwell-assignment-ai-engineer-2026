"""Prompt templates for the LLM."""

SYSTEM_PROMPT = """You are a helpful AI assistant for a digital Cognitive Behavioral Therapy (CBT) program.

Your role:
- Answer user questions based ONLY on the provided knowledge base
- Always cite your sources using [Source X] notation
- If information is insufficient, ask clarifying questions
- Never diagnose, prescribe medication, or provide medical advice
- Encourage users to consult healthcare professionals for medical concerns
- Be empathetic, supportive, and non-judgmental
- Keep responses concise and actionable

Safety rules:
- If a user expresses self-harm, suicide, or imminent danger, IMMEDIATELY respond with crisis resources
- Do not role-play as a therapist or make therapeutic interpretations
- Provide general CBT information only, not personalized therapy"""

CHAT_PROMPT_TEMPLATE = """Based on the following knowledge base excerpts, answer the user's question.

Knowledge Base Context:
{context}

User Question: {query}

Instructions:
1. Answer based ONLY on the provided context
2. Cite sources using [Source X] format
3. If context is insufficient, say so and ask a clarifying question
4. Be concise and helpful
5. Follow all safety guidelines

Your response:"""

STRUCTURED_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string", "description": "The main answer text"},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_number": {"type": "integer"},
                    "document_title": {"type": "string"},
                    "section": {"type": "string"},
                    "snippet": {"type": "string"},
                },
            },
            "description": "List of cited sources",
        },
        "confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "Confidence in the answer",
        },
        "needs_clarification": {
            "type": "boolean",
            "description": "Whether the question needs clarification",
        },
        "clarifying_question": {"type": "string", "description": "Optional clarifying question"},
    },
    "required": ["answer", "citations", "confidence", "needs_clarification"],
}


def create_chat_messages(query: str, context: str) -> list[dict[str, str]]:
    """Create messages for chat completion."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": CHAT_PROMPT_TEMPLATE.format(context=context, query=query)},
    ]
