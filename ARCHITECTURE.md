# WhisperAI: Technical Architecture & Systems Whitepaper

## 1. Executive Summary & Quantization Justification

WhisperAI is a 100% local, hardware-accelerated voice dictation engine for Windows. The overarching engineering philosophy prioritizes deterministic execution, rigid memory boundaries, and zero-trust privacy over probabilistic generation. 

**Model Selection & Quantization Trade-offs**
The architecture centers on two foundational models: `faster-whisper` for Automatic Speech Recognition (ASR) and a localized Large Language Model for intent extraction. For the LLM, we explicitly selected the **Qwen 2.5 1.5B** parameter model utilizing `Q4_K_M` quantization (4-bit integer, medium block quantization). 

This selection is the mathematical optimum for desktop edge inference. Larger models (7B+) offer superior zero-shot reasoning but incur a VRAM footprint and token generation latency that block the main thread and break the illusion of real-time dictation. `Q4_K_M` quantization achieves a massive ~70% reduction in memory footprint compared to FP16 weights with only a marginal (< 2%) degradation in contextual accuracy. This guarantees the model fits entirely in shared RAM or limited VRAM while delivering >40 tokens/second on consumer hardware.

---

## 2. Advanced Engineering Paradigms

### A. Compute Scheduling & OS Integration
Modern Windows environments utilize Big.LITTLE CPU topologies (e.g., Intel's 12th Gen+ hybrid architecture), combining Performance Cores (P-Cores) and Efficiency Cores (E-Cores). A common failure mode for local ML applications is the Windows OS scheduler mistakenly shifting long-running inference threads to E-Cores, resulting in massive latency spikes.

*   **P-Core Thread Pinning:** WhisperAI bypasses the OS scheduler. Upon startup, the `WhisperAIApp` coordinator uses a hardware heuristic via `psutil` to dynamically calculate the physical vs. logical core count. It isolates the hyper-threaded P-Cores and explicitly applies a CPU affinity mask (`win32process` / `psutil.Process().cpu_affinity()`). Heavy ASR and LLM workloads are forced exclusively onto Performance Cores.
*   **Asynchronous UI Offloading:** The PySide6 UI runs exclusively in the main thread at a locked 60 FPS. All inference processing is strictly offloaded to background `QThread` instances.

### B. Memory Circuit Breakers & Resource Governance
Unbounded memory consumption is a catastrophic failure mode in continuous local AI execution. WhisperAI treats memory as a physical constraint with hard circuit breakers.

*   **Ingestion Buffers:** Raw audio chunking and real-time transcription queues utilize strict length-bounded circular buffers (`collections.deque(maxlen=30000)`). This prevents silent memory leaks during dictation sessions lasting several hours.
*   **KV Cache Isolation:** The `llama-cpp-python` engine is bound by a strict context window and a fixed memory allocation. We enforce `LlamaRAMCache(capacity_bytes=256 << 20)`, establishing a hard 256MB ceiling on the KV cache. This guarantees the total application footprint remains comfortably under 1.5GB, preventing disk-swapping and Out-Of-Memory (OOM) crashes on constrained systems.

### C. Deterministic Hybrid Routing (The Split-Pass Strategy)
Small 1.5B parameter LLMs are lightning-fast but suffer from context collapse when tasked with complex structural logic—such as mixing conversational prose with numbered lists. Relying purely on prompting results in hallucinations (e.g., generating conversational preambles inside dictation text).

*   **The Split-Pass Pipeline:** Instead of brute-forcing the prompt, WhisperAI employs a deterministic routing strategy. When the ingestion engine detects "mixed mode" dictation, it physically splits the user's prose from the requested list. Inference is run separately, preventing the model from collapsing the two concepts.
*   **Regex Constraint Layer:** Probabilistic text generation is immediately piped through a deterministic post-processing layer. Hard regular expressions (`re.sub`) enforce line breaks, strip hallucinated conversational filler, and guarantee structural precision before the text is injected into the active window.

---

## 3. Zero-Trust Data Sovereignty & Cryptographic Integrity

For an edge dictation tool, privacy is the primary value proposition over cloud APIs. WhisperAI operates in an entirely air-gapped paradigm.

*   **Data Sovereignty:** Absolutely zero raw audio, transcription buffers, or contextual metadata ever leaves the local machine. Telemetry and logging write exclusively to `%USERPROFILE%\.whisperai\logs\`.
*   **Cryptographic Model Checksumming:** To prevent model poisoning (e.g., loading compromised GGUF weights), the deployment pipeline enforces SHA-256 cryptographic hashing. WhisperAI dynamically verifies the checksums of its ASR and LLM weights against a known-good ledger before initializing inference.

---

## 4. MLOps & Performance Regression Profiling

Continuous Integration (CI) for edge AI requires more than standard unit testing; it requires physical profiling. 

*   **Deterministic ML CI Profiling:** The GitHub Actions pipeline (`pr-validation.yml`) executes a headless dictation mock on every PR. 
*   **Performance Bounds:** The CI physically tracks the inference lifecycle. If the RAM footprint breaches the 1.5GB ceiling, or if the token-generation latency drops below the established baseline, the PR fails automatically. This ensures that any codebase change maintains the strict performance guarantees required for real-time edge execution.
