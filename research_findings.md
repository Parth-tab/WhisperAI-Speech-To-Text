# Research Findings: Best Architectural Practices for Local Windows App

This document outlines the best architectural practices extracted from the latest ArXiv research papers (within the last 12 months) covering Low-latency streaming ASR, Speculative Decoding for local LLMs, and Real-time disfluency removal and semantic text formatting.

## 1. Low-Latency Streaming Automatic Speech Recognition (ASR)
To achieve state-of-the-art streaming ASR on local constraints (e.g., CPU or limited GPU on Windows), the following techniques are recommended:

*   **Int4 k-quant & Operator Fusion (Nemotron Speech Streaming)**: Optimize transducer or encoder-decoder architectures with importance-weighted k-quant (Int4) and graph-level operator fusion. This can reduce memory footprint by ~4x and achieve sub-second algorithmic latency on CPUs with negligible Word Error Rate (WER) degradation.
*   **Chunkwise Aligners**: Instead of standard Transducers which are costly, use Chunkwise Aligners. Divide audio into chunks and align each label to the leftmost frames of its chunk, handling transitions via a learned end-of-chunk probability. This offers superior decoding efficiency for local environments.
*   **Incremental Commitment for Contextual Biasing**: Implement CTC-based Word Spotting across audio chunks using stateful token passing. Use an "incremental commitment mechanism" to emit segments guaranteed not to be affected by future audio, while deferring uncertain regions. This improves domain-specific word recognition without adding latency.
*   **Weighted Lookahead for Punctuation**: For real-time punctuation, use a non-autoregressive scoring method with a bounded K-subword-token lookahead. This avoids free-form generation latency and alignment failures.

## 2. Speculative Decoding for Local LLMs
For accelerating local LLM inference via Speculative Decoding, the following architectural choices should be adopted:

*   **Conditional Tree-Structured Drafting (DominoTree / Weaver)**: Instead of using independent factorized marginals for drafting, use lightweight autoregressive adapters or GRU-based causal corrections that restore path-dependent conditional dependencies between proposed tokens. Generate draft trees rather than single sequences to drastically increase acceptance rates.
*   **GPU-Native CUDA-Graph Builders**: To keep per-round tree construction overhead extremely low, implement the tree builder using optimized GPU-native CUDA-graphs (e.g., SGLang kernels).
*   **Decoupled Long-Short Contexts (DeLS-Spec)**: Use a decoupled architecture where a block-parallel drafter serves as a long-context expert, while a lightweight local head acts as a short-context expert. This local head can be trained cheaply via next-token prediction independently of the backbone, adding flexibility and high acceptance rates.
*   **Lossless vs. Relaxed Speculation**: Be cautious of "relaxed" speculative decoding in local apps. Relaxed approaches often require the drafter to be a high-quality language model in itself, which is counterproductive for a local environment requiring highly lightweight dedicated drafters.

## 3. Real-Time Disfluency Removal & Semantic Text Formatting
Handling disfluencies (stutters, hesitations, repetitions) correctly is crucial for natural, readable transcripts without information loss or hallucination:

*   **Explicit Disfluency Tokens**: Rather than training the ASR to blindly erase disfluencies—which often leads to hallucinations and catastrophic forgetting—introduce explicit disfluency tokens into the ASR model. This allows the model to faithfully transcribe the audio and selectively omit the tokens downstream when "intended" (canonical) text is desired.
*   **Preference-Aware Normalization**: Build a flexible, preference-aware pipeline (like PreferenceASR) where formatting instructions (e.g., casing, entity normalization, and disfluency removal) dictate the behavior of a selective normalizer. This allows users to dynamically switch between "verbatim" and "intended" transcription styles.
*   **Time-to-Next-Speech-Onset for Endpoint Detection (EPD)**: Real-time turn-taking is frequently disrupted by disfluencies and mid-utterance pauses. Use a duration-aware streaming EPD mechanism (like Next-Turn) that predicts the time-to-next-speech-onset directly from speech timestamps, preventing premature cutoffs during hesitations.
