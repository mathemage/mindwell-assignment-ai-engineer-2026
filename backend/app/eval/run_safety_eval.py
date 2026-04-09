"""Evaluation script for safety policy."""

import sys
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.logging import get_logger, setup_logging
from app.eval.datasets import SAFETY_EVAL_DATASET
from app.safety.policy import SafetyChecker

setup_logging()
logger = get_logger(__name__)


def evaluate_safety() -> dict[str, Any]:
    """Evaluate safety policy performance."""
    logger.info("Starting safety evaluation")

    checker = SafetyChecker()
    results = []
    correct_decisions = 0
    total = len(SAFETY_EVAL_DATASET)

    for item in SAFETY_EVAL_DATASET:
        input_text = item["input"]
        expected_decision = item["expected_decision"]
        expected_reason = item["expected_reason"]
        category = item["category"]

        logger.info("Evaluating safety check", input=input_text[:50], category=category)

        # Check safety
        result = checker.check_input(input_text)

        # Evaluate
        decision_correct = result.decision.value == expected_decision
        reason_correct = result.reason_code.value == expected_reason

        if decision_correct and reason_correct:
            correct_decisions += 1

        eval_result = {
            "input": input_text,
            "category": category,
            "expected_decision": expected_decision,
            "actual_decision": result.decision.value,
            "expected_reason": expected_reason,
            "actual_reason": result.reason_code.value,
            "decision_correct": decision_correct,
            "reason_correct": reason_correct,
            "override_provided": result.override_response is not None,
        }
        results.append(eval_result)

        logger.info(
            "Safety check evaluated",
            input=input_text[:50],
            decision_correct=decision_correct,
            reason_correct=reason_correct,
        )

    # Calculate metrics
    accuracy = correct_decisions / total if total > 0 else 0

    # Category-specific metrics
    categories = {item["category"] for item in SAFETY_EVAL_DATASET}
    category_metrics = {}

    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        cat_correct = sum(1 for r in cat_results if r["decision_correct"] and r["reason_correct"])
        category_metrics[cat] = {
            "total": len(cat_results),
            "correct": cat_correct,
            "accuracy": cat_correct / len(cat_results) if cat_results else 0,
        }

    metrics = {
        "total_cases": total,
        "correct_decisions": correct_decisions,
        "accuracy": accuracy,
        "category_metrics": category_metrics,
        "detailed_results": results,
    }

    logger.info("Safety evaluation complete", metrics=metrics)
    return metrics


def print_report(metrics: dict[str, Any]) -> None:
    """Print evaluation report."""
    print("\n" + "=" * 50)
    print("SAFETY EVALUATION REPORT")
    print("=" * 50)
    print(f"\nTotal Cases: {metrics['total_cases']}")
    print(f"Correct Decisions: {metrics['correct_decisions']}")
    print(f"Overall Accuracy: {metrics['accuracy']:.2%}")

    print("\n" + "-" * 50)
    print("CATEGORY BREAKDOWN")
    print("-" * 50)

    for category, cat_metrics in metrics["category_metrics"].items():
        print(f"\n{category.upper()}:")
        print(f"  Total: {cat_metrics['total']}")
        print(f"  Correct: {cat_metrics['correct']}")
        print(f"  Accuracy: {cat_metrics['accuracy']:.2%}")

    print("\n" + "-" * 50)
    print("DETAILED RESULTS")
    print("-" * 50)

    for result in metrics["detailed_results"]:
        status = "✓" if (result["decision_correct"] and result["reason_correct"]) else "✗"
        print(f"\n{status} Input: {result['input'][:60]}...")
        print(f"  Category: {result['category']}")
        print(f"  Expected: {result['expected_decision']} ({result['expected_reason']})")
        print(f"  Actual: {result['actual_decision']} ({result['actual_reason']})")
        if not result["decision_correct"] or not result["reason_correct"]:
            print("  ⚠️  Mismatch detected!")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    metrics = evaluate_safety()
    print_report(metrics)
