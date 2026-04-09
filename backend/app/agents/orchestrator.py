"""Multi-agent pipeline for processing chat requests."""

from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.llm.prompts import create_chat_messages
from app.llm.provider import get_llm_provider
from app.rag.retrieval import format_context_for_llm, retrieve_relevant_chunks
from app.safety.policy import SafetyChecker, SafetyDecision, SafetyResult

logger = get_logger(__name__)


class AgentResult:
    """Result from an agent."""

    def __init__(self, success: bool, data: dict[str, Any], error: str | None = None) -> None:
        self.success = success
        self.data = data
        self.error = error


class RetrieverAgent:
    """Agent responsible for retrieving relevant context."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, query: str) -> AgentResult:
        """Retrieve relevant chunks for the query."""
        try:
            logger.info("RetrieverAgent executing", query_length=len(query))

            results = retrieve_relevant_chunks(self.db, query)

            if not results:
                logger.warning("No relevant chunks found")
                return AgentResult(
                    success=False,
                    data={},
                    error="No relevant information found in knowledge base",
                )

            context = format_context_for_llm(results)

            logger.info("RetrieverAgent complete", num_results=len(results))
            return AgentResult(
                success=True,
                data={
                    "context": context,
                    "retrieval_results": [r.to_dict() for r in results],
                },
            )

        except Exception as e:
            logger.error("RetrieverAgent failed", error=str(e))
            return AgentResult(success=False, data={}, error=str(e))


class DraftAgent:
    """Agent responsible for drafting the initial response."""

    def __init__(self) -> None:
        self.llm = get_llm_provider()

    def execute(self, query: str, context: str) -> AgentResult:
        """Draft a response based on query and context."""
        try:
            logger.info("DraftAgent executing", query_length=len(query))

            messages = create_chat_messages(query, context)
            response = self.llm.generate(messages)

            logger.info("DraftAgent complete", response_length=len(response))
            return AgentResult(
                success=True,
                data={"draft_response": response},
            )

        except Exception as e:
            logger.error("DraftAgent failed", error=str(e))
            return AgentResult(success=False, data={}, error=str(e))


class SafetyAgent:
    """Agent responsible for safety checks."""

    def __init__(self) -> None:
        self.checker = SafetyChecker()

    def check_input(self, query: str) -> SafetyResult:
        """Check input for safety issues."""
        logger.info("SafetyAgent checking input")
        return self.checker.check_input(query)

    def check_output(self, response: str) -> SafetyResult:
        """Check output for safety issues."""
        logger.info("SafetyAgent checking output")
        return self.checker.check_output(response)


class FinalizerAgent:
    """Agent responsible for finalizing the response."""

    def execute(
        self,
        draft_response: str,
        retrieval_results: list[dict[str, Any]],
        safety_result: SafetyResult,
    ) -> AgentResult:
        """Finalize the response with citations and metadata."""
        try:
            logger.info("FinalizerAgent executing")

            # Extract citations from retrieval results
            citations = []
            for i, result in enumerate(retrieval_results, 1):
                citation = {
                    "source_number": i,
                    "document_title": result["document_title"],
                    "section": result["metadata"].get("section_heading", ""),
                    "snippet": result["chunk_text"][:200] + "..."
                    if len(result["chunk_text"]) > 200
                    else result["chunk_text"],
                }
                citations.append(citation)

            final_data = {
                "answer": draft_response,
                "citations": citations,
                "safety_outcome": safety_result.decision.value,
                "safety_reason": safety_result.reason_code.value,
            }

            logger.info("FinalizerAgent complete", num_citations=len(citations))
            return AgentResult(success=True, data=final_data)

        except Exception as e:
            logger.error("FinalizerAgent failed", error=str(e))
            return AgentResult(success=False, data={}, error=str(e))


class ChatOrchestrator:
    """Orchestrator for the multi-agent chat pipeline."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.retriever = RetrieverAgent(db)
        self.drafter = DraftAgent()
        self.safety = SafetyAgent()
        self.finalizer = FinalizerAgent()

    def process_query(self, query: str) -> dict[str, Any]:
        """Process a user query through the agent pipeline."""
        logger.info("ChatOrchestrator starting", query_length=len(query))

        # Step 1: Safety check on input
        input_safety = self.safety.check_input(query)
        if input_safety.decision != SafetyDecision.OK:
            logger.warning(
                "Input failed safety check",
                decision=input_safety.decision.value,
                reason=input_safety.reason_code.value,
            )
            return {
                "answer": input_safety.override_response or "Your request cannot be processed.",
                "citations": [],
                "safety_outcome": input_safety.decision.value,
                "safety_reason": input_safety.reason_code.value,
            }

        # Step 2: Retrieve relevant context
        retrieval_result = self.retriever.execute(query)
        if not retrieval_result.success:
            logger.warning("Retrieval failed", error=retrieval_result.error)
            return {
                "answer": "I couldn't find relevant information in the knowledge base. "
                "Could you please rephrase your question or provide more details?",
                "citations": [],
                "safety_outcome": "ok",
                "safety_reason": "safe",
            }

        # Step 3: Draft response
        draft_result = self.drafter.execute(query, retrieval_result.data["context"])
        if not draft_result.success:
            logger.error("Draft failed", error=draft_result.error)
            return {
                "answer": "I apologize, but I encountered an error generating a response. Please try again.",
                "citations": [],
                "safety_outcome": "ok",
                "safety_reason": "safe",
            }

        # Step 4: Safety check on output
        output_safety = self.safety.check_output(draft_result.data["draft_response"])
        if output_safety.decision != SafetyDecision.OK:
            logger.warning(
                "Output failed safety check",
                decision=output_safety.decision.value,
                reason=output_safety.reason_code.value,
            )
            return {
                "answer": output_safety.override_response or "I cannot provide that information.",
                "citations": [],
                "safety_outcome": output_safety.decision.value,
                "safety_reason": output_safety.reason_code.value,
            }

        # Step 5: Finalize response
        final_result = self.finalizer.execute(
            draft_result.data["draft_response"],
            retrieval_result.data["retrieval_results"],
            output_safety,
        )

        if not final_result.success:
            logger.error("Finalization failed", error=final_result.error)
            return {
                "answer": draft_result.data["draft_response"],
                "citations": [],
                "safety_outcome": "ok",
                "safety_reason": "safe",
            }

        logger.info("ChatOrchestrator complete")
        return final_result.data
