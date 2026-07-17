import re
from pathlib import Path
from llama_cpp import Llama, LlamaRAMCache

# Resolve model directory relative to ~/.whisperai so it works both
# from source and from a PyInstaller frozen bundle.
_MODELS_DIR = Path.home() / ".whisperai" / "models" / "llm"
_MODEL_FILENAME = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
_HF_REPO = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
_HF_FILE = "qwen2.5-1.5b-instruct-q4_k_m.gguf"


def _ensure_model(model_dir: Path, filename: str) -> Path:
    """Download the GGUF model from HuggingFace Hub if not already present."""
    model_path = model_dir / filename
    if model_path.exists():
        return model_path

    model_dir.mkdir(parents=True, exist_ok=True)
    pass
    pass

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


def _ensure_list_newlines(text: str, list_mode: str) -> str:
    """
    Post-LLM safety net: ensure numbered list items appear on their own lines.
    Gated behind list_mode to prevent corruption of decimals or prose.

    list_mode values:
    - 'none':  Return text unchanged.
    - 'pure':  Enforce newlines AND prepend \\n\\n to break from any prior paragraph.
    - 'mixed': Enforce newlines between items, but do NOT prepend \\n\\n because
               the prose paragraph comes first in the same paste.
    """
    if list_mode == "none":
        return text

    # Force a newline before any "N. " pattern not already at the start of a line.
    formatted_text = re.sub(r"(?<=[^\n\s])\s+(\d+\.\s)", r"\n\1", text)

    if list_mode == "pure":
        # Strictly prepend \n\n so the list always starts fresh after previous text.
        return "\n\n" + formatted_text.strip()
    else:  # mixed
        # Prose comes first — just clean up and return without a leading gap.
        return formatted_text.strip()


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
        pass
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=-1,
            verbose=False,
        )
        # Implement context caching for the LLM, strictly bound to 256MB
        self.llm.set_cache(LlamaRAMCache(capacity_bytes=256 << 20))

    def clean_text(
        self, text: str, context: str = "", profile_id: str = "general"
    ) -> str:
        """
        Clean the provided transcript using the LLM.
        Removes filler words, fixes grammar, and formats for the target context.
        """
        from src.llm.prompts import PromptBuilder
        from src.llm.style_profiles import get_style_prompt
        from src.llm.formatter import Formatter
        from src.utils.list_detector import detect_list_mode

        try:
            Formatter().check_repetition(text)
        except ValueError:
            pass
            return ""

        list_mode = detect_list_mode(text)

        # MIXED MODE: The 1.5B model cannot reliably keep prose+list in one pass.
        # Split the raw text at the list boundary, process each part separately,
        # then join. This guarantees the paragraph is preserved as prose.
        if list_mode == "mixed":
            return self._clean_text_mixed(text, context, profile_id)

        style_addon = get_style_prompt(profile_id)

        builder = PromptBuilder()
        if style_addon:
            builder.with_style(style_addon)
        if profile_id == "technical":
            builder.with_code_mode()
        if list_mode == "pure":
            builder.with_list_hint()

        system_prompt = builder.build()

        user_prompt = (
            f"Context: {context}\n" f"Raw transcription: {text}\n\n" f"Output:"
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
                stop=[
                    "<|im_end|>",
                    "Cleaned text:",
                    "cleaned text:",
                    "Output:",
                    "output:",
                    "CLEANED TEXT:",
                ],
                echo=False,
                temperature=0.1,
            )
            end_t = time.time()

            tokens = response.get("usage", {}).get("completion_tokens", 1)
            speed = tokens / max(end_t - start_t, 0.001)
            telemetry.log_token_generation_speed(speed)

            result = response["choices"][0]["text"].strip()

            # Strip ALL occurrences of prompt-echo patterns
            result = re.sub(r"(?i)(cleaned\s*text\s*:|output\s*:)", "", result).strip()
            # Strip any leading/trailing quotes the LLM might add
            result = result.strip("'\"")
            # Post-LLM safety net: enforce newlines and context break based on detected mode
            result = _ensure_list_newlines(result, list_mode)

            # If the LLM returned nothing meaningful, return the original text
            if not result or len(result.strip()) < 2:
                return text

            return result
        except Exception:
            pass
            return text

    def _clean_text_mixed(self, text: str, context: str, profile_id: str) -> str:
        """
        Split-pass handler for 'mixed' mode (prose paragraph followed by a list).

        A 1.5B model given both prose and list in a single pass will reliably
        collapse the prose into a list item. To guarantee correct output, we:
          1. Split the raw transcription at the first list trigger boundary.
          2. Process the prose part with no list hint (standard clean).
          3. Process the list part with full LIST MODE (aggressive list hint).
          4. Join: clean_prose + newline + clean_list (with \n\n prefix from enforcer).
        """
        from src.utils.list_detector import get_list_boundary

        prose_raw, list_raw = get_list_boundary(text)

        # Pass 1: clean the prose part (no list mode)
        prose_result = self.clean_text(
            prose_raw, context=context, profile_id=profile_id
        )

        # Pass 2: clean the list part (will trigger 'pure' list mode)
        list_result = self.clean_text(list_raw, context=context, profile_id=profile_id)

        # Join: prose stays as-is, list gets its \n\n prefix from _ensure_list_newlines
        # Result: "Clean prose sentence.\n\n1. Item one\n2. Item two"
        return prose_result + list_result

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
        except Exception:
            pass
            return text
