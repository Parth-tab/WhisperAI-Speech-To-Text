import sys
import os
from pathlib import Path
from llama_cpp import Llama, LlamaRAMCache

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
            n_gpu_layers=-1,
            verbose=False,
        )
        # Implement context caching for the LLM
        self.llm.set_cache(LlamaRAMCache(capacity_bytes=2 << 30))

    def clean_text(self, text: str, context: str = "") -> str:
        """
        Clean the provided transcript using the LLM.
        Removes filler words, fixes grammar, and formats for the target context.
        """
        from src.llm.prompts import FORMATTING_SYSTEM_PROMPT
        from src.llm.formatter import Formatter
        
        try:
            Formatter().check_repetition(text)
        except ValueError as e:
            print(e)
            return text
            
        system_prompt = FORMATTING_SYSTEM_PROMPT

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

        import time
        from src.core.telemetry import telemetry

        start_t = time.time()
        try:
            response = self.llm(
                prompt,
                max_tokens=512,
                stop=["<|im_end|>"],
                echo=False,
                temperature=0.1,
            )
            end_t = time.time()
            
            tokens = response.get("usage", {}).get("completion_tokens", 1)
            speed = tokens / max(end_t - start_t, 0.001)
            telemetry.log_token_generation_speed(speed)
            
            return response["choices"][0]["text"].strip()
        except Exception as e:
            print(f"[LLMEngine] Error during clean_text: {e}")
            return text

    def execute_command(self, command: str, text: str, context: str = "") -> str:
        system_prompt = (
            "You are an AI assistant editing text for a user. "
            "You will be given the currently selected text and a command to execute on it. "
            "Return ONLY the modified text, with no explanations or meta-commentary."
        )
        user_prompt = (
            f"Context: {context}\n"
            f"Original Text: {text}\n"
            f"Command: {command}\n\n"
            f"Modified text:"
        )
        prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        try:
            response = self.llm(
                prompt,
                max_tokens=1024,
                stop=["<|im_end|>"],
                echo=False,
                temperature=0.1,
            )
            return response["choices"][0]["text"].strip()
        except Exception as e:
            print(f"[LLMEngine] Error during execute_command: {e}")
            return text
