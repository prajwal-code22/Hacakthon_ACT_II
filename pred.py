import torch
import joblib
from transformers import AutoTokenizer
from model_trainer.train_transformer_router import MultiTaskRouter

MODEL_PATH = "./router_model"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

model = MultiTaskRouter.from_pretrained(MODEL_PATH)
model.eval()

route_encoder = joblib.load(
    "./router_model/route_encoder.joblib"
)

query = """
Run hyperparameter optimization across 200 GPUs.
"""

inputs = tokenizer(
    query,
    return_tensors="pt",
    truncation=True,
    padding=True,
)

with torch.no_grad():
    outputs = model(**inputs)

route_id = torch.argmax(
    outputs["route_logits"],
    dim=1
).item()

route = route_encoder.inverse_transform([route_id])[0]

print(f"Predicted Route for {query}", route)