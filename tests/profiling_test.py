import os
import gc
import psutil
import time
import numpy as np
from unittest.mock import MagicMock
from pathlib import Path

from src.core.pipeline import AIPipeline
from src.asr.engine import ASREngine
from src.llm.engine import LLMEngine
from src.utils.list_detector import detect_list_mode


def get_process_memory_mb():
    process = psutil.Process(os.getpid())
    try:
        # Use USS if available (Unique Set Size, ignores shared mmap)
        return process.memory_full_info().uss / (1024 * 1024)
    except AttributeError:
        # Fallback to private or rss
        return process.memory_info().rss / (1024 * 1024)


def test_profiling_and_split_pass():
    # Record baseline memory
    gc.collect()
    baseline_mem = get_process_memory_mb()

    # 1. Setup mocked ASR to return text that triggers "mixed" list mode
    # This specifically forces the split-pass regex routing in LLMEngine
    mock_asr = MagicMock(spec=ASREngine)
    adversarial_transcript = (
        "This is a substantially long prose prefix that we need to ensure "
        "is recognized as a prose paragraph before the list starts. "
        "number one we need to buy apples number two bananas."
    )
    mock_asr.transcribe.return_value = adversarial_transcript

    # Ensure detect_list_mode correctly flags this as 'mixed'
    assert detect_list_mode(adversarial_transcript) == "mixed"

    from unittest.mock import patch

    with patch("src.llm.engine.LlamaRAMCache") as mock_cache_cls:
        from llama_cpp import LlamaRAMCache

        mock_cache_cls.return_value = LlamaRAMCache(capacity_bytes=16 << 20)
        # 2. Instantiate real LLMEngine with smaller n_ctx to stay under 1.5GB
        llm = LLMEngine(n_ctx=512)

    # Measure memory after loading LLM
    gc.collect()
    post_load_mem = get_process_memory_mb()

    pipeline = AIPipeline(asr_engine=mock_asr, llm_engine=llm)

    # Load the adversarial audio file
    audio_path = Path(__file__).parent / "data" / "sample_dictation.wav"
    assert audio_path.exists(), f"Audio file not found: {audio_path}"

    import wave

    with wave.open(str(audio_path), "rb") as w:
        frames = w.readframes(w.getnframes())
        if w.getsampwidth() == 2:
            audio_data = (
                np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            )
        elif w.getsampwidth() == 4:
            audio_data = np.frombuffer(frames, dtype=np.float32)
        else:
            audio_data = np.zeros(16000, dtype=np.float32)

    # 3. Process through pipeline
    start_time = time.time()

    # Track LLM tokens generated
    # We patch telemetry to count tokens_per_second
    token_speeds = []

    from src.core.telemetry import telemetry

    original_log_speed = telemetry.log_token_generation_speed

    def patch_log_speed(speed):
        token_speeds.append(speed)
        original_log_speed(speed)

    telemetry.log_token_generation_speed = patch_log_speed

    result = pipeline.process_audio(audio_data, context="General dictation")

    end_time = time.time()
    latency = end_time - start_time

    # 4. Check memory
    gc.collect()
    peak_mem = get_process_memory_mb()

    # 5. Assertions
    assert (
        peak_mem - baseline_mem < 1536
    ), f"Memory footprint exceeded 1.5GB: {peak_mem - baseline_mem:.2f} MB (Peak: {peak_mem:.2f} MB, Baseline: {baseline_mem:.2f} MB)"

    if __name__ == "__main__":
        test_profiling_and_split_pass()

    # The list mode should have triggered split pass, meaning the LLM was called at least twice
    assert (
        len(token_speeds) >= 2
    ), "Split-pass was not triggered (expected at least 2 LLM calls for mixed mode)"

    # Tokens per second > 1.5
    avg_tps = sum(token_speeds) / len(token_speeds)
    assert avg_tps > 1.5, f"Token generation too slow: {avg_tps:.2f} t/s"

    # The resulting text should have prose and a list
    # 'mixed' mode preserves the prose, and starts the list with \n\n
    assert "apples" in result.lower()

    print("--- Profiling Results ---")
    print(f"Baseline Memory: {baseline_mem:.2f} MB")
    print(f"Model Load Memory: {post_load_mem:.2f} MB")
    print(f"Peak Memory: {peak_mem:.2f} MB")
    print(f"Avg Tokens/Sec: {avg_tps:.2f}")
    print(f"Total Latency: {latency:.2f} sec")
    print(f"Pipeline Output: {result}")
