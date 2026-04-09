"""Evaluation metrics for retrieval quality."""

import sys
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.logging import get_logger, setup_logging
from app.db.session import SessionLocal
from app.eval.datasets import RETRIEVAL_EVAL_DATASET
from app.rag.retrieval import retrieve_relevant_chunks

setup_logging()
logger = get_logger(__name__)


def calculate_hit_at_k(retrieved_titles: list[str], expected_titles: list[str], k: int) -> bool:
    """Calculate if any expected document is in top-k results."""
    retrieved_top_k = retrieved_titles[:k]
    for expected in expected_titles:
        if any(expected.lower() in title.lower() for title in retrieved_top_k):
            return True
    return False


def evaluate_retrieval() -> dict[str, Any]:
    """Evaluate retrieval performance."""
    logger.info("Starting retrieval evaluation")

    db = SessionLocal()
    results = []
    hit_at_1_count = 0
    hit_at_3_count = 0
    hit_at_5_count = 0
    total = len(RETRIEVAL_EVAL_DATASET)

    try:
        for item in RETRIEVAL_EVAL_DATASET:
            query = item["query"]
            expected_titles = item["expected_doc_titles"]
            category = item["category"]

            logger.info("Evaluating query", query=query, category=category)

            # Retrieve chunks
            retrieved_chunks = retrieve_relevant_chunks(db, query, top_k=5)
            retrieved_titles = [chunk.document_title for chunk in retrieved_chunks]

            # Calculate metrics
            hit_at_1 = calculate_hit_at_k(retrieved_titles, expected_titles, k=1)
            hit_at_3 = calculate_hit_at_k(retrieved_titles, expected_titles, k=3)
            hit_at_5 = calculate_hit_at_k(retrieved_titles, expected_titles, k=5)

            if hit_at_1:
                hit_at_1_count += 1
            if hit_at_3:
                hit_at_3_count += 1
            if hit_at_5:
                hit_at_5_count += 1

            result = {
                "query": query,
                "category": category,
                "expected_titles": expected_titles,
                "retrieved_titles": retrieved_titles[:5],
                "hit_at_1": hit_at_1,
                "hit_at_3": hit_at_3,
                "hit_at_5": hit_at_5,
                "num_retrieved": len(retrieved_chunks),
            }
            results.append(result)

            logger.info(
                "Query evaluated",
                query=query,
                hit_at_1=hit_at_1,
                hit_at_3=hit_at_3,
                hit_at_5=hit_at_5,
            )

    finally:
        db.close()

    # Calculate aggregate metrics
    metrics = {
        "total_queries": total,
        "hit_at_1": hit_at_1_count / total if total > 0 else 0,
        "hit_at_3": hit_at_3_count / total if total > 0 else 0,
        "hit_at_5": hit_at_5_count / total if total > 0 else 0,
        "detailed_results": results,
    }

    logger.info("Retrieval evaluation complete", metrics=metrics)
    return metrics


def print_report(metrics: dict[str, Any]) -> None:
    """Print evaluation report."""
    print("\n" + "=" * 50)
    print("RETRIEVAL EVALUATION REPORT")
    print("=" * 50)
    print(f"\nTotal Queries: {metrics['total_queries']}")
    print(f"Hit@1: {metrics['hit_at_1']:.2%}")
    print(f"Hit@3: {metrics['hit_at_3']:.2%}")
    print(f"Hit@5: {metrics['hit_at_5']:.2%}")

    print("\n" + "-" * 50)
    print("DETAILED RESULTS")
    print("-" * 50)

    for result in metrics["detailed_results"]:
        print(f"\nQuery: {result['query']}")
        print(f"Category: {result['category']}")
        print(f"Expected: {', '.join(result['expected_titles'])}")
        print(f"Retrieved: {', '.join(result['retrieved_titles'][:3])}")
        print(
            f"Hit@1: {result['hit_at_1']}, Hit@3: {result['hit_at_3']}, Hit@5: {result['hit_at_5']}"
        )

    print("\n" + "=" * 50)


if __name__ == "__main__":
    metrics = evaluate_retrieval()
    print_report(metrics)
