"""
gemma.py

Loads a local Gemma model and provides a simple generate() interface.
"""

from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


class GemmaModel:

    def __init__(self):

        # Change this to your Gemma model folder
        model_dir = Path(__file__).resolve().parent / "gemma_model"

        print("Loading Gemma model...")

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_dir,
            trust_remote_code=True,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            torch_dtype=torch.float32,
            trust_remote_code=True,
        )

        self.model.to(self.device)
        self.model.eval()

        print(f"Gemma loaded on {self.device}")

    @torch.no_grad()
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.95,
    ):

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt"
        ).to(self.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            pad_token_id=self.tokenizer.eos_token_id,
        )

        text = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True,
        )

        return text


gemma_model = GemmaModel()


def initialize_model():
    return gemma_model