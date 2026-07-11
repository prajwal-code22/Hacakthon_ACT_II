"""
train_transformer_router.py
=============================
Fine-tunes a small transformer (default: distilbert-base-uncased, ~66M
params — small enough to train on a free Colab GPU in well under an hour
even on 300k rows) with THREE output heads sharing one encoder:

    1. intent_head       -> 62-way classification (which of your intents)
    2. route_head        -> binary classification (LOCAL / CLOUD)
    3. complexity_head    -> regression (0.0-1.0 complexity_score)

This mirrors the dual-head architecture pattern (shared encoder + task
heads) you've already used for the Linux intent/NER model — same idea,
one more head.

Why multi-task instead of three separate models:
    - One shared encoder is cheaper to train and to run at inference time
      (single forward pass gives you all three predictions).
    - Intent and complexity are correlated signals for route — training
      them jointly lets the shared representation pick up on that
      correlation, which usually helps route accuracy too.

Run this in Colab (needs a GPU runtime: Runtime -> Change runtime type -> T4 GPU):
    !pip install transformers datasets torch scikit-learn accelerate -q
    python train_transformer_router.py unified_route_dataset.json
"""

import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from transformers import (
    AutoConfig, AutoTokenizer, AutoModel, Trainer, TrainingArguments,
    PreTrainedModel, PretrainedConfig,
)
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error

MODEL_NAME = "distilbert-base-uncased"   # swap for a smaller model (e.g. "prajjwal1/bert-tiny")
                                          # if you need faster training / smaller deployment size
MAX_LENGTH = 128


# ─────────────────────────────────────────────────────────────────────────
# 1. Load & prepare data
# ─────────────────────────────────────────────────────────────────────────

def load_data(filepath: str) -> pd.DataFrame:
    if filepath.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    else:
        df = pd.read_csv(filepath)

    if "recommended_route" in df.columns:
        df["route"] = df["recommended_route"]

    df = df.dropna(subset=["query", "route", "intent", "complexity_score"])
    df = df[df["route"].isin(["LOCAL", "CLOUD"])]
    df["complexity_score"] = df["complexity_score"].astype(float)
    return df.reset_index(drop=True)


class RouterDataset(Dataset):
    def __init__(self, texts, intent_labels, route_labels, complexity_scores, tokenizer):
        self.encodings = tokenizer(
            list(texts), truncation=True, padding="max_length", max_length=MAX_LENGTH
        )
        self.intent_labels = intent_labels
        self.route_labels = route_labels
        self.complexity_scores = complexity_scores

    def __len__(self):
        return len(self.route_labels)

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["intent_labels"] = torch.tensor(self.intent_labels[idx], dtype=torch.long)
        item["route_labels"] = torch.tensor(self.route_labels[idx], dtype=torch.long)
        item["complexity_labels"] = torch.tensor(self.complexity_scores[idx], dtype=torch.float)
        return item


# ─────────────────────────────────────────────────────────────────────────
# 2. Multi-head model
# ─────────────────────────────────────────────────────────────────────────

class MultiTaskRouterConfig(PretrainedConfig):
    model_type = "multitask_router"

    def __init__(self, base_model_name=MODEL_NAME, num_intents=62, **kwargs):
        super().__init__(**kwargs)
        self.base_model_name = base_model_name
        self.num_intents = num_intents


class MultiTaskRouter(PreTrainedModel):
    """
    Shared transformer encoder + three task-specific heads:
        - intent_head: Linear(hidden, num_intents)      -> classification
        - route_head:  Linear(hidden, 2)                 -> classification (LOCAL/CLOUD)
        - complexity_head: Linear(hidden, 1) + sigmoid   -> regression in [0, 1]

    Loss = intent_loss + route_loss + complexity_loss (equal weighting;
    tune the weights below if one task should matter more for your demo).
    """
    config_class = MultiTaskRouterConfig

    def __init__(self, config: MultiTaskRouterConfig):
        super().__init__(config)
        self.encoder = AutoModel.from_config(
            AutoConfig.from_pretrained(config.base_model_name)
        )
        hidden_size = self.encoder.config.hidden_size

        self.intent_head = nn.Linear(hidden_size, config.num_intents)
        self.route_head = nn.Linear(hidden_size, 2)
        self.complexity_head = nn.Sequential(nn.Linear(hidden_size, 1), nn.Sigmoid())

        self.intent_loss_fn = nn.CrossEntropyLoss()
        self.route_loss_fn = nn.CrossEntropyLoss()
        self.complexity_loss_fn = nn.MSELoss()

        # Loss weights — route is the primary task for the hackathon demo,
        # so it gets a slightly higher weight than the auxiliary tasks.
        self.loss_weights = {"intent": 0.3, "route": 1.0, "complexity": 0.3}

    def forward(self, input_ids, attention_mask, intent_labels=None,
                route_labels=None, complexity_labels=None):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]  # [CLS] token representation

        intent_logits = self.intent_head(pooled)
        route_logits = self.route_head(pooled)
        complexity_pred = self.complexity_head(pooled).squeeze(-1)

        loss = None
        if route_labels is not None:
            intent_loss = self.intent_loss_fn(intent_logits, intent_labels)
            route_loss = self.route_loss_fn(route_logits, route_labels)
            complexity_loss = self.complexity_loss_fn(complexity_pred, complexity_labels)
            loss = (
                self.loss_weights["intent"] * intent_loss
                + self.loss_weights["route"] * route_loss
                + self.loss_weights["complexity"] * complexity_loss
            )

        return {
            "loss": loss,
            "intent_logits": intent_logits,
            "route_logits": route_logits,
            "complexity_pred": complexity_pred,
        }


# ─────────────────────────────────────────────────────────────────────────
# 3. Metrics
# ─────────────────────────────────────────────────────────────────────────

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    intent_logits, route_logits, complexity_pred = predictions
    intent_labels, route_labels, complexity_labels = labels

    route_preds = np.argmax(route_logits, axis=1)
    intent_preds = np.argmax(intent_logits, axis=1)

    return {
        "route_accuracy": accuracy_score(route_labels, route_preds),
        "route_f1": f1_score(route_labels, route_preds, average="binary"),
        "intent_accuracy": accuracy_score(intent_labels, intent_preds),
        "complexity_mae": mean_absolute_error(complexity_labels, complexity_pred),
    }


# ─────────────────────────────────────────────────────────────────────────
# 4. Main training routine
# ─────────────────────────────────────────────────────────────────────────

def main(filepath: str, output_dir: str = "./router_model", epochs: int = 3, batch_size: int = 32):
    print("Loading data...")
    df = load_data(filepath)
    print(f"Loaded {len(df)} rows")

    intent_encoder = LabelEncoder()
    route_encoder = LabelEncoder()   # will map CLOUD/LOCAL -> 0/1 alphabetically (CLOUD=0, LOCAL=1)

    df["intent_id"] = intent_encoder.fit_transform(df["intent"])
    df["route_id"] = route_encoder.fit_transform(df["route"])

    print(f"Intents: {len(intent_encoder.classes_)}")
    print(f"Route mapping: {dict(zip(route_encoder.classes_, range(len(route_encoder.classes_))))}")

    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    train_df, val_df = train_test_split(
        df, test_size=0.1, random_state=42, stratify=df["route_id"]
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    train_dataset = RouterDataset(
        train_df["query"].tolist(), train_df["intent_id"].tolist(),
        train_df["route_id"].tolist(), train_df["complexity_score"].tolist(), tokenizer
    )
    val_dataset = RouterDataset(
        val_df["query"].tolist(), val_df["intent_id"].tolist(),
        val_df["route_id"].tolist(), val_df["complexity_score"].tolist(), tokenizer
    )

    config = MultiTaskRouterConfig(base_model_name=MODEL_NAME, num_intents=len(intent_encoder.classes_))
    model = MultiTaskRouter(config)

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=100,
        learning_rate=2e-5,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="route_f1",
        fp16=torch.cuda.is_available(),   # mixed precision on GPU, skip on CPU
        report_to="none",
        # CRITICAL: by default, Trainer only recognizes a field literally
        # named "labels" when gathering label arrays for compute_metrics.
        # Since this model uses three custom-named label fields instead,
        # they must be listed explicitly here, IN THE SAME ORDER unpacked
        # in compute_metrics() below — otherwise eval silently breaks
        # (label_ids ends up empty/misaligned).
        label_names=["intent_labels", "route_labels", "complexity_labels"],
    )

    def collate_fn(batch):
        keys = batch[0].keys()
        return {k: torch.stack([item[k] for item in batch]) for k in keys}

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=collate_fn,
        compute_metrics=compute_metrics,
    )

    print("\nTraining...")
    trainer.train()

    print("\nFinal evaluation:")
    metrics = trainer.evaluate()
    print(metrics)

    # Save model, tokenizer, and label encoders together — you need all
    # three to run inference later.
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    import joblib
    joblib.dump(intent_encoder, f"{output_dir}/intent_encoder.joblib")
    joblib.dump(route_encoder, f"{output_dir}/route_encoder.joblib")
    print(f"\nSaved model + tokenizer + label encoders to {output_dir}")


if __name__ == "__main__":
    import sys
    filepath = sys.argv[1] if len(sys.argv) > 1 else "unified_route_dataset.json"
    main(filepath)
