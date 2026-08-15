# Split-Pass Formatting for Lightweight LLM

To reliably format transcriptions without hallucinations on lightweight 1.5B models (Qwen2.5-1.5B), the pipeline uses a split-pass architecture where deterministic regex pre/post-processing handles structural tokens (e.g., lists, code fences, preambles) while the LLM handles contextual punctuation, casing, and intent extraction.
