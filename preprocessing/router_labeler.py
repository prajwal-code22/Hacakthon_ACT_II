"""
router_labeler.py
===================
Orchestrates feature_extractor + intent_classifier + complexity into a single
labeled record per query, and adds the remaining pieces the spec calls for:

    - estimated_input_tokens / estimated_output_tokens
    - local_model_confidence (0-1)
    - recommended_route (LOCAL / CLOUD), via heuristic combination of
      complexity_score, local_model_confidence, and safety-critical overrides
      (destructive commands, privacy-sensitive content)

This is the single public entry point most callers need: build_record().
"""

from typing import Optional
from config import (
    INTENT_DEFAULT_PROFILE,
    THRESHOLDS,
    TOKEN_ESTIMATION,
    COMPLEXITY_KEYWORDS,
)
from feature_extractor import extract_text_stats, extract_binary_features
from intent_classifier import classify_intent
from complexity import compute_complexity_score, tier_from_score

# Destructive / high-risk keyword list reused from earlier Linux-focused work.
# Kept here (not in config.py's general keyword sets) since it triggers a
# hard safety override on the route decision, not a soft scoring signal.
DESTRUCTIVE_OVERRIDE_KEYWORDS = [
    "rm -rf", "delete all", "format the disk", "format c:", "dd if=", "chmod -r 777",
    "kill -9 all", "shutdown now", "drop table", "drop database", "truncate table",
    "mkfs", "wipe the drive",
]

# Simple privacy heuristic: queries that look like they contain personal /
# sensitive data should prefer LOCAL (data stays on-device) regardless of
# complexity — this is a common real-world routing consideration.
PRIVACY_SENSITIVE_KEYWORDS = [
    "my password", "my ssn", "my social security", "my credit card",
    "my medical record", "confidential", "internal only",
]


def estimate_input_tokens(query: str, context: Optional[str] = None) -> int:
    """Rough token estimate using chars-per-token heuristic (no tokenizer dependency)."""
    text = f"{query or ''} {context or ''}".strip()
    return max(1, round(len(text) / TOKEN_ESTIMATION["chars_per_token"]))


def estimate_output_tokens(intent: str, features: dict) -> int:
    """
    Estimate output length using the intent's typical_output_length prior,
    bumped up if requires_long_output or requires_structured_output fired.
    """
    profile = INTENT_DEFAULT_PROFILE.get(intent, INTENT_DEFAULT_PROFILE["general"])
    base = TOKEN_ESTIMATION["output_length_token_map"][profile["typical_output_length"]]

    if features.get("requires_long_output"):
        base = max(base, TOKEN_ESTIMATION["output_length_token_map"]["long"])
    if features.get("requires_structured_output"):
        base = round(base * 1.2)

    return round(base)


def estimate_local_model_confidence(intent: str, complexity_score: float, features: dict) -> float:
    """
    Estimate how confident we are that a small local model (e.g. Gemma) can
    handle this query well, as a 0-1 score.

    Starts from the intent's base_local_confidence prior, then adjusts down
    for signals that make local execution riskier (high complexity, requires
    external/current knowledge, requires long or structured generation).
    """
    profile = INTENT_DEFAULT_PROFILE.get(intent, INTENT_DEFAULT_PROFILE["general"])
    confidence = profile["base_local_confidence"]

    # Complexity directly erodes confidence — the higher the complexity,
    # the less we trust a small model to handle it well.
    confidence -= complexity_score * 0.35

    if features.get("requires_external_knowledge"):
        confidence -= 0.20   # local models can't browse/verify current facts
    if features.get("requires_long_output"):
        confidence -= 0.10
    if features.get("requires_structured_output"):
        confidence -= 0.05
    if features.get("contains_multiple_questions"):
        confidence -= 0.05
    if features.get("requires_caution"):
        confidence -= 0.15   # risky-sounding operations warrant more caution before local execution

    return round(max(0.0, min(confidence, 1.0)), 2)


def _check_destructive(combined_text: str) -> bool:
    text = combined_text.lower()
    return any(kw in text for kw in DESTRUCTIVE_OVERRIDE_KEYWORDS)


def _check_privacy_sensitive(combined_text: str) -> bool:
    text = combined_text.lower()
    return any(kw in text for kw in PRIVACY_SENSITIVE_KEYWORDS)


def predict_route(
    complexity_score: float,
    local_model_confidence: float,
    is_destructive: bool,
    is_privacy_sensitive: bool,
) -> tuple:
    """
    Heuristic route decision. Returns (route, reason_string).

    Priority order:
        1. Destructive commands -> always CLOUD (stronger reasoning/safety
           judgment needed before executing anything irreversible).
        2. Privacy-sensitive content -> always LOCAL (keep sensitive data
           on-device rather than sending to a cloud API).
        3. Otherwise, blend complexity_score and (1 - local_model_confidence)
           into a single "cloud_pressure" score rather than an OR of two
           independent cutoffs. An OR-based rule routes to CLOUD if EITHER
           signal is even mildly elevated, which over-triggers CLOUD for
           routine queries (e.g. a simple greeting with middling confidence
           would get pushed to CLOUD by low confidence alone). Blending
           the two signals into one weighted score is more forgiving of a
           single weak signal while still escalating when both agree.
    """
    if is_destructive:
        return "CLOUD", "Destructive/high-risk operation requires cloud-level safety judgment."

    if is_privacy_sensitive:
        return "LOCAL", "Privacy-sensitive content routed to local model to avoid cloud exposure."

    cloud_pressure = complexity_score * 0.6 + (1 - local_model_confidence) * 0.4

    if cloud_pressure >= THRESHOLDS["route_cloud_pressure_cutoff"]:
        return "CLOUD", f"cloud_pressure={cloud_pressure:.2f} (complexity={complexity_score:.2f}, local_confidence={local_model_confidence:.2f}) favors cloud."

    return "LOCAL", f"cloud_pressure={cloud_pressure:.2f} (complexity={complexity_score:.2f}, local_confidence={local_model_confidence:.2f}) favors local."


def build_record(query: str, context: Optional[str] = None, style: str = "unspecified") -> dict:
    """
    The main entry point. Given a raw query (and optional context), produce
    a fully labeled routing record.

    This function is dataset-agnostic — it only needs a query string. Any
    dataset loader (Dolly, Alpaca, OASST, UltraChat, your own Linux corpus)
    can call this directly; see converter.py for the per-dataset glue.
    """
    stats = extract_text_stats(query, context)
    features = extract_binary_features(query, context)
    intent_result = classify_intent(query, context)
    intent = intent_result["intent"]

    complexity_score = compute_complexity_score(intent, stats, features)
    expected_tier = tier_from_score(complexity_score)

    input_tokens = estimate_input_tokens(query, context)
    output_tokens = estimate_output_tokens(intent, features)

    local_confidence = estimate_local_model_confidence(intent, complexity_score, features)

    is_destructive = _check_destructive(stats["combined_text"])
    is_privacy_sensitive = _check_privacy_sensitive(stats["combined_text"])

    route, reason = predict_route(complexity_score, local_confidence, is_destructive, is_privacy_sensitive)

    profile = INTENT_DEFAULT_PROFILE.get(intent, INTENT_DEFAULT_PROFILE["general"])

    record = {
        "query": query,
        "intent": intent,
        "intent_confidence": intent_result["confidence"],
        "expected_tier": expected_tier,
        "style": style,
        "complexity_score": complexity_score,
        "reasoning_required": features["requires_reasoning"],
        "coding_required": features["requires_code"] or profile["coding_required"],
        "math_required": features["requires_math"] or profile["math_required"],
        "creativity_required": features["requires_creativity"] or profile["creativity_required"],
        "requires_context": features["requires_context"],
        "requires_external_knowledge": features["requires_external_knowledge"],
        "requires_translation": features["requires_translation"],
        "requires_generation": features["requires_generation"],
        "requires_structured_output": features["requires_structured_output"],
        "requires_long_output": features["requires_long_output"],
        "contains_numbers": features["contains_numbers"],
        "contains_code_block": features["contains_code_block"],
        "contains_url": features["contains_url"],
        "contains_table": features["contains_table"],
        "contains_list": features["contains_list"],
        "contains_constraints": features["contains_constraints"],
        "contains_multiple_questions": features["contains_multiple_questions"],
        "contains_examples": features["contains_examples"],
        "contains_dates": features["contains_dates"],
        "contains_files": features["contains_files"],
        "requires_caution": features["requires_caution"],
        "destructive": is_destructive,
        "privacy_sensitive": is_privacy_sensitive,
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
        "local_model_confidence": local_confidence,
        "recommended_route": route,
        "explanation": reason,
    }
    return record
