"""
train_baseline_router.py
==========================
Fast baseline: TF-IDF + Logistic Regression, predicting route (LOCAL/CLOUD)
directly from the raw query text — NOT from the heuristic features
(complexity_score, intent, etc). This matters: at real inference time,
your router only sees a raw user query, not the labels your heuristic
pipeline computed. So the model must learn to predict route from text alone.

This baseline exists to answer one question before you spend Colab GPU time
on a transformer: "are these heuristic labels even learnable from text?"
If a linear model on bag-of-words gets reasonable accuracy, a transformer
will do noticeably better. If the baseline is near-random, something is
wrong with the labels themselves (check for leakage, check class balance)
before you invest in the bigger model.

Also trains a second baseline for `intent` (62-class) as a secondary check —
useful if you want the router to expose predicted intent alongside route.

Run in Colab or locally: pip install scikit-learn pandas
"""

import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import joblib


import json
import pandas as pd

def load_data(filepath: str) -> pd.DataFrame:
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath)

    elif filepath.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)

    elif filepath.endswith(".jsonl"):
        df = pd.read_json(filepath, lines=True)

    else:
        raise ValueError(f"Unsupported file format: {filepath}")

    # Support both old ('route') and new ('recommended_route')
    if "recommended_route" in df.columns:
        df["route"] = df["recommended_route"]

    df = df.dropna(subset=["query", "route"])
    df = df[df["route"].isin(["LOCAL", "CLOUD"])]

    return df


def train_route_classifier(df: pd.DataFrame, test_size: float = 0.15):
    X_train, X_test, y_train, y_test = train_test_split(
        df["query"], df["route"], test_size=test_size, random_state=42, stratify=df["route"]
    )

    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),      # unigrams + bigrams capture phrases like "write code"
        min_df=2,
        sublinear_tf=True,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(X_train_vec, y_train)

    y_pred = clf.predict(X_test_vec)
    print("=" * 60)
    print("ROUTE CLASSIFIER (LOCAL vs CLOUD)")
    print("=" * 60)
    print(classification_report(y_test, y_pred))
    print("Confusion matrix (rows=actual, cols=predicted), labels=[CLOUD, LOCAL]:")
    print(confusion_matrix(y_test, y_pred, labels=["CLOUD", "LOCAL"]))

    return vectorizer, clf


def train_intent_classifier(df: pd.DataFrame, test_size: float = 0.15):
    if "intent" not in df.columns:
        print("No 'intent' column found, skipping intent classifier.")
        return None, None

    df_intent = df.dropna(subset=["intent"])
    # Drop intents with too few examples to stratify-split cleanly
    counts = df_intent["intent"].value_counts()
    valid_intents = counts[counts >= 5].index
    df_intent = df_intent[df_intent["intent"].isin(valid_intents)]

    X_train, X_test, y_train, y_test = train_test_split(
        df_intent["query"], df_intent["intent"], test_size=test_size,
        random_state=42, stratify=df_intent["intent"]
    )

    vectorizer = TfidfVectorizer(max_features=20000, ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(X_train_vec, y_train)

    y_pred = clf.predict(X_test_vec)
    print("\n" + "=" * 60)
    print(f"INTENT CLASSIFIER ({df_intent['intent'].nunique()} classes)")
    print("=" * 60)
    print(classification_report(y_test, y_pred, zero_division=0))

    return vectorizer, clf


def main(filepath: str):
    df = load_data(filepath)
    print(f"Loaded {len(df)} labeled rows\n")
    print("Route distribution:")
    print(df["route"].value_counts(normalize=True).round(3), "\n")

    route_vectorizer, route_clf = train_route_classifier(df)
    joblib.dump(route_vectorizer, "route_vectorizer.joblib")
    joblib.dump(route_clf, "route_classifier.joblib")
    print("\nSaved route_vectorizer.joblib and route_classifier.joblib")

    intent_vectorizer, intent_clf = train_intent_classifier(df)
    if intent_clf is not None:
        joblib.dump(intent_vectorizer, "intent_vectorizer.joblib")
        joblib.dump(intent_clf, "intent_classifier.joblib")
        print("Saved intent_vectorizer.joblib and intent_classifier.joblib")


if __name__ == "__main__":
    import sys
    filepath = sys.argv[1] if len(sys.argv) > 1 else "unified_route_dataset.json"
    main(filepath)
