"""
initialize_model.py
--------------------
Loads the MultiTaskRouter model once at startup and exposes a singleton instance.

The model is a custom 3-head transformer (distilbert-base-uncased) that predicts:
  - route_logits      : LOCAL or CLOUD  (binary classification)
  - intent_logits     : one of 62 intents (multi-class classification)
  - complexity_pred   : float in [0, 1]  (sigmoid regression head)
"""

import sys
import logging
from pathlib import Path

import torch
import joblib
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)

# ── Resolve paths ──────────────────────────────────────────────────────────
_BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT  = _BACKEND_DIR.parent
MODEL_DIR     = PROJECT_ROOT / "router_model"

# Make model_trainer importable from the project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import after path fix
from model_trainer.train_transformer_router import (  # noqa: E402
    MultiTaskRouter,
    MultiTaskRouterConfig,
)


# ── Singleton class ────────────────────────────────────────────────────────
class RouterModelSingleton:
    """
    Wraps the MultiTaskRouter for inference.

    Attributes
    ----------
    device        : torch.device  (cpu / cuda)
    tokenizer     : AutoTokenizer
    model         : MultiTaskRouter
    route_encoder : sklearn LabelEncoder  (CLOUD=0, LOCAL=1)
    intent_encoder: sklearn LabelEncoder  (62 intent classes)
    """

    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Loading RouterModel on %s …", self.device)

        if not MODEL_DIR.exists():
            raise FileNotFoundError(
                f"router_model directory not found at {MODEL_DIR}. "
                "Place the trained model folder there and restart."
            )

        # Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))

        # Custom multi-head model — cannot use AutoModelForSequenceClassification
        self.model: MultiTaskRouter = MultiTaskRouter.from_pretrained(str(MODEL_DIR))
        self.model.to(self.device)
        self.model.eval()

        # Label encoders saved alongside the model
        self.route_encoder  = joblib.load(MODEL_DIR / "route_encoder.joblib")
        self.intent_encoder = joblib.load(MODEL_DIR / "intent_encoder.joblib")

        logger.info(
            "✅ RouterModel ready | device=%s | routes=%s | intents=%d",
            self.device,
            list(self.route_encoder.classes_),
            len(self.intent_encoder.classes_),
        )


# ── Module-level singleton ─────────────────────────────────────────────────
_instance: RouterModelSingleton | None = None


def initialize_models() -> RouterModelSingleton:
    """Return the shared RouterModelSingleton, loading it on the first call."""
    global _instance
    if _instance is None:
        _instance = RouterModelSingleton()
    return _instance
