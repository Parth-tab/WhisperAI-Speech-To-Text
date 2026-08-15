# 100% Local-Only ASR and LLM Pipeline

To guarantee user privacy, zero network latency dependency, and offline reliability, WhisperAI runs all speech recognition and intent formatting locally on the user's machine using `faster-whisper` and `llama-cpp-python` (Qwen2.5-1.5B GGUF) instead of third-party cloud APIs.
