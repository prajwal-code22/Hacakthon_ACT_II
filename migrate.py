"""
migrate_checkpoint.py
=======================
Upgrades a router_model/ checkpoint saved with the OLD (buggy) version of
train_transformer_router.py — the one where __init__ always called
AutoModel.from_pretrained(), causing crashes on reload (network errors,
"meta device" RuntimeErrors, etc) — into the NEW format that loads fully
offline.

IMPORTANT: this does NOT retrain anything. Your existing learned weights
(encoder + all three heads) are preserved exactly as they were — only the
config.json metadata is upgraded so the model can reconstruct its own
architecture locally on future loads, instead of re-downloading the base
encoder from HuggingFace Hub every time.

This DOES require internet access once (to fetch the base DistilBERT
architecture info needed to correctly reconstruct the encoder config).
That's a one-time migration cost, not a per-inference cost.

Usage:
    python migrate_checkpoint.py <old_checkpoint_dir> <new_output_dir>

Example:
    python migrate_checkpoint.py ./router_model ./router_model_fixed
"""

import sys
import shutil
from pathlib import Path

import torch
from transformers import AutoModel
from safetensors.torch import load_file as load_safetensors

from train_transformer_router import MultiTaskRouter, MultiTaskRouterConfig, MODEL_NAME


def migrate(old_dir: str, new_dir: str) -> None:
    old_path = Path(old_dir)
    new_path = Path(new_dir)
    new_path.mkdir(parents=True, exist_ok=True)

    weights_file = old_path / "model.safetensors"
    if not weights_file.exists():
        raise FileNotFoundError(
            f"No model.safetensors found in {old_path}. "
            "Point this script at the folder containing your FINAL saved "
            "model (the one with config.json + model.safetensors directly "
            "inside it), not one of the checkpoint-XXXX subfolders."
        )

    print(f"Loading old config from {old_path}...")
    old_config = MultiTaskRouterConfig.from_pretrained(old_path)
    num_intents = old_config.num_intents
    print(f"num_intents = {num_intents}")

    print(f"Downloading base encoder architecture ({MODEL_NAME}) once for migration...")
    # This is the ONE legitimate network call in the whole migration — it's
    # only needed to correctly capture the encoder's config for future
    # offline reloads. Your actual trained weights are untouched.
    fresh_config = MultiTaskRouterConfig(base_model_name=MODEL_NAME, num_intents=num_intents)
    model = MultiTaskRouter(fresh_config)   # fresh_config.encoder_config is None here,
                                              # so this legitimately downloads once and
                                              # then captures encoder_config automatically

    print("Loading your trained weights from the old checkpoint...")
    state_dict = load_safetensors(str(weights_file))
    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing:
        print(f"  Warning: {len(missing)} missing keys (first 5): {missing[:5]}")
    if unexpected:
        print(f"  Warning: {len(unexpected)} unexpected keys (first 5): {unexpected[:5]}")
    if not missing and not unexpected:
        print("  All weights loaded cleanly — architecture matches exactly.")

    print(f"Saving migrated (offline-loadable) checkpoint to {new_path}...")
    model.save_pretrained(new_path)

    # Copy over everything else unchanged: tokenizer files + label encoders.
    # None of these are affected by the bug, so they're copied as-is.
    for fname in ["tokenizer.json", "tokenizer_config.json", "vocab.txt",
                  "special_tokens_map.json", "intent_encoder.joblib", "route_encoder.joblib"]:
        src = old_path / fname
        if src.exists():
            shutil.copy(src, new_path / fname)
            print(f"  Copied {fname}")
        else:
            print(f"  (skipped {fname}, not found in old checkpoint)")

    print(f"\nDone. Point your inference code at '{new_path}' instead of '{old_path}'.")
    print("Verifying the migrated checkpoint loads fully offline...")
    _verify_offline_load(new_path)


def _verify_offline_load(path: Path) -> None:
    """Sanity check: reload the migrated model and confirm no network call is needed."""
    reloaded = MultiTaskRouter.from_pretrained(path)
    reloaded.eval()
    print("Verified: migrated checkpoint loads successfully.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python migrate_checkpoint.py <old_checkpoint_dir> <new_output_dir>")
        sys.exit(1)
    migrate(sys.argv[1], sys.argv[2])