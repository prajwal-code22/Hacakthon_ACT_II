"""
complexity.py
==============
Computes a single complexity_score (0.0-1.0) from many independent signals:
    - raw text length (words, sentences)
    - number of questions asked in one query
    - context length (longer context = more to reason over)
    - keyword-weighted signals (reasoning / coding / math / planning / vague)
    - intent's own base_complexity prior (from config.INTENT_DEFAULT_PROFILE)
    - binary feature flags from feature_extractor (requires_reasoning, etc.)

No machine learning — every signal is a transparent, weighted heuristic.
Weights live in WEIGHTS below so they're easy to tune without touching logic.
"""

from typing import Optional
from config import THRESHOLDS, INTENT_DEFAULT_PROFILE

# Weight given to each signal group when summing into the final 0-1 score.
# These should sum to roughly 1.0 across the "always contributes" signals;
# binary feature bonuses are additive on top and clipped at the end.
WEIGHTS = {
    "intent_prior":       0.30,   # base_complexity from the classified intent
    "length_signal":      0.15,   # normalized word count of the query
    "sentence_signal":    0.10,   # normalized sentence count
    "question_signal":    0.10,   # multiple questions = harder to satisfy in one pass
    "context_signal":     0.10,   # longer supplied context = more to process
    "keyword_signal":     0.15,   # reasoning/coding/math/planning keyword density
    "feature_bonus":      0.10,   # sum of binary "requires_*" flags that imply difficulty
}

# Which binary features from feature_extractor bump complexity when True,
# and by how much each contributes to the 0-1 "feature_bonus" bucket.
COMPLEXITY_RAISING_FEATURES = {
    "requires_reasoning": 0.20,
    "requires_code": 0.15,
    "requires_math": 0.15,
    "requires_external_knowledge": 0.15,
    "requires_structured_output": 0.10,
    "requires_long_output": 0.15,
    "requires_creativity": 0.10,
    "contains_multiple_questions": 0.10,
    "contains_constraints": 0.10,
    "requires_caution": 0.20,
}


def _normalize(value: float, cap: float) -> float:
    """Linearly scale value into [0, 1], clipped at `cap`."""
    return max(0.0, min(value / cap, 1.0))


def compute_complexity_score(intent: str, stats: dict, features: dict) -> float:
    """
    Combine all signals into a single complexity score.

    Args:
        intent:   the classified intent string (from intent_classifier)
        stats:    output of feature_extractor.extract_text_stats()
        features: output of feature_extractor.extract_binary_features()

    Returns:
        float in [0.0, 1.0]
    """
    profile = INTENT_DEFAULT_PROFILE.get(intent, INTENT_DEFAULT_PROFILE["general"])
    intent_prior = profile["base_complexity"]

    length_signal = _normalize(stats["word_count"], THRESHOLDS["long_prompt_words"] * 1.5)
    sentence_signal = _normalize(stats["sentence_count"], 6)
    question_signal = _normalize(stats["question_count"], 3)
    context_signal = _normalize(stats["context_word_count"], 200)

    # Keyword density: how many reasoning/coding/math hits per 20 words
    keyword_hit_total = features.get("_reasoning_hits", 0) + features.get("_coding_hits", 0) + features.get("_math_hits", 0)
    keyword_signal = _normalize(keyword_hit_total, 3)

    feature_bonus = sum(
        weight for feat, weight in COMPLEXITY_RAISING_FEATURES.items() if features.get(feat)
    )
    feature_bonus = min(feature_bonus, 1.0)

    score = (
        WEIGHTS["intent_prior"] * intent_prior
        + WEIGHTS["length_signal"] * length_signal
        + WEIGHTS["sentence_signal"] * sentence_signal
        + WEIGHTS["question_signal"] * question_signal
        + WEIGHTS["context_signal"] * context_signal
        + WEIGHTS["keyword_signal"] * keyword_signal
        + WEIGHTS["feature_bonus"] * feature_bonus
    )

    return round(min(max(score, 0.0), 1.0), 3)


def tier_from_score(score: float) -> str:
    """Map a 0-1 complexity_score into 'simple' | 'medium' | 'complex'."""
    if score < THRESHOLDS["tier_simple_max"]:
        return "simple"
    elif score < THRESHOLDS["tier_medium_max"]:
        return "medium"
    return "complex"
