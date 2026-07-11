import sys
import os
from pathlib import Path
from llama_cpp import Llama

# Resolve model directory relative to ~/.whisperai so it works both
# from source and from a PyInstaller frozen bundle.
_MODELS_DIR = Path.home() / ".whisperai" / "models" / "llm"
_MODEL_FILENAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
_HF_REPO = "Qwen/Qwen2.5-3B-Instruct-GGUF"
_HF_FILE = "qwen2.5-3b-instruct-q4_k_m.gguf"


def _ensure_model(model_dir: Path, filename: str) -> Path:
    """Download the GGUF model from HuggingFace Hub if not already present."""
    model_path = model_dir / filename
    if model_path.exists():
        return model_path

    model_dir.mkdir(parents=True, exist_ok=True)
    print(f"[LLMEngine] Model not found. Downloading {filename} from HuggingFace...")
    print(f"[LLMEngine] This is a one-time download (~1.9 GB). Please wait...")

    try:
        from huggingface_hub import hf_hub_download
        downloaded = hf_hub_download(
            repo_id=_HF_REPO,
            filename=_HF_FILE,
            local_dir=str(model_dir),
        )
        return Path(downloaded)
    except Exception as e:
        raise RuntimeError(
            f"Failed to download LLM model. "
            f"Please manually place '{filename}' in '{model_dir}'.\n"
            f"Download from: https://huggingface.co/{_HF_REPO}\n"
            f"Error: {e}"
        )


class LLMEngine:
    def __init__(
        self,
        model_path: str | None = None,
        n_ctx: int = 2048,
        n_threads: int = 4,
    ):
        if model_path is None:
            resolved = _ensure_model(_MODELS_DIR, _MODEL_FILENAME)
        else:
            resolved = Path(model_path)
            if not resolved.is_absolute():
                resolved = _MODELS_DIR / resolved.name

        if not resolved.exists():
            resolved = _ensure_model(_MODELS_DIR, _MODEL_FILENAME)

        self.model_path = str(resolved)
        print(f"[LLMEngine] Loading model from: {self.model_path}")
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            verbose=False,
        )

    def clean_text(self, text: str, context: str = "") -> str:
        """
        Clean the provided transcript using the LLM.
        Removes filler words, fixes grammar, and formats for the target context.
        """
        system_prompt = (
            "You are a professional transcription editor. "
            "Your job is to clean up raw voice dictation by:\n"
            "1. Removing filler words and sounds (um, uh, ah, er, like, you know, I mean, etc.)\n"
            "2. Fixing grammar and punctuation\n"
            "3. Removing false starts and repetitions\n"
            "4. Preserving the speaker's original intent and meaning\n"
            "5. Adapting tone to the context provided\n"
            "Return ONLY the cleaned text, with no explanations or meta-commentary."
        )

        user_prompt = (
            f"Context: {context}\n"
            f"Raw transcription: {text}\n\n"
            f"Cleaned text:"
        )

        prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

        response = self.llm(
            prompt,
            max_tokens=512,
            stop=["<|im_end|>"],
            echo=False,
            temperature=0.1,
        )
        return response["choices"][0]["text"].strip()
