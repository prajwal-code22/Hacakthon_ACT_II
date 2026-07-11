"""
analyze_route_skew.py
=======================
Analyzes skew in a labeled routing dataset (JSON or CSV) from two angles:

  1. CLASS SKEW — how imbalanced is LOCAL vs CLOUD? Reported as:
     - raw counts / percentages
     - imbalance ratio (majority : minority)
     - Bernoulli skewness coefficient: treats route as a 0/1 variable
       (CLOUD=1) and computes the actual statistical skewness of that
       binary distribution. Positive = skewed toward LOCAL (more common),
       negative = skewed toward CLOUD.

  2. COMPLEXITY SCORE SKEW — the standard Fisher-Pearson skewness
     coefficient of the continuous complexity_score column, which tells
     you whether most queries cluster at the low-complexity end with a
     long tail of hard ones (positive skew), or vice versa.

No external dependencies beyond the standard library — works with or
without pandas/scipy installed.

Usage:
    python analyze_route_skew.py path/to/dataset.json
    python analyze_route_skew.py path/to/dataset.csv
"""

import json
import csv
import sys
import math
from collections import Counter, defaultdict


def load_records(filepath: str) -> list:
    if filepath.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    elif filepath.endswith(".csv"):
        with open(filepath, "r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    else:
        raise ValueError("File must be .json or .csv")


def _get_route(record: dict) -> str:
    """Support both the newer 'recommended_route' field and the older 'route' field."""
    return record.get("recommended_route") or record.get("route") or "UNKNOWN"


def _get_complexity(record: dict):
    val = record.get("complexity_score")
    if val is None or val == "":
        return None
    return float(val)


def bernoulli_skewness(p: float) -> float:
    """
    Skewness of a Bernoulli(p) distribution: (1 - 2p) / sqrt(p * (1-p)).
    p = proportion of the class coded as 1 (here: CLOUD).

    Interpretation:
        skew > 0  -> distribution skewed toward 0 (LOCAL is the majority)
        skew < 0  -> distribution skewed toward 1 (CLOUD is the majority)
        skew == 0 -> perfectly balanced (p = 0.5)
    Larger |skew| = more imbalanced.
    """
    if p <= 0 or p >= 1:
        return float("inf") if 0 < p < 1 else 0.0
    return (1 - 2 * p) / math.sqrt(p * (1 - p))


def fisher_pearson_skewness(values: list) -> float:
    """
    Standard (sample) Fisher-Pearson skewness coefficient for a list of
    continuous values (here: complexity_score).

        skew > 0  -> long tail toward higher values (most scores are low,
                     a few are very high — i.e. most queries look simple,
                     a minority are genuinely complex)
        skew < 0  -> long tail toward lower values
        skew == 0 -> symmetric distribution
    """
    n = len(values)
    if n < 3:
        return 0.0
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance)
    if std == 0:
        return 0.0
    m3 = sum((x - mean) ** 3 for x in values) / n
    return m3 / (std ** 3)


def analyze(filepath: str= r"C:\Users\ASUS\Desktop\Hacakthon ACT II\Hacakthon_ACT_II\unified_route_dataset.json") -> None:
    records = load_records(filepath)
    n = len(records)
    print(f"Loaded {n} records from {filepath}\n")

    # ── 1. Overall class skew ────────────────────────────────────────
    routes = [_get_route(r) for r in records]
    counts = Counter(routes)
    local_n = counts.get("LOCAL", 0)
    cloud_n = counts.get("CLOUD", 0)
    total = local_n + cloud_n

    print("=" * 60)
    print("CLASS SKEW: LOCAL vs CLOUD")
    print("=" * 60)
    if total == 0:
        print("No LOCAL/CLOUD labeled records found.")
    else:
        local_pct = local_n / total * 100
        cloud_pct = cloud_n / total * 100
        majority, minority = (local_n, cloud_n) if local_n >= cloud_n else (cloud_n, local_n)
        imbalance_ratio = majority / minority if minority > 0 else float("inf")

        p_cloud = cloud_n / total
        skew = bernoulli_skewness(p_cloud)

        print(f"LOCAL:  {local_n:>7} ({local_pct:5.1f}%)")
        print(f"CLOUD:  {cloud_n:>7} ({cloud_pct:5.1f}%)")
        print(f"Imbalance ratio (majority:minority): {imbalance_ratio:.2f} : 1")
        print(f"Bernoulli skewness coefficient: {skew:+.3f}")
        if skew > 0.5:
            print("  -> Strongly skewed toward LOCAL")
        elif skew > 0.1:
            print("  -> Mildly skewed toward LOCAL")
        elif skew < -0.5:
            print("  -> Strongly skewed toward CLOUD")
        elif skew < -0.1:
            print("  -> Mildly skewed toward CLOUD")
        else:
            print("  -> Roughly balanced")

    # ── 2. Complexity score distribution skew ────────────────────────
    scores = [s for s in (_get_complexity(r) for r in records) if s is not None]
    print("\n" + "=" * 60)
    print("COMPLEXITY_SCORE DISTRIBUTION SKEW")
    print("=" * 60)
    if len(scores) < 3:
        print("Not enough complexity_score values to compute skewness.")
    else:
        mean = sum(scores) / len(scores)
        sorted_scores = sorted(scores)
        median = sorted_scores[len(scores) // 2]
        skew = fisher_pearson_skewness(scores)

        print(f"n = {len(scores)}")
        print(f"mean   = {mean:.3f}")
        print(f"median = {median:.3f}")
        print(f"min    = {min(scores):.3f}   max = {max(scores):.3f}")
        print(f"Fisher-Pearson skewness: {skew:+.3f}")
        if skew > 0.5:
            print("  -> Right-skewed: most queries are low-complexity, with a long tail of hard ones")
        elif skew < -0.5:
            print("  -> Left-skewed: most queries are high-complexity, with a tail of easy ones")
        else:
            print("  -> Roughly symmetric complexity distribution")

    # ── 3. Per-source breakdown (if source_dataset / style field present) ─
    source_field = None
    if records and "source_dataset" in records[0]:
        source_field = "source_dataset"
    elif records and "style" in records[0]:
        source_field = "style"

    if source_field:
        print("\n" + "=" * 60)
        print(f"PER-{source_field.upper()} BREAKDOWN")
        print("=" * 60)
        by_source = defaultdict(lambda: {"LOCAL": 0, "CLOUD": 0})
        for r in records:
            src = r.get(source_field, "unknown")
            route = _get_route(r)
            if route in ("LOCAL", "CLOUD"):
                by_source[src][route] += 1

        for src, c in sorted(by_source.items(), key=lambda x: -(x[1]["LOCAL"] + x[1]["CLOUD"])):
            tot = c["LOCAL"] + c["CLOUD"]
            if tot == 0:
                continue
            p_cloud_src = c["CLOUD"] / tot
            src_skew = bernoulli_skewness(p_cloud_src)
            print(f"{src:20s} LOCAL={c['LOCAL']:>6} ({c['LOCAL']/tot*100:5.1f}%)  "
                  f"CLOUD={c['CLOUD']:>6} ({c['CLOUD']/tot*100:5.1f}%)  skew={src_skew:+.2f}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_route_skew.py path/to/dataset.json")
        sys.exit(1)
    analyze(sys.argv[1])