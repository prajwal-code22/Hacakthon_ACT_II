"""
predictor.py
-------------
Predictor class — runs a single forward pass through MultiTaskRouter
and returns route, intent, confidence, and complexity.
"""

import logging
from typing import TypedDict

import torch

from initialize_model import RouterModelSingleton, initialize_models

logger = logging.getLogger(__name__)


# ── Return type ────────────────────────────────────────────────────────────
class PredictionResult(TypedDict):
    route: str        # "LOCAL" | "CLOUD"
    intent: str       # e.g. "linux_command"
    confidence: float # softmax probability of the predicted route class [0, 1]
    complexity: float # sigmoid output from the complexity head [0, 1]


# ── Predictor ──────────────────────────────────────────────────────────────
class Predictor:
    """
    Stateless predictor.

    Uses the shared RouterModelSingleton (loaded once at startup) to
    tokenise a query, run inference, and decode the three model outputs.
    """

    def __init__(self) -> None:
        self._router: RouterModelSingleton = initialize_models()
        logger.info("Predictor initialised ✅")

    @torch.no_grad()
    def predict(self, query: str) -> PredictionResult:
        """
        Classify *query* and return a routing prediction.

        Parameters
        ----------
        query : str
            Raw user query text.

        Returns
        -------
        PredictionResult
            route      – "LOCAL" or "CLOUD"
            intent     – human-readable intent label
            confidence – probability assigned to the predicted route class
            complexity – complexity score from the dedicated sigmoid head
        """
        # 1. Tokenise
        inputs = self._router.tokenizer(
            query,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128,
        )
        inputs = {k: v.to(self._router.device) for k, v in inputs.items()}

        # 2. Forward pass — returns dict with three tensors
        outputs = self._router.model(**inputs)
        #   outputs["route_logits"]   shape (1, 2)
        #   outputs["intent_logits"]  shape (1, 62)
        #   outputs["complexity_pred"] shape (1,)

        # 3. Route: softmax → confidence + class index
        route_probs  = torch.softmax(outputs["route_logits"], dim=1)
        route_conf, route_idx = torch.max(route_probs, dim=1)

        # 4. Intent: argmax
        intent_idx = torch.argmax(outputs["intent_logits"], dim=1)

        # 5. Complexity: direct sigmoid scalar
        complexity = float(outputs["complexity_pred"].item())

        # 6. Decode labels
        route  = self._router.route_encoder.inverse_transform([route_idx.item()])[0]
        intent = self._router.intent_encoder.inverse_transform([intent_idx.item()])[0]

        result: PredictionResult = {
            "route":      route,
            "intent":     intent,
            "confidence": round(float(route_conf.item()), 4),
            "complexity": round(complexity, 4),
        }

        logger.info(
            "Predicted → route=%s conf=%.2f%% intent=%s complexity=%.2f",
            result["route"],
            result["confidence"] * 100,
            result["intent"],
            result["complexity"],
        )
        return result
