import logging
import re
from pathlib import Path

from llama_cpp import Llama, LlamaRAMCache

logger = logging.getLogger("whisperai")

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
        n_threads: int | None = None,
        use_gpu: bool = True,
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
        self.use_gpu = use_gpu
        self.n_ctx = n_ctx

        import os
        total_cores = os.cpu_count() or 4
        self.n_threads = n_threads or max(2, min(total_cores - 2, 4))
        self.llm = None

        self._load_model()

    def _load_model(self):
        if self.use_gpu:
            try:
                logger.info("Initializing LLMEngine on GPU (n_gpu_layers=-1)...")
                self.llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_threads=self.n_threads,
                    n_gpu_layers=-1,
                    repeat_last_n=256,
                    verbose=False,
                )
            except Exception as e:
                logger.warning(f"GPU initialization for LLM failed ({e}). Falling back to CPU.")

        if self.llm is None:
            logger.info("Initializing LLMEngine on CPU (n_gpu_layers=0)...")
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=0,
                repeat_last_n=256,
                verbose=False,
            )

        # Implement context caching for the LLM, strictly bound to 256MB
        try:
            self.llm.set_cache(LlamaRAMCache(capacity_bytes=256 << 20))
        except Exception:
            pass

    def hibernate(self):
        """Unload LLM model from RAM during idle periods."""
        if hasattr(self, 'llm') and self.llm is not None:
            logger.info("[LLMEngine] Hibernating: Unloading LLM model from RAM.")
            del self.llm
            self.llm = None
            import gc
            gc.collect()

    def wake_up(self):
        """Reload LLM model into RAM."""
        if getattr(self, 'llm', None) is None:
            logger.info("[LLMEngine] Waking up: Reloading LLM model.")
            self._load_model()

    def clean_text(
        self, text: str, context: str = "", profile_id: str = "general"
    ) -> str:
        """
        Clean the provided transcript using the LLM.
        Removes filler words, fixes grammar, and formats for the target context.
        """
        from src.llm.formatter import Formatter
        from src.llm.prompts import PromptBuilder
        from src.llm.style_profiles import get_style_prompt
        from src.utils.list_detector import detect_list_mode
        from src.utils.text_cleaner import sanitize_symbol_loops

        if not text or len(text.strip()) < 3:
            return sanitize_symbol_loops(text)

        try:
            Formatter().check_repetition(text)
        except ValueError:
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
            f"Context: {context}\n"
            f"Raw transcription: {text}\n\n"
            f"Instructions:\n"
            f"1. Fix minor grammar and remove filler words (um, uh).\n"
            f"2. PRESERVE all markdown formatting (e.g., **, #, `) exactly as written.\n"
            f"3. DO NOT rewrite the sentence or change the meaning.\n"
            f"4. DO NOT add commentary.\n"
            f"Output ONLY the corrected text:"
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
                    "\n---",
                    "\n===",
                    "\n***",
                    "\nAI:",
                    "\nAssistant:",
                ],
                echo=False,
                temperature=0.1,
                repeat_penalty=1.1,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )
            end_t = time.time()

            tokens = response.get("usage", {}).get("completion_tokens", 1)
            speed = tokens / max(end_t - start_t, 0.001)
            telemetry.log_token_generation_speed(speed)

            result = response["choices"][0]["text"].strip()

            # Strip ALL occurrences of prompt-echo and AI header patterns
            result = re.sub(r"(?i)^\s*(AI|Assistant)\b\s*[:\-=]*\s*", "", result)
            result = re.sub(r"(?i)^\s*(Output|Cleaned\s*Text)\s*[:\-=]+\s*", "", result)
            result = re.sub(r"(?i)(cleaned\s*text\s*:|output\s*:)", "", result).strip()

            # Reject meta-commentary or refusal hallucinations
            meta_triggers = [
                "you have not provided",
                "please provide",
                "as an ai",
                "false start",
                "no text to clean",
                "i cannot",
                "here is the cleaned",
                "i've cleaned",
            ]
            if any(trig in result.lower() for trig in meta_triggers):
                logger.warning(f"[LLM] Discarded meta-commentary hallucination (length={len(result)})")
                return sanitize_symbol_loops(text)

            # Word-count guard: Prevents the LLM from rewriting or truncating
            orig_words = len(text.split())
            new_words = len(result.split())

            if new_words > orig_words + 15 and orig_words > 3:
                logger.warning(f"[LLM] Discarded output: added too many words ({new_words} > {orig_words}+15)")
                return sanitize_symbol_loops(text)

            if new_words < orig_words * 0.6 and orig_words > 5:
                logger.warning(f"[LLM] Discarded output: truncated too many words ({new_words} < {orig_words}*0.6)")
                return sanitize_symbol_loops(text)

            if len(result) > max(len(text) * 2.5, 50) and len(text) > 10:
                logger.warning(f"[LLM] Discarded output much longer than input (len={len(result)} vs input_len={len(text)})")
                return sanitize_symbol_loops(text)

            # Reject raw LLM hallucination loops (5+ repeating letters or 12+ repeating zeros)
            if re.search(r"([a-zA-Z])\1{4,}|0{12,}", result):
                logger.warning(f"[LLM] Discarded LLM output due to character repetition loop (length={len(result)})")
                return sanitize_symbol_loops(text)

            # Apply universal symbol loop sanitizer
            result = sanitize_symbol_loops(result)
            # Strip leading/trailing quotes
            result = result.strip("'\"").strip()

            # Discard if output contains no alphanumeric characters (e.g. symbol-only junk)
            if result and not re.search(r"[a-zA-Z0-9]", result):
                result = ""

            # Post-LLM safety net: enforce newlines and context break based on detected mode
            result = _ensure_list_newlines(result, list_mode)

            # If the LLM returned nothing meaningful, return cleaned fallback text
            if not result or len(result.strip()) < 2:
                return sanitize_symbol_loops(text)

            return result
        except Exception:
            return sanitize_symbol_loops(text)
        finally:
            if self.llm and hasattr(self.llm, "reset"):
                try:
                    self.llm.reset()
                except Exception:
                    pass
            import gc
            gc.collect()

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
        from src.utils.text_cleaner import sanitize_symbol_loops

        # Enforce maximum text and context length truncation guards to prevent prompt KV cache overflow
        if text and len(text) > 4000:
            text = text[:4000]
        if context and len(context) > 500:
            context = context[:500]

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
            raw_res = response["choices"][0]["text"].strip()
            from src.llm.formatter import Formatter

            Formatter().check_repetition(raw_res)
            return sanitize_symbol_loops(raw_res)
        except Exception:
            return sanitize_symbol_loops(text)
        finally:
            if self.llm and hasattr(self.llm, "reset"):
                try:
                    self.llm.reset()
                except Exception:
                    pass
            import gc
            gc.collect()
