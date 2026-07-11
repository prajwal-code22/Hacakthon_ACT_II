"""
feature_extractor.py
=====================
Domain-agnostic feature extraction. Works on ANY (query, context) pair
regardless of which dataset it came from — this is what makes the pipeline
reusable: only the dataset LOADER changes per source (see converter.py),
this module never does.

Produces two kinds of output:
    1. Raw text statistics (length, sentence count, question count, etc.)
    2. Binary features (contains_url, contains_code_block, requires_math, ...)

No machine learning. Everything here is regex + keyword counting, driven
entirely by the dictionaries in config.py.
"""

import re
from typing import Optional
from config import FEATURE_PATTERNS, COMPLEXITY_KEYWORDS

_COMPILED_PATTERNS = {name: re.compile(pat, re.IGNORECASE) for name, pat in FEATURE_PATTERNS.items()}


def _count_matches(pattern_name: str, text: str) -> int:
    """Count non-overlapping regex matches for a named pattern from config."""
    return len(_COMPILED_PATTERNS[pattern_name].findall(text))


def _keyword_hits(text: str, keywords: list) -> int:
    """Count how many keywords/phrases from a list appear in text as whole words/phrases."""
    return sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE))


def extract_text_stats(query: str, context: Optional[str] = None) -> dict:
    """
    Basic text statistics used downstream by complexity scoring.

    Returns:
        dict with word_count, char_count, sentence_count, question_count,
        context_word_count, combined_text (query + context, for reuse).
    """
    query = query or ""
    context = context or ""
    combined = f"{query} {context}".strip()

    sentence_count = len(re.findall(r"[.!?]+", query)) or 1
    question_count = _count_matches("question", query)

    return {
        "word_count": len(query.split()),
        "char_count": len(query),
        "sentence_count": sentence_count,
        "question_count": question_count,
        "context_word_count": len(context.split()) if context else 0,
        "combined_text": combined,
    }


def extract_binary_features(query: str, context: Optional[str] = None) -> dict:
    """
    Extract the full binary feature set described in the project spec.

    Returns a dict of 20 boolean flags:
        requires_reasoning, requires_context, requires_external_knowledge,
        requires_code, requires_math, requires_translation, requires_generation,
        requires_structured_output, requires_long_output, requires_creativity,
        contains_numbers, contains_code_block, contains_url, contains_table,
        contains_list, contains_constraints, contains_multiple_questions,
        contains_examples, contains_dates, contains_files
    """
    query = query or ""
    context = context or ""
    combined = f"{query} {context}".strip()
    combined_lower = combined.lower()

    # ── Surface-level content flags (regex-driven) ──────────────────────
    contains_code_block = bool(_COMPILED_PATTERNS["code_block"].search(combined))
    contains_url = bool(_COMPILED_PATTERNS["url"].search(combined))
    contains_table = bool(_COMPILED_PATTERNS["table"].search(combined))
    contains_list = bool(_COMPILED_PATTERNS["list"].search(combined))
    contains_numbers = bool(_COMPILED_PATTERNS["number"].search(combined))
    contains_dates = bool(_COMPILED_PATTERNS["date"].search(combined))
    contains_files = bool(_COMPILED_PATTERNS["file_ref"].search(combined))
    contains_constraints = bool(_COMPILED_PATTERNS["constraint"].search(combined))
    contains_examples = bool(_COMPILED_PATTERNS["example_ref"].search(combined))
    contains_multiple_questions = _count_matches("question", query) >= 2

    # ── Derived "requires_*" flags (keyword + surface-feature combos) ───
    reasoning_hits = _keyword_hits(combined_lower, COMPLEXITY_KEYWORDS["reasoning_keywords"])
    coding_hits = _keyword_hits(combined_lower, COMPLEXITY_KEYWORDS["coding_keywords"])
    math_hits = _keyword_hits(combined_lower, COMPLEXITY_KEYWORDS["math_keywords"])

    requires_reasoning = reasoning_hits > 0 or "why" in combined_lower or "explain" in combined_lower
    requires_context = bool(context.strip()) or "based on" in combined_lower or "according to" in combined_lower
    requires_external_knowledge = any(
        term in combined_lower for term in ["current", "latest", "today", "recent", "news", "who is", "what year"]
    )
    requires_code = coding_hits > 0 or contains_code_block
    requires_math = math_hits > 0 or bool(re.search(r"\d+\s*[\+\-\*/\^=]\s*\d+", combined))
    if not requires_math:
        # Catch narrative word problems (e.g. "Natalia sold clips to 48
        # friends... how many did she sell altogether?") that contain no
        # explicit math keywords or symbols, only a story with numbers.
        number_count = _count_matches("number", combined)
        has_word_problem_cue = _keyword_hits(combined_lower, COMPLEXITY_KEYWORDS["math_word_problem_cues"]) > 0
        if number_count >= 2 and has_word_problem_cue and "?" in combined:
            requires_math = True
    requires_translation = any(
        term in combined_lower for term in ["translate", "in spanish", "in french", "in german", "into japanese"]
    )
    requires_generation = any(
        term in combined_lower for term in ["write", "generate", "create", "draft", "compose"]
    )
    requires_structured_output = contains_table or contains_list or any(
        term in combined_lower for term in ["json", "table format", "bullet points", "as a list"]
    )
    word_count = len(query.split())
    requires_long_output = any(
        term in combined_lower for term in ["essay", "detailed", "in depth", "comprehensive", "full report"]
    ) or word_count > 40
    requires_creativity = any(
        term in combined_lower for term in ["story", "poem", "creative", "imagine", "invent", "brainstorm"]
    )
    risk_hits = _keyword_hits(combined_lower, COMPLEXITY_KEYWORDS["risk_keywords"])
    requires_caution = risk_hits > 0

    return {
        "requires_reasoning": requires_reasoning,
        "requires_context": requires_context,
        "requires_external_knowledge": requires_external_knowledge,
        "requires_code": requires_code,
        "requires_math": requires_math,
        "requires_translation": requires_translation,
        "requires_generation": requires_generation,
        "requires_structured_output": requires_structured_output,
        "requires_long_output": requires_long_output,
        "requires_creativity": requires_creativity,
        "requires_caution": requires_caution,
        "contains_numbers": contains_numbers,
        "contains_code_block": contains_code_block,
        "contains_url": contains_url,
        "contains_table": contains_table,
        "contains_list": contains_list,
        "contains_constraints": contains_constraints,
        "contains_multiple_questions": contains_multiple_questions,
        "contains_examples": contains_examples,
        "contains_dates": contains_dates,
        "contains_files": contains_files,
        # exposed for reuse by complexity.py, not part of the official spec list
        "_reasoning_hits": reasoning_hits,
        "_coding_hits": coding_hits,
        "_math_hits": math_hits,
    }


def extract_all_features(query: str, context: Optional[str] = None) -> dict:
    """Convenience wrapper combining text stats + binary features into one dict."""
    stats = extract_text_stats(query, context)
    binary = extract_binary_features(query, context)
    return {**stats, **binary}