# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-07-17

### Added
- **Silent Auto-Updater (Handoff Bootstrapper):** WhisperAI now silently checks GitHub for updates on boot. If an update is found, a non-intrusive system tray notification allows users to download and install the update seamlessly in the background without worrying about OS-level file locks.
- **Lazy-Load Model Architecture:** The application installer size has been drastically reduced (from ~3GB to <100MB). Faster-Whisper and Qwen 1.5B GGUF models are now lazily loaded from the Hugging Face CDN directly into `%USERPROFILE%\.whisperai\models` upon first boot, tracked via a responsive UI progress bar.
- **Universal Bluetooth Support:** Expanded heuristics for Bluetooth Hands-Free Profile (HFP) devices to ensure robust duplex stream initialization.

### Fixed
- **GIL Deadlock on Audio Init:** Fixed a critical defect where re-initializing PortAudio (`sd._initialize()`) on every toggle caused the Python Global Interpreter Lock (GIL) to freeze for up to 15 seconds during Windows WASAPI Bluetooth enumeration. Hardware state is now safely cached on boot.
- **UI Freeze on Hardware Error:** Replaced dangerous blocking modal dialogs (`QMessageBox.critical`) in the floating Flow Bubble with non-blocking system tray notifications (`tray.showMessage()`), preventing permanent main-thread lockups when audio hardware fails.

---

## [1.0.0] - Initial Release

This release includes the final deployment optimizations, successfully compiling the architecture into a single `.exe`.

### Added
- **Phase 3 Streaming:** Fully integrated Phase 3 streaming, ensuring ultra-low latency audio processing and real-time transcription feedback.
- **Context Caching:** Implemented intelligent context caching. This minimizes redundant processing and significantly improves inference speed by reusing context where appropriate.
- **Explicit Disfluency Tokens:** Added handling for explicit disfluency tokens (e.g., "uh", "um"). The model now gracefully handles and filters out these tokens to produce cleaner transcripts.
- **Auto-Healing Watchdog:** Deployed an auto-healing watchdog implementation. The watchdog actively monitors critical application components and automatically restarts them in the event of failures or deadlocks, guaranteeing continuous operation.
- **Flow Bubble UI:** The new Flow Bubble UI provides a non-intrusive, always-on-top indicator of the application's state.
- **Contextual Dictation:** Contextual dictation analyzes the application you are currently typing in and adapts its vocabulary appropriately (e.g., coding terms for IDEs, formal language for emails).
- **Command Mode Macros:** Command Mode allows you to execute predefined macros using your voice.
