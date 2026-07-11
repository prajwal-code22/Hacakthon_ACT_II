"""
intent_classifier.py
======================
Heuristic intent classification across 60+ intents (see config.INTENT_KEYWORDS).

Method (no ML, fully deterministic):
    1. For each candidate intent, count keyword/phrase hits in the query+context.
    2. Add bonus points for any regex pattern matches defined in
       config.INTENT_REGEX (used for syntactically distinctive intents like
       SQL, code, math).
    3. Pick the highest-scoring intent. Ties are broken by a fixed priority
       order (more specific intents win over generic ones like
       "question_answering" or "conversation").
    4. If no intent scores above zero, fall back to "general".

This is intentionally simple and fully auditable — every score can be
traced back to which keywords/regex fired, which matters for a hackathon
demo where you may need to explain *why* a query was classified a certain way.
"""

import re
from typing import Optional
from config import INTENT_KEYWORDS, INTENT_REGEX

_COMPILED_INTENT_REGEX = {
    intent: [re.compile(pat, re.IGNORECASE) for pat in patterns]
    for intent, patterns in INTENT_REGEX.items()
}

# Pre-compile a word-boundary regex per keyword, per intent. Using \b...\b
# instead of a naive substring check prevents false positives like the
# keyword "hi" matching inside "this" or "chip".
_COMPILED_KEYWORDS = {
    intent: [re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE) for kw in keywords]
    for intent, keywords in INTENT_KEYWORDS.items()
}

# Intents that should lose tie-breaks against more specific matches.
# (e.g. a query matching both "coding" and "question_answering" keywords
# should be classified as "coding" — it's the more actionable/specific label.)
_GENERIC_INTENTS = {"question_answering", "conversation", "small_talk", "general", "opinion", "greeting"}

REGEX_MATCH_BONUS = 2  # extra score points per matching regex pattern


def _score_intent(intent: str, combined_lower: str, combined_raw: str) -> int:
    """Compute the keyword+regex match score for a single intent."""
    score = sum(1 for pattern in _COMPILED_KEYWORDS.get(intent, []) if pattern.search(combined_lower))

    for pattern in _COMPILED_INTENT_REGEX.get(intent, []):
        if pattern.search(combined_raw):
            score += REGEX_MATCH_BONUS

    return score


def classify_intent(query: str, context: Optional[str] = None) -> dict:
    """
    Classify a query into one of 60+ intents.

    Returns:
        {
            "intent": str,                 # winning intent label
            "confidence": float,           # 0-1, normalized top score vs runner-up
            "scores": dict,                # full per-intent score breakdown (debug use)
        }
    """
    query = query or ""
    context = context or ""
    combined_raw = f"{query} {context}".strip()
    combined_lower = combined_raw.lower()

    scores = {
        intent: _score_intent(intent, combined_lower, combined_raw)
        for intent in INTENT_KEYWORDS
    }

    max_score = max(scores.values()) if scores else 0

    if max_score == 0:
        return {"intent": "general", "confidence": 0.3, "scores": scores}

    # Collect all intents tied at the max score, prefer non-generic ones
    top_intents = [i for i, s in scores.items() if s == max_score]
    specific_top = [i for i in top_intents if i not in _GENERIC_INTENTS]
    winner = specific_top[0] if specific_top else top_intents[0]

    # Confidence: how dominant the winning score is vs the next-best distinct score
    sorted_scores = sorted(set(scores.values()), reverse=True)
    runner_up = sorted_scores[1] if len(sorted_scores) > 1 else 0
    spread = max_score - runner_up
    confidence = min(1.0, 0.5 + spread * 0.15)  # heuristic: bigger spread = more confident

    return {"intent": winner, "confidence": round(confidence, 2), "scores": scores}
