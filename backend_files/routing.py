"""Business routing, independent of models and network services."""
import math

WEIGHTS = {
    "Faithfulness": 0.35,
    "Contextual Recall": 0.25,
    "Contextual Precision": 0.20,
    "Answer Relevancy": 0.20,
}
THRESHOLDS = {
    "Faithfulness": 0.85,
    "Contextual Recall": 0.80,
    "Contextual Precision": 0.75,
    "Answer Relevancy": 0.75,
}


def route_scores(scores):
    """Never invent a missing judge score or treat it as a passing score."""
    valid = all(
        isinstance(scores.get(name), (int, float))
        and not isinstance(scores[name], bool)
        and math.isfinite(scores[name])
        and -1e-12 <= scores[name] <= 1 + 1e-12
        for name in WEIGHTS
    )
    if not valid:
        return {"composite_score": None, "route": "MANUAL LOOKUP",
                "reason": "A required evaluation score is unavailable or invalid."}
    # Native judge probability arithmetic can yield 1 + machine epsilon.
    # Clamp only after validating the tight numerical tolerance above.
    composite = sum(WEIGHTS[name] * min(1.0, max(0.0, scores[name])) for name in WEIGHTS)
    return {
        "composite_score": composite,
        "route": "AUTO ANSWER" if composite >= 0.75 else "MANUAL LOOKUP",
        "reason": "Weighted composite meets 0.75." if composite >= 0.75
                  else "Weighted composite is below 0.75.",
    }
