from pathlib import Path
import torch
import joblib

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)


class RouterModel:

    def __init__(self):

        model_dir = Path(__file__).resolve().parent.parent / "router_model"

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)

        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_dir
        ).to(self.device)

        self.model.eval()

        self.route_encoder = joblib.load(
            model_dir / "route_encoder.joblib"
        )

        self.intent_encoder = joblib.load(
            model_dir / "intent_encoder.joblib"
        )

        print("✓ Router model loaded")

    @torch.no_grad()
    def predict(self, query: str):

        inputs = self.tokenizer(
            query,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128,
        )

        inputs = {
            k: v.to(self.device)
            for k, v in inputs.items()
        }

        outputs = self.model(**inputs)

        probs = torch.softmax(outputs.logits, dim=1)

        confidence, pred = torch.max(probs, dim=1)

        pred = pred.item()
        confidence = confidence.item()

        route = self.route_encoder.inverse_transform([pred])[0]

        return {
            "query": query,
            "route": route,
            "score": round(confidence, 4),
            "prediction_id": pred,
        }


_router = None


def initialize_models():

    global _router

    if _router is None:
        _router = RouterModel()

    return _router