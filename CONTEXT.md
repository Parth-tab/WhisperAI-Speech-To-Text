# WhisperAI Speech-To-Text

A fast, context-aware, 100% local voice dictation application for Windows that utilizes Faster-Whisper and local LLMs to intelligently format and inject transcribed text into any active window.

## Language

### Audio & Ingestion

**Audio Stream**:
Continuous, buffered PCM audio data captured from the active microphone input device.
_Avoid_: Voice stream, microphone buffer

**Voice Activity Detection (VAD)**:
Silero-based detection algorithm used to detect the start and end of spoken speech segments from the audio stream.
_Avoid_: Sound trigger, noise filter

**Hardware Discovery**:
Boot-time enumeration and caching of physical audio input devices and Bluetooth profiles without runtime C-level polling.
_Avoid_: Audio scanning, device polling

### ASR & Transcription

**ASR Engine**:
The Faster-Whisper (CTranslate2) local speech-to-text model runtime.
_Avoid_: Whisper server, STT backend

**Transcription**:
Raw text produced directly by the ASR engine before any LLM post-processing or formatting.
_Avoid_: Dictation output, speech log

### Intent & Formatting

**Intent Engine**:
The local Llama.cpp runtime running quantized Qwen2.5-1.5B (GGUF) used for punctuation, capitalization, and command extraction.
_Avoid_: Chat model, AI agent

**Split-Pass Formatting**:
The strategy of combining deterministic regex pre/post-processing with minimal LLM prompts to prevent small-model hallucination.
_Avoid_: Single-prompt generation, one-shot formatting

### UI & Injection

**Floating Overlay**:
The PySide6 frameless, always-on-top, non-blocking visual interface showing recording, transcribing, and processing states.
_Avoid_: Popup window, modal dialog, HUD

**Active Window Detection**:
Win32-level identification of the target foreground application handle (HWND) before recording or injection.
_Avoid_: Focus scraper, window hook

**Text Injection**:
Direct keyboard simulation or clipboard-based insertion targeting the active window control without stealing focus.
_Avoid_: Typing macro, text pasting
